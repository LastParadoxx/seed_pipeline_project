"""Metrics collection for the ingestion pipeline.

The Metrics class collects counts during ingestion.  At the end of
processing it can produce a human‑readable summary.  You can extend
this class as needed to track additional metrics.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Metrics:
    seeds_new: int = 0
    seeds_existing: int = 0
    variations_new: int = 0
    variations_existing: int = 0
    observations_inserted: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    invalid_records: int = 0

    def increment(self, **kwargs: int) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, getattr(self, key) + value)

    def as_dict(self) -> Dict[str, int]:
        return {
            "seeds_new": self.seeds_new,
            "seeds_existing": self.seeds_existing,
            "variations_new": self.variations_new,
            "variations_existing": self.variations_existing,
            "observations_inserted": self.observations_inserted,
            "files_processed": self.files_processed,
            "files_skipped": self.files_skipped,
            "invalid_records": self.invalid_records,
        }

    def summary(self) -> str:
        return (
            f"Processed {self.files_processed} file(s), "
            f"skipped {self.files_skipped}. "
            f"Seeds: {self.seeds_new} new, {self.seeds_existing} existing. "
            f"Variations: {self.variations_new} new, {self.variations_existing} existing. "
            f"Observations: {self.observations_inserted}. "
            f"Invalid records: {self.invalid_records}."
        )