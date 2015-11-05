"""Standard token authentication for guest clients.

.. moduleauthor:: Dave Zimmelman <zimmed@zimmed.io>

"""

import hmac
import time
from hashlib import md5 as hash_method
from .exception import TokenInvalidError, TimeOutError


def timeout_check(timestamp, timeout=10.0):
    if time.time() > float(timestamp) + timeout:
        raise TimeOutError("Took too long to process request. "
                           "(Limit: " + str(timeout) + "s)")


def hash_values(key, *args):
    value = ''.join([str(arg) for arg in args])
    return hmac.HMAC(key, value, hash_method).hexdigest()


def auth_guest(event):
    token = hash_values(event.client, event.type, event.timestamp)
    if token != event.data.token:
        raise TokenInvalidError("Invalid token provided in request.")
