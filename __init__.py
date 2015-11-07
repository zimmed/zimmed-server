"""zimmed-server package.

A modular, threaded, event socket server.

.. packageauthor:: Dave Zimmelman <zimmed@zimmed.io>

Exports:
    :class EventServer -- Event-driven WebSocket server.
    :module event -- SocketEvent definitions.
    :module router -- EventRouter for listening and processing SocketEvents.
    :module socket -- Base WebSocket server (built on tornado.websocket)

"""

from .socket import SocketServer
from .event import (SocketConnectEvent, SocketDisconnectEvent,
                    SocketDataEvent)
import logging

class EventServer(SocketServer):
    """Threaded WebSocket server for handling socket requests.

    Takes socket requests and queues SocketEvents to be read by the program
    event loop (SocketRouter).

    Note:
        No initialization required.

    Usage:
        ...

    Class Methods:
        emit -- Emit data to specified client.
        broadcast -- Emit data to all connected clients, or specified list of
            clients.
        has_events -- Returns true if Server has events queued for reading.
        get_event -- Get next SocketEvent from queue.

    """

    @classmethod
    def handle(cls, client, message):
        if message is 'connect':
            e = SocketConnectEvent(client.uid, client.request.remote_ip)
        elif message is 'disconnect':
            e = SocketDisconnectEvent(client.uid, client.request.remote_ip)
        else:
            e = SocketDataEvent(client.uid, client.request.remote_ip, message)
        cls._out_queue.put(e)

    @classmethod
    def emit(cls, socket_event, client_id):
        message = socket_event.json()
        logging.debug("Emitting: " + message)
        logging.debug("\tto: " + client_id)
        super(EventServer, cls).emit(message, client_id)

    @classmethod
    def broadcast(cls, socket_event, include=None, exclude=None):
        message = socket_event.json()
        super(EventServer, cls).broadcast(message, include, exclude)

    @classmethod
    def is_empty(cls):
        return cls._out_queue.empty()

    @classmethod
    def has_events(cls):
        return not cls.is_empty()

    @classmethod
    def get_event(cls):
        return cls.get_message()


# ----------------------------------------------------------------------------
__version__ = 1.01
__license__ = "MIT"
__credits__ = ["zimmed"]
__copyright__ = '''
Copyright (c) 2015 David Zimmelman - Re-use code freely with credit to
original author(s).
'''
# ----------------------------------------------------------------------------
