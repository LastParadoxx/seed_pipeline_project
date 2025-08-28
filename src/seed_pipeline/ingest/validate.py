"""Validation utilities for canonical records.

The ingest pipeline operates on canonical records produced by adapters.
Before processing a record into the database we validate that
mandatory fields are present and non‑empty.  Records that fail
validation are counted and skipped.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple


def validate_record(record: Dict[str, Any]) -> Tuple[bool, str | None]:
    """Validate a canonical record.

    Ensures that `seed` and `variation` are non‑empty strings.  Other
    fields are optional.  Returns a tuple of (is_valid, reason).  If
    `is_valid` is False then the record should be skipped.
    """
    seed = record.get("seed")
    variation = record.get("variation")
    if not seed or not isinstance(seed, str):
        return False, "missing or invalid seed"
    if not variation or not isinstance(variation, str):
        return False, "missing or invalid variation"
    return True, None