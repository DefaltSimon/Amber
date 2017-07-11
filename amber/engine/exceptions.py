# coding=utf-8


class AmberException(Exception):
    """
    Base exception class
    """
    pass

class IdMissing(AmberException):
    """
    Raised when an id you provided does not exist in cache
    """
    pass


class EventMissing(AmberException):
    """
    Raised when you try to access an event type that does not exist
    """
    pass

class InvalidParameter(AmberException):
    """
    Raised when an unexpected parameter is passed to the function
    """
    pass


class NotAllowed(AmberException):
    """
    General exception for things you're not allowed to do (when trying to enter a room, for example).
    """
    pass
