"""Parse generic response JSON files.

This adapter supports a class of JSON files where a top level `responses`
object contains one or more response items.  Each response item has a
`variations` mapping from seed names to lists of variations (strings).
Additional metadata such as `hotkey` and `uid` may be present to
identify the miner.  A quality score may be encoded elsewhere but is
treated as optional.

Example input structure (simplified):

```json
{
  "seed_names": ["Michael", "Ahmed", ...],
  "responses": {
    "149": {
      "uid": 149,
      "hotkey": "0xabc123",
      "variations": {
        "michael": ["micheal", "mikel"],
        "ahmed":   ["ahmad", "amed"]
      }
    },
    "150": {
      ...
    }
  }
}
```

The adapter yields one canonical record for each `(seed, variation)` pair.
The `miner_ext_id` is taken from the `hotkey` field if present; if not,
`uid` is used as a fallback.  No score is emitted because the example
files do not provide per‑variation scores.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Optional


def _get_miner_id(resp: Dict[str, Any]) -> Optional[str]:
    """Extract a miner identifier from a response object.

    Tries the `hotkey` field first, then falls back to `uid`.
    Returns None if neither is present.
    """
    hotkey = resp.get("hotkey")
    if hotkey:
        return str(hotkey)
    uid = resp.get("uid")
    if uid is not None:
        return str(uid)
    return None


def parse(obj: Any) -> Iterator[Dict[str, Any]]:
    """Parse a generic responses JSON object and yield canonical records.

    Args:
        obj: A Python object loaded from JSON (usually a dict).
    Yields:
        dicts with the keys `seed`, `variation`, `miner_ext_id`, `score`,
        and `raw`.
    """
    if not isinstance(obj, dict):
        return
    responses = obj.get("responses")
    if not isinstance(responses, dict):
        return
    for resp in responses.values():
        if not isinstance(resp, dict):
            continue
        miner_id = _get_miner_id(resp)
        variations_map = resp.get("variations", {})
        if not isinstance(variations_map, dict):
            continue
        for seed, variations in variations_map.items():
            if not isinstance(variations, (list, tuple)):
                continue
            for variation in variations:
                if not variation:
                    continue
                # Build the canonical record.  We don't include the raw
                # payload by default because it can be large; callers may
                # choose to store resp or subset of it as raw_payload if
                # needed.
                yield {
                    "seed": seed,
                    "variation": variation,
                    "miner_ext_id": miner_id,
                    "score": None,
                    "raw": None,
                }