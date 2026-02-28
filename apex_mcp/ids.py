"""Unique ID generator for APEX import operations.

IDs must be large integers unique within an import session.
Formula: 8_900_000_000_000_000 + (random_salt % 1_000_000) * 1_000_000 + counter.
"""
from __future__ import annotations
import os
import threading


class IdGenerator:
    """Session-scoped unique ID generator with named registry."""

    _BASE = 8_900_000_000_000_000
    _lock = threading.Lock()

    def __init__(self):
        # Salt from OS random bytes — 1M possible values, collision-resistant across sessions
        self._salt = int.from_bytes(os.urandom(4), "big") % 1_000_000
        self._counter = 0
        self._registry: dict[str, int] = {}

    def reset(self) -> None:
        """Reset counter and registry for a new app session."""
        with self._lock:
            self._salt = int.from_bytes(os.urandom(4), "big") % 1_000_000
            self._counter = 0
            self._registry = {}

    def next(self, name: str | None = None) -> int:
        """Generate and optionally register a new unique ID."""
        with self._lock:
            self._counter += 1
            new_id = self._BASE + self._salt * 1_000_000 + self._counter
            if name:
                self._registry[name] = new_id
            return new_id

    def get(self, name: str) -> int:
        """Retrieve a previously registered ID by name."""
        if name not in self._registry:
            raise KeyError(f"No ID registered under '{name}'. Call next('{name}') first.")
        return self._registry[name]

    def register(self, name: str, value: int) -> int:
        """Manually register a fixed ID (e.g., AUTH = 1000)."""
        self._registry[name] = value
        return value

    def has(self, name: str) -> bool:
        return name in self._registry

    def __call__(self, name: str | None = None) -> int:
        """Shorthand for next()."""
        return self.next(name)


# Module-level singleton — reset on each apex_create_app call
ids = IdGenerator()
