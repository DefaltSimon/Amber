# coding=utf-8
import logging
import websockets
from websockets import exceptions
import asyncio

try:
    from ujson import dumps, loads
except ImportError:
    from json import dumps, loads

from .handler import SocketHandler

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Socket:
    def __init__(self, amber, loop: asyncio.AbstractEventLoop, host, port):
        self.loop = loop
        self.amber = amber

        assert isinstance(self.loop, asyncio.AbstractEventLoop)

        self.host = host
        self.port = port

        self.connected_once = False

        self.s_cor = websockets.serve(self.parse_socket, host, port)
        self.socket = None

        self.sockets = []

    async def start(self, amber):
        self.loop.create_task(self.s_cor)
        log.info("Websocket ready")

    async def parse_socket(self, socket, path):
        parser = SocketHandler(self.amber, socket)

        self.sockets.append(socket)

        if self.connected_once:
            log.warning("Websocket was already connected once, received another one")
        self.connected_once = True

        while True:
            try:
                resp = await socket.recv()
            except exceptions.ConnectionClosed:
                log.info("Client disconnected")
                return

            try:
                resp = loads(resp)
            except:
                log.critical("Invalid JSON response: {}".format(resp))
                # raise
                continue

            assert isinstance(resp, dict)

            # Gets type
            typ_ = resp.get("type")

            # Gets event/action type
            if typ_ == "event":
                add = resp.get("event")
            elif typ_ == "action":
                add = resp.get("action")
            else:
                log.warning("Should not happen!")
                raise RuntimeError

            # Finally, extracts the data
            data = resp.get("data")
            req_id = resp.get("req_id")

            await parser.handle(typ_, add, req_id, data)
