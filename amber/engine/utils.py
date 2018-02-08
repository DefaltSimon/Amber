# coding=utf-8


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ObjectType:
    ROOM = "room"
    ITEM = "item"
    RECIPE = "recipe"


def get_attribute_values(_class):
    attributes = get_class_attributes(_class)
    return [getattr(_class, a) for a in attributes]


def get_class_attributes(_class):
    # oh dear god
    return [a for a in dir(_class) if
            not a.startswith('__') and
            not callable(getattr(_class, a))]
