"""Event router module.

Handles main program event loop.

Exports:
    :class EventRouter -- Static router class for handling events.

"""

from core.decorators import classproperty
from core.exceptions import InitError
from .exception import HTTPError, BadRequestError
import threading
import time
import logging


class EventRouter(object):
    """EventRouter for handling SocketEvents queued by an EventServer.

    Note:
        Do not initialize.

    Usage:
        See EventServer class.

    Class Properties:
        :type listening: bool -- Whether or not the router is currently
            listening for events.

    Class Methods:
        on -- Add new event listener.
        off -- Remove all event handlers for given event type.
        off_last -- Remove the last-added event handler for the given
            event type.
        listen_sync -- Listen to events synchronously (blocking).
        listen_async -- Start async listen thread. (non-blocking).
        listen_async_stop -- Stop async listen thread.

    """

    _routers = {}
    _listening = False
    _thread = None
    _thread_event = None

    class Router(object):

        def __init__(self, method, *args):
            self.method = method
            self.args = args

        def __call__(self, event, stack=None):

            self.method(event, *self.args)
            if stack:
                do = stack.pop()
                do(event, stack)

    @classproperty
    def listening(cls):
        return cls._listening

    @classmethod
    def on(cls, event_type, method, *args):
        """Add new event listener.

        :param event_type: str -- The name of the event. This is sent from
            the client in the 'type' field of the JSON object.
        :param method: callable (event, *args) -- The handler function.
        :param args: list -- Additional args to pass to method.
        :return: cls (Cascading)
        """
        if event_type not in cls._routers.iterkeys():
            cls._routers[event_type] = []
        cls._routers[event_type].append(cls.Router(method, *args))
        return cls

    @classmethod
    def off(cls, event_type):
        """Remove all event listeners for type.

        :param event_type: str -- Name of event type.
        :return: cls (Cascading)
        """
        try:
            del cls._routers[event_type]
        except KeyError:
            pass
        return cls

    @classmethod
    def off_last(cls, event_type):
        """Remove only the most-recently added listener.

        :param event_type: str -- Event type
        :return: cls (Cascading)
        """
        try:
            if len(cls._routers[event_type]) > 1:
                cls._routers.pop()
        except KeyError:
            pass
        return cls

    @classmethod
    def listen_sync(cls, event_server, t_event=None):
        """Listen to and handle events produced by the EventServer.

        This is a synchronous function and will block by default.

        :param event_server: EventServer class
        :param t_event: threading.Event | None -- Optional event for
            monitoring threaded loop state.
        """
        try:
            get = event_server.get_event
            empty = event_server.is_empty
            cls._listening = True
            while cls._listening:
                if not empty():
                    event = get()
                    cls.handle(event, event_server)
                time.sleep(0.01)
            if t_event:
                t_event.set()
        except KeyboardInterrupt:
            cls._listening = False
            return 0

    @classmethod
    def listen_async(cls, event_server):
        """Runs listen_sync in separate thread. Non-blocking.

        :param event_server: EventServer class
        """
        cls._thread_event = threading.Event()
        cls._thread = threading.Thread(target=cls.listen_sync,
                                       args=(event_server, cls._thread_event))
        cls._thread.daemon = True
        cls._thread.start()

    @classmethod
    def listen_async_stop(cls):
        """Stop async listen thread."""
        if not cls.listening:
            raise RuntimeError("Router already not listening.")
        cls._listening = False
        while not cls._thread_event.is_set():
            time.sleep(0.1)
        cls._thread_event = None
        cls._thread = None

    @classmethod
    def handle(cls, event, event_server):
        event_type = event.type
        if event_type in cls._routers:
            stack = list(cls._routers[event_type])
            do = stack.pop()
            try:
                do(event, stack)
            except HTTPError as error:
                error.type = event_type
                event_server.emit(error, event.client)
        else:
            logging.warn('Uncaught event type: ' + event_type)
            e = BadRequestError("Uncaught event.")
            e.type = event_type
            event_server.emit(e, event.client)

    def __init__(self, *args, **kwargs):
        raise InitError("EventRouter is not to be initialized.")

