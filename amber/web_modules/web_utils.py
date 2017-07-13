# coding=utf-8
import threading
import os
import re

version_pattern = re.compile(r"^__version__\s*=\s*[\"'](.*)[\"']", re.MULTILINE)
MODULE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper


def get_engine_version():
    with open(os.path.join(MODULE_DIR, "__init__.py")) as file:
        return re.search(version_pattern, file.read()).groups()[0]

class Status:
    OK = "ok"
    FORBIDDEN = "forbidden"
    MISSING = "missing"
    ERROR = "error"