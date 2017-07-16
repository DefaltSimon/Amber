# coding=utf-8
import logging

log = logging.getLogger(__name__)

action_list = [
    "add-to-inventory",
    "move-to",
]

ADD_TO_INV = "add-to-inventory"
MOVE_TO = "move-to"


class Action:
    __slots__ = (
        "action", "message", "obj"
    )

    def __init__(self, action, obj):
        if action not in action_list:
            raise TypeError("no such action: {}".format(action))

        self.action = action
        self.obj = obj

    @classmethod
    def add_to_inventory(cls, item):
        return cls(ADD_TO_INV, item)

    @classmethod
    def move_to_room(cls, room):
        return cls(MOVE_TO, room)

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "obj": self.obj
        }
