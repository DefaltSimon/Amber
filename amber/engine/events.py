# coding=utf-8
import logging
from .exceptions import EventMissing


log = logging.getLogger(__name__)


class EventManager:
    def __init__(self, name, events: list):
        self._name = name

        self._events = {str(a): None for a in events}

    # noinspection PyCallingNonCallable
    def dispatch_event(self, event_name, *args, **kwargs):
        """
        Internal use only, to dispatch individual events
        :param event_name: Event name
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :return: None or what the function returns
        """
        if event_name not in self._events.keys():
            raise EventMissing("{} is not an event".format(event_name))

        fn = self._events.get(event_name)
        if fn:
            return fn(*args, **kwargs)
        else:
            return None

    def set_event_handler(self, event_name, fn):
        if event_name not in self._events.keys():
            raise EventMissing("{} is not a valid event!".format(event_name))

        if fn in self._events.values():
            log.warning("Event function {} for {} was already registered, overwriting".format(event_name, self._name))

        log.info("{} for {} registered".format(event_name, self._name))
        self._events[event_name] = fn
