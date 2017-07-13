#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
GPG agent multiplexer.
It accepts many requests and forwards them to the running gpg-agent.
The answer is redirected back to the incoming connection.

The traffic goes through an SSL connection.

:author: Frédéric Haziza
:copyright: (c) 2017, NBIS System Developers.
'''

import sys
import logging
import asyncio
import ssl
from functools import partial

from .conf import CONF

LOG = logging.getLogger('gpg_proxy')

# Monkey-patching ssl
ssl.match_hostname = lambda cert, hostname: True

async def copy_chunk(reader,writer):
    while True:
        data = await reader.read(4096)
        if not data:
            return
        print(data)
        writer.write(data)
        await writer.drain()

async def handle_connection(gpg_socket_path, reader_conn,writer_conn):

    name_from = writer_conn.get_extra_info('peername')
    LOG.debug(f'Connection to {name_from}')

    reader_agent, writer_agent = await asyncio.open_unix_connection(path=gpg_socket_path)

    await asyncio.gather(
        copy_chunk(reader_conn,writer_agent),
        copy_chunk(reader_agent,writer_conn)
    )
    writer_conn.close()
    writer_agent.close()

def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    loop = asyncio.get_event_loop()
    gpg_socket_path = CONF.get('worker','gpg_home') + '/S.gpg-agent.extra'
    LOG.info(f'GPG socket: {gpg_socket_path}')

    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain('/etc/ega/ega.cert', '/etc/ega/ega.key')

    server = loop.run_until_complete(
        asyncio.start_server(partial(handle_connection,gpg_socket_path),
                             host='0.0.0.0',
                             port=9010,
                             ssl=ssl_ctx,
                             loop=loop)
    )
    try:
        loop.run_forever()
    except Exception as e:
        LOG.debug(repr(e))
        server.close()
    
    loop.close()


if __name__ == '__main__':
    main()

