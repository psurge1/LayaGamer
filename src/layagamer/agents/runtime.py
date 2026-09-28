"""Lazily load and share one local Laya Router across compatible agents."""
from threading import Lock
from typing import Any


class SharedRouter:
    def __init__(self, device: str | None = None):
        self.device = device
        self._router: Any = None
        self._load_lock = Lock()

    def predict(self, *args, **kwargs) -> dict:
        if self._router is None:
            with self._load_lock:
                if self._router is None:
                    from laya import Router
                    self._router = Router(**({"device": self.device} if self.device else {}))
        return self._router.predict(*args, **kwargs)
