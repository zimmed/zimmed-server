"""zimmed-server package.

A modular, threaded, event socket server.

.. packageauthor:: Dave Zimmelman <zimmed@zimmed.io>

Exports:
    :

"""

from tornado.escape import json_encode
from core.decorators import classproperty
from .socket import SocketServer
from .event import (SocketConnectEvent, SocketDisconnectEvent,
                    SocketDataEvent)


class EventServer(SocketServer):

    @classmethod
    def handle(cls, client_id, message):
        if message is 'connect':
            e = SocketConnectEvent(client_id)
        elif message is 'disconnect':
            e = SocketDisconnectEvent(client_id)
        else:
            e = SocketDataEvent(client_id, message)
        cls._out_queue.put(e)

    @classmethod
    def emit(cls, client_id, data):
        message = json_encode(data)
        super(EventServer, cls).emit(client_id, message)

    @classmethod
    def broadcast(cls, client_ids, data):
        message = json_encode(data)
        super(EventServer, cls).broadcast(client_ids, message)

    @classproperty
    def has_events(cls):
        return cls._out_queue.empty()

    @classmethod
    def get_event(cls):
        return cls.get_message()


# ----------------------------------------------------------------------------
__version__ = 1.00
__license__ = "MIT"
__credits__ = ["zimmed"]
__copyright__ = '''
Copyright (c) 2015 David Zimmelman - Re-use code freely with credit to
original author(s).
'''
# ----------------------------------------------------------------------------
