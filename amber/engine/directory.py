# coding=utf-8

# Utility to keep track of certain instances

import logging
from .utils import Singleton


log = logging.getLogger(__name__)

# Storage for singletons

world = {}
def add_to_world(instance, name):
    if name not in world.keys():
        world[name] = instance


def remove_from_world(name):
    if name in world.keys():
        del world[name]


def is_in_world(name):
    return name in world.keys()



# Keeps track of already-used ids

ids = []
def add_id(id_):
    if id_ not in ids:
        ids.append(id_)

def id_exists(id_):
    return id_ in ids

def remove_id(id_):
    global ids
    if id_ in ids:
        ids = [i for i in ids if i != id_]



class ObjectCollector(metaclass=Singleton):
    def __init__(self):
        self.items = []
        self.rooms = []
        self.blueprints = []

    def add_item(self, item):
        """
        Adds an item to the cache
        :param item: Item object to register
        :return: None
        """
        # if not isinstance(item, Item):
        #     raise TypeError("expected Item, got {}".format(type(item)))
        if item not in self.items:
            log.debug("Adding item:{} to cache".format(item.name))
            self.items.append(item)
        else:
            log.warning("Item {} was already in cache".format(item.name))

    def add_room(self, room):
        """
        Adds a room to the cache
        :param room: Room object to register
        :return: None
        """
        # if not isinstance(room, Room):
        #     raise TypeError("expected Room, got {}".format(type(room)))

        if room not in self.items:
            log.debug("Adding room:{} to cache".format(room.name))
            self.rooms.append(room)
        else:
            log.warning("Room {} was already in cache".format(room.name))

    def add_blueprint(self, bp):
        """
        Adds a recipe to the cache
        :param bp: Blueprint object to register
        :return: None
        """
        # if not isinstance(recipe, Room):
        #     raise TypeError("expected Blueprint, got {}".format(type(recipe)))
        if bp not in self.items:
            log.debug("Adding blueprint:{} to cache".format(bp.name))
            self.blueprints.append(bp)
        else:
            log.warning("Blueprint {} was already in cache".format(bp.name))


    def find_item_by_id(self, item_id: str):
        """
        Finds an Item by its id
        :param item_id: Item id
        :return: Item or None if not found
        """
        for item in self.items:
            if item.id == item_id:
                return item

        return None

    def find_room_by_id(self, room_id: str):
        """
        Finds a Room by its id
        :param room_id: Room id
        :return: Room or None if not found
        """
        for room in self.rooms:
            if room.id == room_id:
                return room

        return None

    def find_recipe_by_id(self, recipe_id: str):
        """
        Finds a Blueprint by its id
        :param recipe_id: Blueprint id
        :return: Blueprint or None if not found
        """
        for recipe in self.blueprints:
            if recipe.id == recipe_id:
                return recipe

        return None

    def find_by_id_fuzzy(self, object_id: str):
        """
        Attempts to find the matching object by an id in all caches
        :param object_id: object id
        :return: Room/Item/Blueprint or None if not found
        """
        obj = self.find_item_by_id(object_id)
        if obj:
            return obj

        obj = self.find_room_by_id(object_id)
        if obj:
            return obj

        obj = self.find_recipe_by_id(object_id)
        if obj:
            return obj

        return None

# Singleton, so it only has one instance
obj_collector = ObjectCollector()
