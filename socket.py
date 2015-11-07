"""Web socket server.

This module is mostly abstracted by the other server modules.

.. moduleauthor:: Dave Zimmelman <zimmed@zimmed.io>

Exports:
    :class SocketServer
    :class SocketHandler
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import uuid
import Queue
import threading
import time


# noinspection PyAbstractClass
class SocketHandler(tornado.websocket.WebSocketHandler):

    _server = None

    @classmethod
    def set_server(cls, server):
        cls._server = server

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        self.server.on_connect(self)

    def on_close(self):
        self.server.on_disconnect(self)

    def on_message(self, message):
        self.server.on_message(self, message)

    def check_origin(self, _):
        return True

    @property
    def server(self):
        if not self.__class__.server:
            raise ValueError("Server ref not set for SocketHandler.")
        return self.__class__._server


class RestHandler(tornado.web.RequestHandler):
    def get(self):
        self.send_error(404)


class SocketServer(object):

    _instance = None
    _thread = None
    _out_queue = Queue.Queue()

    @classmethod
    def is_listening(cls):
        return bool(cls._thread)

    @classmethod
    def get_message(cls):
        return cls._out_queue.get()

    @classmethod
    def handle(cls, client, message):
        pass

    @classmethod
    def on_connect(cls, client):
        logging.info("Client connected.")
        cls.get_instance().add_client(client)
        cls.handle(client, 'connect')

    @classmethod
    def on_disconnect(cls, client):
        logging.info("Client disconnected.")
        cls.get_instance().del_client(client)
        cls.handle(client, 'disconnect')

    @classmethod
    def on_message(cls, client, message):
        logging.info("Received message.")
        logging.debug("\t%s" % repr(message))
        cls.handle(client, message)

    @classmethod
    def get_instance(cls, *args, **kwargs):
        return cls._instance or cls(*args, **kwargs)

    @classmethod
    def emit(cls, message, client_id):
        cls._instance.send(client_id, message)

    @classmethod
    def broadcast(cls, message, include=None, exclude=None):
        clients = None
        ex = False
        if include and exclude:
            clients = [x for x in include if x not in exclude]
        elif include and not exclude:
            clients = include
        elif exclude:
            clients = exclude
            ex = True
        cls._instance.send_all(clients, message, ex)

    @classmethod
    def disconnect(cls, client_id):
        cls._instance.close_client(client_id)

    @classmethod
    def start(cls, *args, **kwargs):
        if not cls.is_listening():
            if 'log_level' in kwargs:
                logging.basicConfig(level=kwargs['log_level'])
                del kwargs['log_level']
            logging.info("Starting SocketServer...")
            ref = cls.get_instance(*args, **kwargs)
            cls._thread = threading.Thread(target=cls.listen_loop,
                                           args=(ref,))
            cls._thread.daemon = True
            cls._thread.start()

    @classmethod
    def stop(cls):
        try:
            logging.info("Stopping SocketServer...")
            tornado.ioloop.IOLoop.current().stop()
            time.sleep(1)
            cls._thread = None
            return 0
        except KeyboardInterrupt:
            return 1

    @classmethod
    def listen_loop(cls, ref):
        ref.app = tornado.web.Application([
            (r"/", ref.rest_handler),
            (r"/ws", ref.socket_handler)])
        ref.app.listen(ref.port)
        tornado.ioloop.IOLoop.current().start()

    def __init__(self, address='127.0.0.1', port='27016'):
        if self.__class__._instance:
            raise RuntimeError("Re-instantiation of singleton object.")
        self.__class__._instance = self
        self.address, self.port = address, port
        self.socket_handler = SocketHandler
        self.socket_handler.set_server(self.__class__)
        self.rest_handler = RestHandler
        self._clients = {}
        self.app = None

    def send(self, client_id, message):
        client = self.get_client(client_id)
        logging.debug("Sending back message: " + message)
        if client:
            client.write_message(message)
        else:
            logging.warn('Could not send message to client: ' + client_id)

    def send_all(self, client_ids, message, exclude):
        clients = client_ids
        if not client_ids:
            clients = [k for k in self._clients.iterkeys()]
        elif client_ids and exclude:
            clients = [k for k in self._clients.iterkeys()
                       if k not in client_ids]
        for cid in clients:
            self.send(cid, message)

    def get_client(self, client_id):
        try:
            return self._clients[client_id]
        except KeyError:
            return None

    def client_id(self, client):
        if not hasattr(client, 'uid'):
            uid = uuid.uuid4().hex
            while uid in self._clients:
                uid = uuid.uuid4().hex
            client.uid = uid
        return client.uid

    def close_client(self, client_id):
        # client = self.get_client(client_id)
        client = SocketHandler()
        if not client:
            logging.warn("Disconnect attempt for non-existing client.")
        else:
            self.del_client(client)
            client.close()

    def add_client(self, client):
        client_id = self.client_id(client)
        self._clients[client_id] = client

    def del_client(self, client_or_id):
        if not isinstance(client_or_id, str):
            client_or_id = client_or_id.uid
        try:
            del self._clients[client_or_id]
        except KeyError:
            pass
