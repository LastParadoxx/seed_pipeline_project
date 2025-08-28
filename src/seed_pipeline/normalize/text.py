"""String normalisation utilities.

The ingestion pipeline relies on normalising seed and variation strings to
deterministically map inputs to canonical representations.  The
functions in this module perform the following operations:

* Lowercase conversion
* Unicode NFKD normalisation and accent stripping
* Collapse of multiple whitespace characters into a single space
* Optional collapse of repeated characters (e.g. "aaasem" -> "asem")
* Retention of intra‑word apostrophes and hyphens

If you need to customise the behaviour (e.g. enable repeated character
collapse) you can pass `collapse_repeats=True`.  Note that repeated
character collapse is disabled by default because it may conflate
genuinely different names.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata


_WHITESPACE_RE = re.compile(r"\s+")
_REPEATS_RE = re.compile(r"(.)\1{2,}")  # match character repeated 3+ times


def _strip_accents(text: str) -> str:
    """Strip accents from a Unicode string using NFKD normalisation."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_text(text: str, *, collapse_repeats: bool = False) -> str:
    """Normalise an arbitrary string.

    This helper underpins both `normalize_seed` and `normalize_variation`.

    Args:
        text: The raw input string.
        collapse_repeats: If True, collapse runs of the same character
            longer than two down to a single occurrence.  This can help
            de‑duplicate noisy variations but may also remove genuine
            elongations.

    Returns:
        A normalised representation suitable for hashing and equality
        comparison.
    """
    if not isinstance(text, str):
        text = str(text)
    # Trim leading/trailing whitespace
    text = text.strip()
    # Lowercase
    text = text.lower()
    # Remove accents
    text = _strip_accents(text)
    # Collapse whitespace
    text = _WHITESPACE_RE.sub(" ", text)
    # Optionally collapse repeated characters beyond 2
    if collapse_repeats:
        def _collapse(match: re.Match[str]) -> str:
            return match.group(1)
        text = _REPEATS_RE.sub(_collapse, text)
    return text


def normalize_seed(text: str, *, collapse_repeats: bool = False) -> str:
    """Normalise a seed name.

    Currently this simply delegates to `normalize_text`.  In future you
    could add seed‑specific logic here.
    """
    return normalize_text(text, collapse_repeats=collapse_repeats)


def normalize_variation(text: str, *, collapse_repeats: bool = False) -> str:
    """Normalise a variation string.

    Delegates to `normalize_text`.  Variation normalisation uses the same
    rules as seeds.
    """
    return normalize_text(text, collapse_repeats=collapse_repeats)


def md5_hex(text: str) -> str:
    """Return the hexadecimal MD5 digest of `text`.

    Args:
        text: A normalised string (so the hash is deterministic).
    Returns:
        A 32‑character hexadecimal string.
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()