# coding=utf-8
import logging
from typing import Union

from . import directory
from .types_ import Room
from .utils import Singleton
from .exceptions import InvalidParameter, NotAllowed,IdMissing


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class MessageDefaults:
    __slots__ = (
        "use", "failed_use", "failed_pickup", "failed_combine"
    )

    def __init__(self, use:str = None, failed_use:str = None, failed_pickup:str = None, failed_combine:str = None):
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
    def __init__(self, name, description:str = None, version:str = None):
        """
        The main class of the Amber engine.
        :param name: Game name
        :param description: Game description
        :param version: Version of your game
        """
        self.name = name
        self.description = description
        self.version = version

        # Internals

        self.current_room = None
        self.previous_room = None
        self.starting_room = None



        # Add instance ref to global directory
        if not directory.is_in_world("amber"):
            directory.add_to_world(self, "amber")


    @staticmethod
    def _late_load():
        for room in directory.obj_collector.rooms:
            room._finalize_loading()

    def set_starting_point(self, room):
        if not isinstance(room, (Room, str)):
            raise TypeError("expected Room/str, got {}".format(type(room)))

        if isinstance(room, str):
            r_name = str(room)

            room = directory.obj_collector.find_room_by_id(room)
            if not room:
                raise IdMissing("no such id: {}".format(r_name))

        self.starting_room = room

    def walk_to(self, room: Union[Room, str]) -> Room:
        """
        Moves the player to a different room. A check
        :param room:
        :return:
        """
        # Checks
        if isinstance(room, str):
            r_name = str(room)

            room = directory.obj_collector.find_room_by_id(room)
            if not room:
                raise InvalidParameter("{} does not exist".format(r_name))

        if not isinstance(room, (Room, str)):
            raise InvalidParameter("room: expected Room/str, got {}".format(type(room)))

        # If
        if not self.current_room.can_leave:
            raise NotAllowed("you are not allowed to leave this room")
        if not room.can_enter:
            raise NotAllowed("you are not allowed to enter this room")

        # Main part
        self.previous_room = self.current_room
        self.current_room = room

        return self.current_room

    def combine(self, item1, item2):
        # TODO implement
        pass

    def start(self, autosave=True):
        self._late_load()

