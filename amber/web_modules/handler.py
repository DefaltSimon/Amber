# coding=utf-8
import logging
from ujson import dumps

log = logging.getLogger(__name__)

# TODO deprecated
class SocketEventManager:
    def __init__(self):
        """
        Similar to EventManager, but allows custom events
        """
        self.callbacks = {}

    # noinspection PyCallingNonCallable
    def dispatch_event(self, event_name, *args, **kwargs):
        """
        Internal use only, to dispatch individual events
        :param event_name: Event name
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: None or what the function returns
        """

        fn = self.callbacks.get(event_name)
        if fn:
            return fn(*args, **kwargs)
        else:
            return None

    def set_event_handler(self, event_name, fn):
        if fn in self.callbacks.values():
            log.warning("Event function {} was already registered, overwriting".format(event_name))

        log.info("Event {} registered".format(event_name))
        self.callbacks[event_name] = fn


class SocketHandler:
    def __init__(self, amber, socket):
        self.sock = socket
        self.amber = amber

        self.events = {}
        self.actions = {}

        self.e_mgr = SocketEventManager()

    # EVENT REGISTERING
    def event(self, fn, event_name):
        """
        Registers an event handler via decorators
        :param fn: Provided automatically by the decorator
        :param event_name: Your first parameter: name of the event (by property names)
        :return: function for the decorator to use
        """
        if not callable(fn):
            raise TypeError("not a function")

        # Register the event
        self.e_mgr.set_event_handler(event_name, fn)
        return fn

    async def send(self, payload):
        await self.sock.send(dumps(payload))

    async def reply(self, status, data, **kwargs):
        payload = {
            "status": status,
            "data": data,
        }
        payload = {**payload, **kwargs}
        await self.sock.send(payload)

    async def handle(self, type_, additional, req_id, data):
        if type_ == "event":
            status, resp = self.handle_event(additional, data)
            await self.reply(status, resp, req_id=req_id)

        elif type_ == "action":
            status, resp = self.handle_action(additional, data)
            await self.reply(status, resp, req_id=req_id)

        else:
            log.warning("No such type: {}".format(type_))

    async def handle_event(self, event_type, data, **kwargs) -> tuple:
        pass

    async def handle_action(self, action_type, data, **kwargs) -> tuple:
        pass