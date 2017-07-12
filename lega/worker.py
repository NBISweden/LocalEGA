#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Re-Encryption Worker
#
####################################

It simply consumes message from the message queue configured in the [worker] section of the configuration files.

It defaults to the `tasks` queue.

It is possible to start several workers, of course!
However, they should have the gpg-agent socket location in their environment (when using GnuPG 2.0 or less).
In GnuPG 2.1, it is not necessary (Just point the `homedir` to the right place).

When a message is consumed, it must be of the form:
* filepath
* target
* hash (of the unencrypted content)
* hash_algo: the associated hash algorithm
'''

import sys
import os
import logging
import json
from pathlib import Path
import shutil
import stat
import uuid
from multiprocessing import Process, cpu_count

from .conf import CONF
from . import exceptions
from . import crypto
from . import amqp as broker
from . import db
from .utils import checksum, check_error

LOG = logging.getLogger('worker')

@check_error
def work(data):
    '''Main ingestion function

    The data is of the form:
    * user id
    * a filename
    * encrypted hash information (with both the hash value and the hash algorithm)
    * unencrypted hash information (with both the hash value and the hash algorithm)

    The hash algorithm we support are MD5 and SHA256, for the moment.
    '''

    file_id = data['file_id']
    user_id = data['user_id']
    elixir_id = data['elixir_id']
    
    # Find inbox
    inbox = Path( CONF.get('worker','inbox',raw=True) % { 'user_id': user_id } )
    LOG.info(f"Inbox area: {inbox}")

    filename = data['filename']
    LOG.info(f"Processing {filename}")

    # Check if file is in inbox
    inbox_filepath = inbox / filename
    if not inbox_filepath.exists():
        raise exceptions.NotFoundInInbox(filename) # return early

    # Ok, we have the file in the inbox
    filehash = data['encrypted_integrity']['hash']
    hash_algo = data['encrypted_integrity']['algorithm']
    
    assert( isinstance(filehash,str) )
    assert( isinstance(hash_algo,str) )
    
    ################# Check integrity of encrypted file
    LOG.debug(f"Verifying the {hash_algo} checksum of encrypted file: {inbox_filepath}")
    if not checksum(inbox_filepath, filehash, hashAlgo = hash_algo):
        LOG.error(f"Invalid {hash_algo} checksum for {inbox_filepath}")
        raise exceptions.Checksum(hash_algo, f'for {inbox_filepath}')
    LOG.debug(f'Valid {hash_algo} checksum for {inbox_filepath}')

    # Fetch staging area
    staging_area = Path( CONF.get('worker','staging') )
    LOG.info(f"Staging area: {staging_area}")
    #staging_area.mkdir(parents=True, exist_ok=True) # re-create
        
    # Create a unique name for the staging area
    #unique_name = str(uuid.uuid4())
    unique_name = str(uuid.uuid5(uuid.NAMESPACE_OID, 'lega'))
    LOG.debug(f'Created an unique filename in the staging area: {unique_name}')
    staging_filepath = staging_area / unique_name
    
    unencrypted_hash = data['unencrypted_integrity']['hash']
    unencrypted_algo = data['unencrypted_integrity']['algorithm']
    
    LOG.debug(f'Starting the re-encryption\n\tfrom {inbox_filepath}\n\tto {staging_filepath}')
    db.set_progress(file_id, str(staging_filepath))
    details, staging_checksum = crypto.ingest( str(inbox_filepath),
                                               unencrypted_hash,
                                               hash_algo = unencrypted_algo,
                                               target = staging_filepath)
    db.set_encryption(file_id, details, staging_checksum)
    LOG.debug(f'Re-encryption completed')

    #target_name = f"{unencrypted_algo}__{unencrypted_hash}"
    target_name = f"{file_id:0>20}" # filling with zeros, and 20 characters wide

    reply = {
        'file_id' : file_id,
        'filepath': str(staging_filepath),
        'target_name': target_name,
        'user_id': user_id,
    }
    LOG.debug(f"Reply message: {reply!r}")
    return reply

def consume():

    connection = broker.get_connection('local.broker')
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1) # One job per worker

    try:
        broker.consume(channel,
                       work,
                       from_queue  = CONF.get('local.broker','tasks_queue'),
                       to_channel  = channel,
                       to_exchange = CONF.get('local.broker','exchange'),
                       to_routing  = CONF.get('local.broker','routing_complete'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

def main(args=None):
    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    if hasattr(os, 'sched_getaffinity'):
        nb_cores = len(os.sched_getaffinity(0))
    else:
        nb_cores = cpu_count()

    LOG.debug(f'Number of Cores: {nb_cores}')

    extra_workers = []
    for _ in range(2, nb_cores, 2):
        p = Process(group=None, target=consume) # no name
        p.start()
        extra_workers.append(p)
        
    if extra_workers:
        LOG.info(f'Starting {len(extra_workers)} extra workers')
    consume() # and this one

if __name__ == '__main__':
    main()
