# coding=utf-8
import logging
import websockets
import asyncio

try:
    from ujson import dumps, loads
except ImportError:
    from json import dumps, loads

from .utils import Status

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class ResponseParser:
    def __init__(self, socket):
        self.socket = socket

    async def reply(self, status, data, **kwargs):
        payload = {
            "status": status,
            "data": data,
        }
        payload = {**payload, **kwargs}
        await self.socket.send(payload)


    async def handle(self, typ_, additional, req_id, data):
        log.info("Browser connected!")

        if typ_ == "event":
            pass
        elif typ_ == "action":
            pass

        # Todo implement
        dt = {
            "sample": "ayy"
        }

        await self.reply(Status.OK, dt, req_id=req_id)


class Socket:
    def __init__(self, loop: asyncio.AbstractEventLoop, host, port):
        self.loop = loop
        assert isinstance(self.loop, asyncio.AbstractEventLoop)

        self.host = host
        self.port = port

        self.s_cor = websockets.serve(self.parse_socket, host, port)
        self.socket = None
        self.parser = ResponseParser(self)

    async def start(self):
        self.loop.create_task(self.s_cor)
        log.info("Websocket ready")

    async def send(self, payload):
        payload = dumps(payload)
        await self.socket.send(payload)

    async def parse_socket(self, socket, path):
        self.socket = socket

        while True:
            resp = await socket.recv()
            try:
                resp = loads(resp)
            except:
                log.critical("Invalid JSON response: {}".format(resp))
                raise

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


            await self.parser.handle(typ_, add, req_id, data)

