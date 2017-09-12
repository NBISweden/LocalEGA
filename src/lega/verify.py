#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
####################################
#
# Verifying the vault files
#
####################################

This module checks the files in the vault, by decrypting them and
recalculating their checksum.
It the checksum still corresponds to the one of the original file,
we consider that the vault has properly stored the file.
'''

import sys
import logging
import os

from .conf import CONF
from .utils import crypto, db, checksum
from .utils import db_log_error_on_files, checksum
from .utils.amqp import get_connection, consume

LOG = logging.getLogger('verify')

@db_log_error_on_files
def work(data):
    '''Verifying that the file in the vault does decrypt properly'''

    file_id = data['file_id']
    filename, org_hash, org_hash_algo, vault_filename, vault_checksum = db.get_details(file_id)

    if not checksum.is_valid(vault_filename, vault_checksum, hashAlgo='sha256'):
        raise VaultDecryption(vault_filename)

    return { 'vault_name': vault_filename, 'org_name': filename }
    
def main(args=None):

    if not args:
        args = sys.argv[1:]

    CONF.setup(args) # re-conf

    from_connection = get_connection('local.broker')
    from_channel = from_connection.channel()
    from_channel.basic_qos(prefetch_count=1) # One job per worker

    to_connection = get_connection('cega.broker').channel()

    try:
        consume(from_channel,
                work,
                from_queue  = CONF.get('local.broker','archived_queue'),
                to_channel  = to_channel,
                to_exchange = CONF.get('cega.broker','exchange'),
                to_routing  = CONF.get('cega.broker','routing_file_verified'))
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

if __name__ == '__main__':
    main()
