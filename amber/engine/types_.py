# coding=utf-8
import logging
import re
from typing import Union

from . import directory
from .exceptions import IdMissing, AmberException
from .events import EventManager

log = logging.getLogger(__name__)


def _generate_id(preferred: str):
    """
    Internal use, generates an id based on item's name. If preferred id is not available, adds numbers to the end. (item1, item2, ...)
    :param preferred: The id you prefer is generated
    :return: Generated ID (unique to all types)
    """
    if not directory.id_exists(preferred):
        directory.add_id(preferred)
        return preferred
    else:
        # Loops until a non-used number is found
        c = 1
        while directory.id_exists(preferred) and preferred is not None:
            buff = "{}{}".format(preferred, c)
            preferred = str(buff)

            c += 1

        directory.add_id(preferred)
        return preferred


def _get_item_postponed(item_id):
    """
    For internal use, to postpone getting an item until everything is loaded
    (Ab)uses generators
    :param item_id: id of the Item
    :return: Item / None
    """
    yield item_id, directory.obj_collector.find_item_by_id(item_id)


def _get_room_postponed(room_id):
    """
    For internal use, to postpone getting the room until all rooms are loaded
    Ab)uses generators
    :param room_id: id of the Room
    :return: Room / None
    """
    yield directory.obj_collector.find_room_by_id(room_id)

# Regex for use in descriptions
desc_regex = re.compile(r"({\w+\|\w+})", re.MULTILINE)

class Description:
    def __init__(self, string: Union[str, list], desc_id=None):
        """
        Creates and parses a text with dynamic links to items/rooms
        :param string: Text to parse
        """
        # TODO implement removing sentences after usage
        self.text = str(string)
        self._groups = []

        self.rooms = []
        self.items = []

        self._q_rooms = []
        self._q_items = []

        self._parse_string()

        self.id = None
        if not desc_id:
            self.id = _generate_id("description")
        elif directory.id_exists(desc_id):
            raise RuntimeError("object with id '{}' already exists".format(desc_id))
        else:
            self.id = _generate_id(desc_id)


    def _parse_string(self):
        self._groups = list(desc_regex.findall(self.text))

        for group in self._groups:
            type_, obj_id = group.lstrip("{").rstrip("}").split("|")

            if type_ == "room":
                self._q_rooms.append(obj_id)
            elif type_ == "item":
                self._q_items.append(obj_id)
            else:
                log.warning("{} is not a valid type, ignoring".format(type_))
                continue

    def _finalize_loading(self):
        """
        Internal, should be called when all stuff is loaded
        :return: None
        """
        for q_room in self._q_rooms:
            room = directory.obj_collector.find_room_by_id(q_room)
            if not room:
                raise IdMissing("{} is not a room".format(q_room))

            self.rooms.append(room)

        for q_item in self._q_items:
            item = directory.obj_collector.find_item_by_id(q_item)
            if not item:
                raise IdMissing("{} is not an item".format(q_item))

            self.items.append(item)

# TODO music


class Room:
    def __init__(self, name: str, description:Union[str, list] = None, initial_msg:str = None, locations:list = None, image=None, sound=None, room_id=None):
        """
        Creates a room that the player "can" step in
        :param name: Name of the room, displayed at the top
        :param description: Room description (see Descriptions)
        :param initial_msg: The message that is displayed when the player enters the room for the first time (see Top Messages)
        :param locations: a list of Room's that can be accessed from this room
        :param image: Path to the image that should be displayed in this room
        :param sound: Path to the sound that should be played here
        :param room_id: Item id that you assign (OPTIONAL). Defaults to the name if available, otherwise numbers (room_name1, room_name2, ...) are added
        """
        self._name = name
        self._desc = Description(description)
        self._msg = initial_msg

        self._locations = []
        if locations:
            for loc in locations:
                # Location can be either a Room object or an id
                if isinstance(loc, (Room, str)):
                    self._locations.append(loc)
                else:
                    raise TypeError("expected Room/str, got {}".format(type(loc)))

        self._image = image
        self._sound = sound

        # Generates / uses an id
        # Tries the name. If taken, adds numbers at the end
        self.id = None
        if not room_id:
            self.id = _generate_id(self._name)
        elif directory.id_exists(room_id):
            raise RuntimeError("object with id '{}' already exists".format(room_id))
        else:
            self.id = _generate_id(room_id)


        # Internal vars
        self._entered = False

        # Used for events
        events = ["enter", "leave", "description", "message", "name", "locations", "image", "sound"]
        self._event_mgr = EventManager(self._name, events)

        # Add item to cache
        directory.obj_collector.add_room(self)

    # PROPERTIES
    @property
    def name(self) -> str:
        res = self._event_mgr.dispatch_event("name", self._name)
        if res:
            return res
        else:
            return self._name

    @property
    def description(self) -> Union[str, Description]:
        res = self._event_mgr.dispatch_event("description", self._desc)
        if res:
            return res
        else:
            return self._desc

    @property
    def initial_message(self) -> str:
        res = self._event_mgr.dispatch_event("message", self._msg)
        if res:
            return res
        else:
            if self._entered:
                return ""
            else:
                self._entered = True
                return self._msg

    @property
    def locations(self) -> list:
        res = self._event_mgr.dispatch_event("locations", self._locations)
        if res:
            return res
        else:
            return self._locations

    @property
    def image(self):
        res = self._event_mgr.dispatch_event("image", self._image)
        if res:
            return res
        else:
            return self._image

    @property
    def sound(self):
        res = self._event_mgr.dispatch_event("sound", self._sound)
        if res:
            return res
        else:
            return self._sound

    # EVENT REGISTERING
    def event(self, event_name):
        """
        Registers an event handler via decorators
        :param event_name: Your first parameter: name of the event (by property names)
        :return: function for the decorator to use
        """
        def real_dec(fn):
            if not callable(fn):
                raise TypeError("not a function")

            # Register the event
            self._event_mgr.set_event_handler(event_name, fn)
            return fn

        return real_dec

    @staticmethod
    def handle_id_or_object(room_or_id):
        """
        Internal for ease of use (to convert room id to Room)
        :param room_or_id: Room object or room id
        :return: Room
        """
        if isinstance(room_or_id, Room):
            return room_or_id
        else:
            room = directory.obj_collector.find_room_by_id(room_or_id)
            if room:
                return room
            else:
                raise IdMissing("room {} does not exist".format(room_or_id))

    def _finalize_loading(self):
        log.debug("Finalizing {}".format(self._name))
        for c, room_i in enumerate(self._locations.copy()):
            if isinstance(room_i, str):
                room = directory.obj_collector.find_room_by_id(room_i)
                if not room:
                    raise IdMissing("Room id {} does not exist".format(room_i))
            else:
                continue

            self._locations[c] = room

    def add_location(self, location):
        """
        Adds a location that the player can traverse
        :param location: Room object
        :return: None
        """
        loc = self.handle_id_or_object(location)
        self._locations.append(loc)

    def remove_location(self, location):
        """
        Removes a "path" from this room (to be used in custom logic scripts
        :param location: Room object
        :return: bool indicating success
        """
        loc = self.handle_id_or_object(location)
        self._locations.remove(loc)

    def set_as_starting_room(self):
        amber = directory.world.get("amber")
        if not amber:
            raise AmberException("Amber is not yet instantiated, do so at the top of the script!")


        if amber.starting_room is not None:
            log.warning("starting room was already set, but still overwriting")

        amber.starting_room = self

    @property
    def can_enter(self) -> bool:
        """
        Property specifying if the user's allowed to enter this room. Can be prevented by a custom event
        :return: bool
        """
        res = self._event_mgr.dispatch_event("enter", self)
        # None is the default return type (when there is no function registered)
        if res is None:
            res = True

        return res

    @property
    def can_leave(self) -> bool:
        """
        Property indicating if the user can leave this room. Can be prevented by a custom event handler
        :return: bool
        """
        res = self._event_mgr.dispatch_event("leave", self)
        if res is None:
            res = True

        return res


class Blueprint:
    def __init__(self, ingredient1, ingredient2, result, message: str = None, recipe_id:str = None):
        """
        Binds two items together to they can form another item
        :param ingredient1: Item
        :param ingredient2: Item
        :param result: Item that is made from two ingredients
        :param message: Message to be displayed when combining
        :param recipe_id: Blueprint ID that you can assign (OPTIONAL, see Room initialization)
        """
        ingredient1 = Item.handle_id_or_object(ingredient1)
        ingredient2 = Item.handle_id_or_object(ingredient2)
        result      = Item.handle_id_or_object(result)

        self.item1   = ingredient1
        self.item2   = ingredient2
        self._result = result

        self._msg = message

        self.id = None
        if not recipe_id:
            self.id = _generate_id("{}-{}".format(ingredient1.name, ingredient2.name))
        elif directory.id_exists(recipe_id):
            raise RuntimeError("object with id '{}' already exists".format(recipe_id))
        else:
            self.item_id = _generate_id(recipe_id)

        directory.obj_collector.add_blueprint(self)


class Item:
    def __init__(self, name, description:Union[str, list] = None, recipes:list = None, item_id:str = None):
        self._name = name
        self._desc = Description(description)

        self._recipes = []
        # Parses recipes / gets instances if id is provided
        if recipes:
            for rec in recipes:

                if isinstance(rec, Blueprint):
                    self._recipes.append(rec)
                elif isinstance(rec, str):
                    # Find by id
                    f_rec = directory.obj_collector.find_recipe_by_id(rec)
                    if f_rec:
                        self._recipes.append(f_rec)
                    else:
                        raise TypeError("Blueprint id invalid")

        # Generates / uses an id
        # Tries the name. If taken, adds numbers at the end
        self.item_id = None
        if not item_id:
            self.item_id = _generate_id(self._name)
        elif directory.id_exists(item_id):
            raise RuntimeError("object with id '{}' already exists".format(item_id))
        else:
            self.item_id = _generate_id(item_id)


        # INTERNALS

        # Used for events
        events = ["name", "description", "recipes"]
        self.event = EventManager(self._name, events)

        # Add item to cache
        directory.obj_collector.add_item(self)

    # PROPERTIES
    @property
    def name(self) -> str:
        res = self.event.dispatch_event("name", self._name)
        if res:
            return res
        else:
            return self._name

    @property
    def description(self) -> Union[Description, str]:
        res = self.event.dispatch_event("description", self._desc)
        if res:
            return res
        else:
            return self._desc

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
        self.event.set_event_handler(event_name, fn)
        return fn


    @staticmethod
    def handle_id_or_object(item_or_id):
        """
        Internal for ease of use (to convert item id to Item)
        :param item_or_id: Room object or room id
        :return: Item
        """
        if isinstance(item_or_id, Item):
            return item_or_id
        else:
            item = directory.obj_collector.find_item_by_id(item_or_id)
            if item:
                return item
            else:
                raise IdMissing("item {} does not exist".format(item_or_id))