"""Adapter registry.

This module maintains a global mapping of adapter names to functions.
When a user invokes the ingest CLI they specify an adapter name; the
registry will look up and return the appropriate parser.  Adapters
should accept a Python object loaded from JSON (usually a dict) and
yield canonical records as dictionaries.
"""
from __future__ import annotations

from typing import Callable, Dict, Iterable, Any

from . import generic_responses_v1


# Registry mapping adapter names to callables
_REGISTRY: Dict[str, Callable[[Any], Iterable[Dict[str, Any]]]] = {
    "generic_responses_v1": generic_responses_v1.parse,
}


def get_adapter(name: str) -> Callable[[Any], Iterable[Dict[str, Any]]]:
    """Return the adapter callable registered under `name`.

    Raises:
        KeyError: if no adapter is registered under that name.
    """
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown adapter: {name}") from exc


def get_adapter_names() -> list[str]:
    """Return a sorted list of registered adapter names."""
    return sorted(_REGISTRY.keys())