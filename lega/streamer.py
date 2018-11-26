#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Decrypting file from the vault, given a stable ID.

Only used for testing to see if the encrypted file can be sent as a Crypt4GH-formatted stream
"""

# import sys
# import os
import io
import time
import asyncio
import uvloop
import ed25519
from nacl.public import PrivateKey, PublicKey
from nacl.encoding import HexEncoder as KeyFormatter
# from nacl.encoding import URLSafeBase64Encoder as KeyFormatter
from crypt4gh.crypt4gh import Header
from aiohttp import web

from .conf import CONF, configure
from .utils import storage
from .utils import async_db as db
from .utils.logging import LEGALogger

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

LOG = LEGALogger(__name__)

####################################


async def init(app):
    # Some settings

    chunk_size = CONF.get_value('vault', 'chunk_size', conv=int, default=1 << 22)  # 4 MB
    app['chunk_size'] = chunk_size

    # Load the LocalEGA private key
    key_location = CONF.get_value('DEFAULT', 'private_key')
    LOG.info('Retrieving the Private Key from %s', key_location)
    with open(key_location, 'rt') as k:  # text file
        privkey = PrivateKey(k.read(), KeyFormatter)
        app['private_key'] = privkey

    # Load the LocalEGA header signing key
    signing_key_location = CONF.get_value('DEFAULT', 'signing_key')
    LOG.info('Retrieving the Signing Key from %s', signing_key_location)
    if signing_key_location:
        with open(signing_key_location, 'rt') as k:  # hex file
            app['signing_key'] = ed25519.SigningKey(bytes.fromhex(k.read()))
    else:
        app['signing_key'] = None


async def shutdown(app):
    '''Function run after a KeyboardInterrupt. After that: cleanup'''
    LOG.info('Shutting down the database engine')
    await db.close()

####################################

# |-------------|--------------------------------------------------------|
# | Field       | Explanation                                            |
# |-------------|--------------------------------------------------------|
# | stable_id   | EGA stable id, in case we print a message              |
# | pubkey      | The public PGP key of the user for Crypt4GH encryption |
# |-------------|--------------------------------------------------------|


def request_context(func):
    async def wrapper(r):

        correlation_id = r.headers.get('correlation_id')
        if not correlation_id:
            LOG.error('No correlation id in the header')
            # raise web.HTTPBadRequest(reason='Invalid request')

        LOG.debug('Init Context', extra={'correlation_id': correlation_id})

        # Getting post data
        data = await r.json()
        LOG.debug('Data: %s', data, extra={'correlation_id': correlation_id})

        stable_id = data.get('stable_id')
        if not stable_id:  # It should be there. Assertion instead?
            LOG.error('Missing stable ID', extra={'correlation_id': correlation_id})
            raise web.HTTPUnprocessableEntity(reason='Missing stable ID')

        pubkey = data.get('pubkey')
        if not pubkey:  # It should be there. Assertion instead?
            LOG.error('Missing public key for the re-encryption', extra={'correlation_id': correlation_id})
            raise web.HTTPUnprocessableEntity(reason='Missing public key')
        # Load it
        pubkey = PublicKey(pubkey, KeyFormatter)

        request_id = None
        start_time = time.perf_counter()
        try:

            # Fetch information and Create request
            user_info = ''
            client_ip = data.get('client_ip') or ''
            startCoordinate = int(r.query.get('startCoordinate', 0))
            endCoordinate = r.query.get('endCoordinate', None)
            endCoordinate = int(endCoordinate) if endCoordinate is not None else None

            request_info = await db.make_request(stable_id,
                                                 user_info,
                                                 client_ip,
                                                 start_coordinate=startCoordinate,
                                                 end_coordinate=endCoordinate)
            if not request_info:
                LOG.error('Unable to create a request entry', extra={'correlation_id': correlation_id})
                raise web.HTTPServiceUnavailable(reason='Unable to process request')

            # Request started
            request_id, header, vault_path, vault_type, _, _, _ = request_info

            # Set up file transfer type
            LOG.info('Loading the vault handler: %s', vault_type, extra={'correlation_id': correlation_id})
            if vault_type == 'S3':
                mover = storage.S3Storage()
            elif vault_type == 'POSIX':
                mover = storage.FileStorage()
            else:
                LOG.error('Invalid storage method: %s', vault_type, extra={'correlation_id': correlation_id})
                raise web.HTTPUnprocessableEntity(reason='Unsupported storage type')

            # Do the job
            response, dlsize = await func(r,
                                          correlation_id,
                                          pubkey,
                                          r.app['private_key'],
                                          r.app['signing_key'],
                                          header,
                                          vault_path,
                                          mover,
                                          chunk_size=r.app['chunk_size'])
            # Mark as complete
            elapsed_time = round(time.perf_counter() - start_time, 3)  # rounded?
            speed = dlsize / elapsed_time if elapsed_time else 0.0
            await db.download_complete(request_id, dlsize, speed)
            return response
        # except web.HTTPError as err:
        except Exception as err:
            if isinstance(err, AssertionError):
                raise err
            cause = err.__cause__ or err
            LOG.error('%r', cause, extra={'correlation_id': correlation_id})  # repr = Technical
            if request_id:
                await db.set_error(request_id, cause)
            raise web.HTTPServiceUnavailable(reason='Unable to process request')
    return wrapper


@request_context
async def outgest(r, correlation_id, pubkey, privkey, signing_key, header, vault_path, mover, chunk_size=1 << 22):

    # Crypt4GH encryption
    LOG.info('Re-encrypting the header', extra={'correlation_id': correlation_id})  # in hex -> bytes, and take away 16 bytes
    header_obj = Header.from_stream(io.BytesIO(bytes.fromhex(header)))
    reencrypted_header = header_obj.reencrypt(pubkey, privkey, signing_key=signing_key)
    renc_header = bytes(reencrypted_header)
    LOG.debug('Org header %s', header, extra={'correlation_id': correlation_id})
    LOG.debug('Reenc header %s', renc_header.hex(), extra={'correlation_id': correlation_id})

    # Read the rest from the vault
    LOG.info('Opening vault file: %s', vault_path, extra={'correlation_id': correlation_id})
    with mover.open(vault_path, 'rb') as vfile:

        # Ready to answer
        response = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'application/octet-stream'})
        await response.prepare(r)
        # Sending the header
        await response.write(renc_header)
        await response.drain()
        bytes_count = len(renc_header)

        # Sending the remainder
        while True:
            data = vfile.read(chunk_size)  # not async...I know
            if not data:
                break
            await response.write(data)
            await response.drain()
            bytes_count += len(data)

        # Finally
        await response.write_eof()
        return response, bytes_count


@configure
def main(args=None):
    """Run streamer service."""
    host = CONF.get_value('DEFAULT', 'host')  # fallbacks are in defaults.ini
    port = CONF.get_value('DEFAULT', 'port', conv=int)

    # loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    server = web.Application()
    server.router.add_post('/', outgest)

    # Registering the initialization routine
    server.on_startup.append(init)
    server.on_cleanup.append(shutdown)

    # ...and cue music
    LOG.info(f"Start reencryption service on {host}:{port}")
    web.run_app(server, host=host, port=port)


if __name__ == '__main__':
    main()
