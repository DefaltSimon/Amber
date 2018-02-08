# coding=utf-8
import logging
from random import randint
try:
    from ujson import dumps
except ImportError:
    from json import dumps
import inspect

from .web_utils import Status, get_engine_version
from ..engine.types_ import Room, Description, Item, Blueprint
from ..engine.exceptions import NoSuchBlueprint, IdMissing
from ..engine import action as act, presence

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


def parse_event_response(res: tuple) -> tuple:
    # If user returns only the message, default to no action, just the message
    if not isinstance(res, tuple):
        return act.Action.nothing(), res

    # Max two arguments
    if len(res) != 2:
        raise TypeError("expected only two arguments, got {}".format(len(res)))

    o_act, message = res

    if isinstance(o_act, act.Action):
        if o_act.action == act.ADD_TO_INV:
            amber._add_to_inventory(o_act.object)

        elif o_act.action == act.MOVE_TO:
            st, message = amber.walk_to(o_act.object)

        elif o_act.action == act.REMOVE_FROM_INV:
            items = o_act.object
            for item in items:
                amber._remove_from_inventory(item)


        # Add action to dictionary - event returned an Action
        return Status.OK, {**{"message": message}, **o_act.to_dict()}

    if isinstance(o_act, bool):
        return Status.OK if o_act else Status.FORBIDDEN, {"message": message}

    # The first parameter should always be either Action or bool
    raise RuntimeError("First tuple parameter should be an Action object or a bool, got {}".format(type(o_act).__name__))


def extract_from_room(room: Room) -> dict:
    return {
        "name": room.name,
        "description": extract_from_description(room.description),
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
        "rooms": {a.id: extract_from_room_name_id(a) for a in desc.rooms},
        "items": {a.id: extract_from_item(a) for a in desc.items},
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


def extract_locations(obj: list) -> list:
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

######
# ROOM
# room/
######


# /get

@action.on("room/get")
def get_room_info(data):
    """
    Gets current room state
    :param data: None

    :return dict(Room)
    """
    cr = amber.current_room

    return Status.OK, extract_from_room(cr)


@action.on("room/get/description")
def get_room_desc(data):
    """
    Gets current room description
    :param data: None

    :return dict(Description)
    """
    desc = amber.current_room.description

    return Status.OK, extract_from_description(desc)


@action.on("room/get/locations")
def get_room_paths(data):
    """
    Gets possible ways to different rooms from the current one
    :param data: None

    :return: list(Room, ...)
    """
    return Status.OK, extract_locations(amber.current_room.locations)


@action.on("room/get/name")
def get_room_name(data):
    """
    Gets the current room name
    :param data: None

    :return: str
    """
    cr = amber.current_room

    return Status.OK, cr.name


@action.on("room/get/image")
def get_room_image(data):
    """
    Gets the current room image.
    :param data: None

    :return: str
    """
    image = amber.current_room.image

    return Status.OK, image


@action.on("room/use/description")
def use_from_description(obj):
    """
    Uses a description item
    :param obj:

    :return: dict(message, Action)
    """
    obj = obj.get("item")

    try:
        obj = Item.handle_id_or_object(obj)

        resp = obj.pickup()
        return parse_event_response(resp)

    # Is a room, not an item
    except IdMissing:
        obj = Room.handle_id_or_object(obj)

        resp = amber.walk_to(obj)

        return parse_event_response(resp)


@action.on("room/enter")
def move_to(data):
    """
    Enters a room
    :param data: dict(room: str)

    :return: dict(room: Room, Action)
    """
    room_id = data.get("room")

    room = Room.handle_id_or_object(room_id)

    resp = amber.walk_to(room)
    status, stuff = parse_event_response(resp)

    return status, {**(stuff if type(stuff) is dict else {}), **{"room": extract_from_room(room)}}


######
# GAME
# game/
######


@event.on("game/handshake")
def handshake(data):
    """
    Initial handshake that must be completed when connected
    :param data: dict(uiVersion)

    :return: dict(engineVersion, author, name, description)
    """
    ui_version = data.get("uiVersion")
    log.info("Client connected with uiVersion {}".format(ui_version))

    payload = {
        "engineVersion": get_engine_version(),
        "author": amber.author,
        "name": amber.name,
        "description": amber.description,
    }

    return Status.OK, payload


@action.on("game/get/inventory")
def get_inventory(data):
    """
    Gets inventory state
    :param data: None

    :return: list
    """
    return Status.OK, dictify(amber.inventory)


@action.on("game/get/intro")
def get_intro(data):
    """
    Gets the game intro
    :param data: None

    :return: dict(title, image, sound)
    """
    intro = presence.world.get("intro")
    if not intro:
        return Status.MISSING, None

    pl = {
        "title": intro.title,
        "image": intro.image,
        "sound": intro.sound,
    }

    return Status.OK, pl


######
# INVENTORY
# inventory/
######

@action.on("inventory/get")
def get_inventory(data):
    """
    Returns the current inventory state
    :param data: None

    :return: dict(inventory: list)
    """
    return dictify(amber.inventory)


@action.on("inventory/use")
def use_item(data):
    """
    Uses an item in your inventory
    :param data: dict(item: str)

    :return: dict(message, Action)
    """
    item_id = data.get("item")
    item = Item.handle_id_or_object(item_id)

    resp = item.use()

    return parse_event_response(resp)


@action.on("inventory/combine")
def combine_items(data):
    """
    Combines two items (either both in inventory or one in room)
    :param data: dict(items: list)

    :return:
    If successful, dict(item: Item, Action.remove_item())
    """
    item1, item2 = data.get("items")

    obj1, obj2 = presence.obj_collector.find_by_id(item1), presence.obj_collector.find_by_id(item2)

    if isinstance(obj1, Item) and isinstance(obj2, Item):
        # Both are items, do a normal combine

        bp = amber.combine(item1, item2)

        if not bp:
            return Status.MISSING, amber.defaults.failed_combine
        else:
            res_item = bp.result
            # Default status is True, parse_event_response does not automatically remove items from inventory
            status, additional = parse_event_response(bp.combine())

            # Default behaviour: remove previous items, add the new one into inventory
            if status == Status.OK:
                amber._add_to_inventory(res_item)
                amber._remove_from_inventory(obj1)
                amber._remove_from_inventory(obj2)

                # on REMOVE_FROM_INVENTORY, client automatically refreshes the inventory, so this is fine
                return Status.OK, {**{"message": bp.message}, **act.Action.remove_from_inventory((obj1, obj2)).to_dict()}
            # If user is not allowed to combine, return a message (additional)
            else:
                return status, additional

    # Either of the items is an Item and a Room
    elif (isinstance(obj1, Room) and isinstance(obj2, Item)) or (isinstance(obj1, Item) and isinstance(obj2, Room)):
        # TODO room combine logic
        pass

    # TODO prevent Room + Room


######
# ITEM
# item/
######

@action.on("item/get")
def get_item_info(data):
    """
    Gets item info
    :param data: dict(id)

    :return: dict(item: Item)
    """
    try:
        item = Item.handle_id_or_object(data.get("id"))
    except IdMissing:
        return Status.MISSING, {}

    return Status.OK, {"item": extract_from_item(item)}


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