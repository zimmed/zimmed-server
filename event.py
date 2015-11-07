"""Socket events

.. moduleauthor:: Dave Zimmelman <zimmed@zimmed.io>

Exports:
    :class SocketEvent
    :class SocketConnectEvent
    :class SocketDisconnectEvent
    :class SocketDataEvent
    :class SocketServerEvent
"""

from core.dotdict import DotDict
from tornado.escape import json_decode, json_encode


class SocketEvent(object):
    """base SocketEvent

    Init Params:
        etype -- The type of the event.
        client_id -- The socket client identifier.
        kwargs -- Event data.

    Properties:
        :type type: str -- Event type
        :type client: str -- Client ID
        :type data: ImmutableDotDict -- The event data.

    Methods:
        json -- Get JSON representation of event.
    """

    def __init__(self, etype, client_id, client_ip, **kwargs):
        self.type, self.client, self.data = etype, client_id, {}
        self.client_ip = client_ip
        if kwargs:
            self.data.update(kwargs)
        self.data = DotDict(self.data)
        self.__locked = True

    def __setattr__(self, key, value):
        try:
            if hasattr(self, key) and self.__locked:
                raise ValueError("Cannot assign to existing event attribute.")
        except AttributeError:
            pass
        finally:
            super(SocketEvent, self).__setattr__(key, value)

    def json(self):
        d = dict(self.data)
        d['type'] = self.type
        if self.client:
            d['client'] = self.client
        return json_encode(d)

    def ok_response(self, **kwargs):
        return SocketServerEvent(self.type, **kwargs)

    def __str__(self):
        return self.json()


class SocketConnectEvent(SocketEvent):

    def __init__(self, client_id, client_ip):
        super(SocketConnectEvent, self).__init__('connect', client_id, client_ip)


class SocketDisconnectEvent(SocketEvent):

    def __init__(self, client_id, client_ip):
        super(SocketDisconnectEvent, self).__init__('disconnect', client_id, client_ip)


class SocketDataEvent(SocketEvent):

    def __init__(self, client_id, client_ip, message):
        etype = 'invalid'
        if isinstance(message, (str, basestring, unicode)):
            data = _native_strings(json_decode(message))

        else:
            data = message
        if 'type' in data.iterkeys():
            etype = data['type']
            del data['type']
        super(SocketDataEvent, self).__init__(etype, client_id, client_ip, **data)


class SocketServerEvent(SocketEvent):

    def __init__(self, etype, **kwargs):
        kwargs['status'] = 200
        super(SocketServerEvent, self).__init__(etype, None, None, **kwargs)


def _native_strings(obj):
    if isinstance(obj, (str, unicode, basestring)):
        return str(obj)
    if isinstance(obj, dict):
        new_obj = {}
        for k, v in obj.iteritems():
            new_obj[str(k)] = _native_strings(v)
        return new_obj
    if isinstance(obj, list):
        return [_native_strings(x) for x in obj]
    return obj
