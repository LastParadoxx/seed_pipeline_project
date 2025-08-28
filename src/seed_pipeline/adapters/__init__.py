"""Adapters package.

An adapter is a callable that takes a Python object loaded from JSON
(typically a dictionary) and yields canonical records.  Canonical
records are dictionaries with the keys:

* `seed`: the raw seed string
* `variation`: the raw variation string
* `miner_ext_id`: an optional string identifying the miner (or hotkey)
* `score`: an optional float representing a quality score
* `raw`: an arbitrary payload to store on the observation

The purpose of adapters is to decouple parsing of diverse input
formats from the core ingestion logic.  To add support for a new
format, create a new module and register it in `registry.py`.
"""

from .registry import get_adapter_names, get_adapter

__all__ = ["get_adapter_names", "get_adapter"]