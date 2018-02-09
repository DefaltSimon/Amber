# coding=utf-8
import logging
import time
from typing import Union

from . import presence
from .types_ import Room, Item, Blueprint
from .utils import Singleton
from .exceptions import IdMissing, AmberException

# Flask webmodule import
from ..web_modules.web_core import run_web


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MessageDefaults:
    __slots__ = (
        "use", "failed_use", "failed_pickup", "failed_combine"
    )

    def __init__(self, use: str = None, failed_use: str = None, failed_pickup: str = None, failed_combine: str = None):
        """
        MessageDefaults is a class designed to simplify general messages
        This applies ONLY if not overridden by an Item!
        :param use: What to say when an Item is used but has no description
        :param failed_use: What to say when an Item cannot be used with something else
        :param failed_pickup: What to say when you can't pick up an item
        :param failed_combine: What to say when you can't combine two items
        """
        self.use = use

        self.failed_use = failed_use

        self.failed_pickup = failed_pickup

        self.failed_combine = failed_combine


class Amber(metaclass=Singleton):
    def __init__(self, name, description : str = None, version : str = None, author : str = None, defaults : MessageDefaults = None):
        """
        The main class of the Amber engine.
        :param name: Game name
        :param description: Game description
        :param version: Version of your game
        :param author: You, the author
        :param defaults: MessageDefaults instance
        """
        self.name = name
        self.description = description
        self.version = version
        self.author = author

        self.current_room = None
        self.previous_room = None
        self.starting_room = None

        self.inventory = []

        # Internals
        self._start_time = time.time()

        self.defaults = defaults or MessageDefaults()

        # Add instance ref to global directory
        if not presence.is_in_world("amber"):
            presence.add_to_world(self, "amber")

    # noinspection PyProtectedMember
    @staticmethod
    def _lazy_load():
        for room in presence.obj_collector.rooms:
            room._finalize_loading()

    def set_starting_point(self, room):
        if not isinstance(room, (Room, str)):
            raise TypeError("expected Room/str, got {}".format(type(room)))

        if isinstance(room, str):
            r_name = str(room)

            room = presence.obj_collector.find_room_by_id(room)
            if not room:
                raise IdMissing("no such id: {}".format(r_name))

        self.starting_room = room

    def walk_to(self, room: Union[Room, str]) -> tuple:
        """
        Moves the player to a different room. A check
        :param room:
        :return: tuple(Action/bool, message)
        """
        # Checks
        if isinstance(room, str):
            r_name = str(room)

            room = presence.obj_collector.find_room_by_id(room)
            if not room:
                raise IdMissing("{} does not exist".format(r_name))

        if not isinstance(room, (Room, str)):
            raise TypeError("room: expected Room/str, got {}".format(type(room)))

        resp = self.current_room.enter()

        # Main part
        self.previous_room = self.current_room
        self.current_room = room

        return resp

    def combine(self, item1: Union[str, Item], item2: Union[str, Item]) -> Union[None, Blueprint]:
        """
        Combines two items together
        :param item1: First item to combine
        :param item2: Second item to combine
        :return: Item that is made
        """
        # Check types
        item1 = Item.handle_id_or_object(item1)
        item2 = Item.handle_id_or_object(item2)

        # Find matching blueprint
        bp = None
        for r in item2.blueprints + item1.blueprints:
            assert isinstance(r, Blueprint)

            if r.matches_items(item1, item2):
                bp = r
                break

        if not bp:
            return None

        # Return new item
        return bp

    def start(self, autosave=True, open_browser=True):
        # TODO implement autosave and saving
        """
        Begins the game. This function MUST be placed at the end of the file.
        :param autosave: Whether to enable autosave or not
        :param open_browser: If you want to automatically open the browser
        :return: None
        """
        log.debug("Starting lazy-load")
        self._lazy_load()
        log.debug("Finished lazy-load")

        if not self.starting_room:
            raise AmberException("no starting room")

        self.current_room = self.starting_room

        run_web(self, open_browser)

    # INTERNAL METHODS
    def _add_to_inventory(self, item: Union[Item, str]):
        item = Item.handle_id_or_object(item)

        if item not in self.inventory:
            self.inventory.append(item)

    def _remove_from_inventory(self, item: Union[Item, str]):
        item = Item.handle_id_or_object(item)

        if item in self.inventory:
            self.inventory.remove(item)
