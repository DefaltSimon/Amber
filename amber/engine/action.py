# coding=utf-8
import logging

log = logging.getLogger(__name__)


ADD_TO_INV = "add_to_inventory"
REMOVE_FROM_INV = "remove_from_inventory"
MOVE_TO = "move_to"
NOTHING = "nothing"

action_list = [
    ADD_TO_INV,
    MOVE_TO,
    NOTHING,
    REMOVE_FROM_INV,
]


class Action:
    __slots__ = (
        "action", "message", "object"
    )

    def __init__(self, action, obj=None):
        if action not in action_list:
            raise TypeError("no such action: {}".format(action))

        # Automatically creates a tuple if not present
        if action == REMOVE_FROM_INV:
            if not isinstance(obj, (tuple, list)):
                obj = (obj, )

        self.action = action
        self.object = obj

    @classmethod
    def add_to_inventory(cls, item):
        return cls(ADD_TO_INV, item.id)

    @classmethod
    def move_to_room(cls, room):
        return cls(MOVE_TO, room.id)

    @classmethod
    def remove_from_inventory(cls, items: tuple):
        return cls(REMOVE_FROM_INV, items)

    @classmethod
    def nothing(cls):
        return cls(NOTHING)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "object": self.object
        }
