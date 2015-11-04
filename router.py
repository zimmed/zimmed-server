"""Event router module.

Handles main program event loop.

Exports:
    :class EventRouter -- Static router class for handling events.

"""

from core.decorators import classproperty
from core.exceptions import InitError
import threading
import time


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

            def no_next(_):
                pass

            def do_next(e):
                do = stack.pop()
                do(e, stack)

            self.method.next = do_next if stack else no_next
            self.method(event, *self.args)

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
        """
        if event_type not in cls._routers.iterkeys():
            cls._routers[event_type] = []
        cls._routers[event_type].append(cls.Router(method, *args))

    @classmethod
    def off(cls, event_type):
        """Remove all event listeners for type.

        :param event_type: str -- Name of event type.
        """
        try:
            del cls._routers[event_type]
        except KeyError:
            pass

    @classmethod
    def off_last(cls, event_type):
        """Remove only the most-recently added listener.

        :param event_type: str -- Event type
        """
        try:
            if len(cls._routers[event_type]) > 1:
                cls._routers.pop()
        except KeyError:
            pass

    @classmethod
    def listen_sync(cls, **kwargs):
        """Listen to and handle events produced by the EventServer.

        This is a synchronous function and will block by default.

        :param kwargs: expects `empty` and `get` methods.
        """
        if 'get' not in kwargs.iterkeys() or 'empty' not in kwargs.iterkeys():
            raise KeyError('`get` and `empty` params required for listening.')
        get = kwargs['get']
        empty = kwargs['empty']
        cls._listening = True
        while cls._listening:
            if not empty():
                event = get()
                cls.handle(event)
        if 't_event' in kwargs.iterkeys():
            kwargs['t_event'].set()

    @classmethod
    def listen_async(cls, **kwargs):
        """Runs listen_sync in separate thread. Non-blocking.

        :param kwargs: Same as listen_sync
        """
        cls._thread_event = threading.Event()
        kwargs.update(t_event=cls._thread_event)
        cls._thread = threading.Thread(target=cls.listen_sync, kwargs=kwargs)
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
    def handle(cls, event):
        event_type = event.type
        try:
            stack = list(cls._routers[event_type])
            do = stack.pop()
            do(event, stack)
        except (KeyError, IndexError):
            pass

    def __init__(self, *args, **kwargs):
        raise InitError("EventRouter is not to be initialized.")

