"""Utility functions for reading input files.

This module contains helpers for computing checksums and loading
JSON files safely.  Using a checksum rather than a file name alone
allows the ingest pipeline to skip files that have been processed
previously even if they have been renamed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def compute_checksum(path: Path, block_size: int = 8192) -> str:
    """Compute the SHA‑256 checksum of a file and return it as hex."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    """Load a JSON document from `path` and return the parsed object.

    Raises json.JSONDecodeError if the file is not valid JSON.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)