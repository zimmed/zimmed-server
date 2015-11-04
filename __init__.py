"""zimmed-server package.

A modular, threaded, event socket server.

.. packageauthor:: Dave Zimmelman <zimmed@zimmed.io>

Exports:
    :class EventServer -- Event-driven WebSocket server.
    :module event -- SocketEvent definitions.
    :module router -- EventRouter for listening and processing SocketEvents.
    :module socket -- Base WebSocket server (built on tornado.websocket)

"""

from tornado.escape import json_encode
from .socket import SocketServer
from .event import (SocketConnectEvent, SocketDisconnectEvent,
                    SocketDataEvent)


class EventServer(SocketServer):
    """Threaded WebSocket server for handling socket requests.

    Takes socket requests and queues SocketEvents to be read by the program
    event loop (SocketRouter).

    Note:
        No initialization required.

    Usage:
        # Best used with EventRouter. See server.router for details.
        from server.router import EventRouter as router
        from server.event import SocketServerEvent
        from server import EventServer

        def display_incoming_message(event, template):
            print format(template, event.client, event.data.message)
        def send_new_message(event):
            EventServer.broadcast(
                SocketServerEvent('chat-message',
                                  from=event.client,
                                  message=event.data.message),
                exclude=[event.client])
        def connection_notice(event, disconnected=False):
            dis = 'dis' if disconnected else ''
            message = format("%s has %sconnected., event.client, dis)
            print message
            EventServer.broadcast(
                SocketServerEvent('chat-message',
                                  from='SERVER',
                                  message=message),
                exclude=[event.client])
            message = 'Goodbye.' if disconnected else 'Welcome to the server.'
            EventServer.emit(
                SocketServerEvent('chat-message',
                                  from='SERVER',
                                  message=message),
                event.client)
        router.on('chat-event', send_new_message)
        router.on('chat-event', display_incoming_message, "%s: %s")
        router.on('connect', connection_notice)
        router.on('disconnect', connection_notice, True)
        router.listen_async(get=EventServer.get_event,
            empty=(lambda: not EventServer.has_events()))
        try:
            while True:
                pass
        except KeyboardInterrupt:
            router.listen_async_stop()

    Class Methods:
        emit -- Emit data to specified client.
        broadcast -- Emit data to all connected clients, or specified list of
            clients.
        has_events -- Returns true if Server has events queued for reading.
        get_event -- Get next SocketEvent from queue.

    """

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
    def emit(cls, socket_event, client_id):
        message = socket_event.json()
        super(EventServer, cls).emit(client_id, message)

    @classmethod
    def broadcast(cls, socket_event, include=None, exclude=None):
        message = socket_event.json()
        super(EventServer, cls).broadcast(include, exclude, message)

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
