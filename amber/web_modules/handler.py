# coding=utf-8
import logging
from random import randint
from ujson import dumps
import inspect

from .web_utils import Status, get_engine_version
from ..engine.types_ import Room, Description, Item, Blueprint
from ..engine.exceptions import NotAllowed, AmberException, NoSuchBlueprint, IdMissing
from ..engine import action as act, directory

log = logging.getLogger(__name__)

amber = None


class HandlerMeta(type):
    _instances = {}

    def __call__(cls, event_or_action, *args, **kwargs):
        if event_or_action not in cls._instances.keys():
            cls._instances[event_or_action] = super(HandlerMeta, cls).__call__(event_or_action, *args, **kwargs)

        return cls._instances[event_or_action]


class SocketEventManager(metaclass=HandlerMeta):
    def __init__(self, _):
        """
        Similar to EventManager, but allows custom events
        """
        self.r = randint(5, 500)

        self.callbacks = {}

    # noinspection PyCallingNonCallable
    async def dispatch_event(self, event_name, *args, **kwargs):
        """
        Internal use only, to dispatch individual events
        :param event_name: Event name
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: None or what the function returns
        """

        fn = self.callbacks.get(event_name)
        if fn:
            if inspect.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            else:
                return fn(*args, **kwargs)
        else:
            return None

    def set_event_handler(self, event_name, fn):
        if fn in self.callbacks.values():
            log.warning("Event function {} was already registered, overwriting".format(event_name))

        log.info("Event {} registered".format(event_name))
        self.callbacks[event_name] = fn

    # EVENT REGISTERING
    def on(self, event_name):
        """
        Registers an event handler via decorators
        :param fn: Provided automatically by the decorator
        :param event_name: Your first parameter: name of the event (by property names)
        :return: function for the decorator to use
        """
        def real_dec(fn):
            if not callable(fn):
                raise TypeError("not a function")

            # Register the event
            self.set_event_handler(event_name, fn)
            return fn

        return real_dec


event = SocketEventManager("event")
action = SocketEventManager("action")

# UTILITIES


def extract_from_room(room: Room) -> dict:
    return {
        "name": room.name,
        "description": room.description,
        "msg": room.message,
        "image": room.image,
        "sound": room.sound,
        "id": room.id,
    }


def extract_from_room_name_id(room: Room) -> dict:
    return {
        "name": room.name,
        "id": room.id,
    }


def extract_from_item(item: Item) -> dict:
    return {
        "name": item.name,
        "description": item.description,
        "id": item.id,
    }


def extract_from_description(desc: Description) -> dict:
    return {
        "text": desc.text,
        "rooms": desc.rooms,
        "items": desc.items,
        "id": desc.id,
    }


def extract_from_blueprint(bp: Blueprint) -> dict:
    return {
        "item1": bp.item1,
        "item2": bp.item2,
        "result": bp.result,
    }


def extract_from_action(a: act.Action) -> dict:
    return a.to_dict()


def extract_locations(obj):
    return [extract_from_room_name_id(a) for a in obj]


def dictify(obj):
    if isinstance(obj, Room):
        tree = extract_from_room(obj)
        for k, el in tree.items():
            tree[k] = dictify(el)

        return tree

    elif isinstance(obj, Item):
        tree = extract_from_item(obj)
        for k, el in tree.items():
            tree[k] = dictify(el)

        return tree

    elif isinstance(obj, Description):
        tree = extract_from_description(obj)
        for k, el in tree.items():
            if k == "rooms":
                tree[k] = {r.get("id"): r for r in [extract_from_room_name_id(r) for r in el]}
            elif k == "items":
                tree[k] = {r.get("id"): r for r in [extract_from_item(r) for r in el]}

        return tree

    elif isinstance(obj, Blueprint):
        tree = extract_from_blueprint(obj)
        for k, el in tree.items():
            tree[k] = dictify(el)

        return tree

    elif isinstance(obj, act.Action):
        return obj.to_dict()

    elif isinstance(obj, (str, int, float)):
        return obj

    elif isinstance(obj, dict):
        return {dictify(k): dictify(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [dictify(a) for a in obj]

    elif obj is None:
        return None

    else:
        return obj.__dict__


# EVENT HANDLERS


@event.on("handshake")
def handshake(data):
    ui_version = data.get("uiVersion")
    log.info("Client connected with uiVersion {}".format(ui_version))

    payload = {
        "engineVersion": get_engine_version(),
        "author": amber.author,
        "name": amber.name,
        "description": amber.description,
    }

    return Status.OK, payload

# TODO test
@action.on("get-inventory")
def get_inventory(data):
    return Status.OK, {"inventory": dictify(amber.inventory)}


@action.on("get-intro")
def get_intro(data):
    intro = directory.world.get("intro")
    if not intro:
        return Status.MISSING, None

    pl = {
        "title": intro.title,
        "image": intro.image,
        # TODO sound
    }

    return Status.OK, pl


@action.on("get-room")
def get_room_info(data):
    cr = amber.current_room

    return Status.OK, dictify(cr)


@action.on("get-item")
def get_item_info(data):
    item = Item.handle_id_or_object(data.get("id"))

    if not item:
        return Status.MISSING, {}

    return Status.OK, {"item": extract_from_item(item)}

# TODO test
@action.on("get-room-desc")
def get_room_desc(data):
    desc = amber.current_room.description

    return Status.OK, dictify(desc)


@action.on("get-locations")
def get_locations(data):
    return Status.OK, {"locations": extract_locations(amber.current_room.locations)}

# TODO test
@action.on("move-to")
def move_to(data):
    room_id = data.get("room")

    room = Room.handle_id_or_object(room_id)

    try:
        new = amber.walk_to(room)
    except NotAllowed as e:
        return Status.FORBIDDEN, {"message": e}

    return Status.OK, dictify(new)

# TODO test
@action.on("combine-items")
def combine_items(item_list):
    item1, item2 = item_list.get("items")
    item1, item2 = Item.handle_id_or_object(item1), Item.handle_id_or_object(item2)

    try:
        result = amber.combine(item1, item2)
    except NoSuchBlueprint as e:
        return Status.FORBIDDEN, {"message": e}

    return Status.OK, dictify(result)

# TODO test
@action.on("use-item")
def use_item(data):
    item_id = data.get("item")

    item = Item.handle_id_or_object(item_id)
    status, msg = item.use()

    if status is False:
        return Status.FORBIDDEN, {"message": msg}
    else:
        if isinstance(status, act.Action):
            return Status.OK, {**dictify(status.to_dict()), **{"message": msg}}
        else:
            return Status.OK, {"message": msg}

# TODO test
@action.on("desc-use")
def use_from_description(obj):
    obj = obj.get("item")

    try:
        obj = Item.handle_id_or_object(obj)

        status, msg = obj.pickup()
        if status is False:
            return Status.FORBIDDEN, dict(data={"message": msg})
        else:
            if isinstance(status, act.Action):
                return Status.OK, {**dictify(status.to_dict()), **{"message": msg}}
            else:
                return Status.OK, {"message": msg}

    # Is a room, not an item
    except IdMissing:
        obj = Room.handle_id_or_object(obj)

        room = amber.walk_to(obj)
        status = act.Action.move_to_room(room)
        return Status.OK, {**{"message": room.message}, **dictify(status.to_dict())}



class SocketHandler:
    def __init__(self, amber_inst, socket):
        self.sock = socket
        self.amber = amber_inst

        global amber
        amber = amber_inst

        self.events = {}
        self.actions = {}

        self.mgr_event = SocketEventManager("event")
        self.mgr_action = SocketEventManager("action")

    async def reply(self, status, data, **kwargs):
        log.debug("Sending to client")
        log.debug(data)

        payload = {
            "status": status,
            "data": data,
        }
        payload = {**payload, **kwargs}
        await self.sock.send(dumps(payload))

    async def handle(self, type_, additional, req_id, data):
        if type_ == "event":
            log.debug("Event: {}".format(additional))
            status, resp = await self.handle_event(additional, data)
            await self.reply(status, resp, req_id=req_id)

        elif type_ == "action":
            log.debug("Action: {}".format(additional))
            status, resp = await self.handle_action(additional, data)
            await self.reply(status, resp, req_id=req_id)

        else:
            log.warning("No such type: {}".format(type_))

    async def handle_event(self, event_type, data, **kwargs) -> tuple:
        if event_type in self.mgr_event.callbacks.keys():
            return await self.mgr_event.dispatch_event(event_type, data, **kwargs)

    async def handle_action(self, action_type, data, **kwargs) -> tuple:
        if action_type in self.mgr_action.callbacks.keys():
            return await self.mgr_action.dispatch_event(action_type, data, **kwargs)