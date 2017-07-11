# coding=utf-8
import threading

def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper


class Status:
    OK = "ok"
    FORBIDDEN = "forbidden"
    MISSING = "missing"
    ERROR = "error"