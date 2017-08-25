import json
import logging
from pathlib import Path
from base64 import b64encode, b64decode
from functools import wraps
import secrets
import string
import os
import sys

from aiohttp.web import HTTPUnauthorized

from ..conf import CONF
from . import db
from . import exceptions

LOG = logging.getLogger('utils')

def only_central_ega(async_func):
    '''Decorator restrain endpoint access to only Central EGA'''
    @wraps(async_func)
    async def wrapper(request):
        # Just an example
        if request.headers.get('X-CentralEGA', 'no') != 'yes':
            raise HTTPUnauthorized(text='Not authorized. You should be Central EGA.\n')
        # Otherwise, it is from CentralEGA, we continue
        res = async_func(request)
        res.__name__ = getattr(async_func, '__name__', None)
        res.__qualname__ = getattr(async_func, '__qualname__', None)
        return (await res)
    return wrapper

def db_log_error_on_files(func):
    '''Decorator to store the raised exception in the database'''
    @wraps(func)
    def wrapper(data):
        file_id = data['file_id'] # I should have it
        try:
            res = func(data)
            return res
        except Exception as e:
            if isinstance(e,AssertionError):
                raise e

            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            LOG.debug(f'Origin: exc_type: {exc_type} | fname: {fname} | line: {exc_tb.tb_lineno}')

            db.set_error(file_id, e)
    return wrapper

def get_data(data):
    try:
        return json.loads(b64decode(data))
    except Exception as e:
        print(repr(e))
        return None
    #return json.loads(msgpack.unpackb(data))

alphabet = string.ascii_letters + string.digits
def generate_password(length):
    return ''.join(secrets.choice(alphabet) for i in range(length))


def set_file_id(data):
    '''Adding the related file into the database
    and adding the return file id into the message'''

    data['user_id'] = data['elixir_id'].split('@')[0]
    del data['elixir_id']

    filename = data['filename']

    # Insert in database
    file_id = db.insert_file(filename, user_id) 
    assert file_id is not None, 'Ouch...database problem!'
    LOG.debug(f'Created id {file_id} for {data["filename"]}')

    data['file_id'] = file_id
    return data

def sanitize_user_id(data):
    '''Removes the @elixir-europe.org from the elixir ID.'''

    data['user_id'] = data['elixir_id'].split('@')[0]
    del data['elixir_id']

    return data
