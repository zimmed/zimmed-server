"""Socket events

.. moduleauthor:: Dave Zimmelman <zimmed@zimmed.io>

Exports:

"""

from core.dotdict import ImmutableDotDict
from tornado.escape import json_decode, json_encode


class SocketEvent(object):

    def __init__(self, etype, client_id, **kwargs):
        self.type, self.client, self.data = etype, client_id, {}
        if kwargs:
            self.data.update(kwargs)
        self.data = ImmutableDotDict(self.data)
        self.__locked = True

    def __setattr__(self, key, value):
        try:
            if self.__locked:
                raise ValueError("Cannot assign to event object.")
        except AttributeError:
            pass
        finally:
            super(SocketEvent, self).__setattr__(key, value)

    def json(self):
        d = dict(self.data)
        self.data['message'] = self.type
        if self.client:
            self.data['client'] = self.client
        return json_encode(d)

    def __str__(self):
        return self.json()


class SocketConnectEvent(SocketEvent):

    def __init__(self, client_id):
        super(SocketConnectEvent, self).__init__('connect', client_id)


class SocketDisconnectEvent(SocketEvent):

    def __init__(self, client_id):
        super(SocketDisconnectEvent, self).__init__('disconnect', client_id)


class SocketDataEvent(SocketEvent):

    def __init__(self, client_id, message):
        etype = 'invalid'
        data = json_decode(message)
        if 'message' in data.iterkeys():
            etype = data['type']
            del data['type']
        super(SocketDataEvent, self).__init__(etype, client_id, **data)

