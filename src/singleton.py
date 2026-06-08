import threading
from typing import Any


class Singleton:
    __instance = None
    __lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any):
        if not cls.__instance:
            with cls.__lock:
                if not cls.__instance:
                    cls.__instance = super().__new__(cls)
                    cls.__instance._initialized = False
        return cls.__instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
