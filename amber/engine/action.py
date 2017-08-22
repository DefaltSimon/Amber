# coding=utf-8
import logging

log = logging.getLogger(__name__)


ADD_TO_INV = "add_to_inventory"
MOVE_TO = "move_to"
NOTHING = "nothing"

action_list = [
    ADD_TO_INV,
    MOVE_TO,
    NOTHING,
]


class Action:
    __slots__ = (
        "action", "message", "object"
    )

    def __init__(self, action, obj=None):
        if action not in action_list:
            raise TypeError("no such action: {}".format(action))

        self.action = action
        self.object = obj

    @classmethod
    def add_to_inventory(cls, item):
        return cls(ADD_TO_INV, item.id)

    @classmethod
    def move_to_room(cls, room):
        return cls(MOVE_TO, room.id)

    @classmethod
    def nothing(cls):
        return cls(NOTHING)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "object": self.object
        }
