"""Batch ingestion logic.

This module contains the core of the ingestion pipeline.  It ties
together the file reading helpers, the adapter registry, the
normalisation functions, validation, and database persistence.  The
entrypoint `ingest_batch` takes a batch name, a list of file paths and
an adapter name and returns a Metrics object summarising the
operation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..adapters import get_adapter
from ..db.engine import SessionLocal
from ..db import models
from ..normalize.text import (
    normalize_seed,
    normalize_variation,
    md5_hex,
)
from ..ingest.file_io import compute_checksum, load_json
from ..ingest.validate import validate_record
from ..ingest.metrics import Metrics


def _get_or_create_batch(session: Session, batch_name: str) -> models.Batch:
    batch = session.execute(
        select(models.Batch).where(models.Batch.batch_name == batch_name)
    ).scalar_one_or_none()
    if batch:
        return batch
    batch = models.Batch(batch_name=batch_name)
    session.add(batch)
    session.flush()
    return batch


def _get_or_create_seed(session: Session, raw_seed: str, norm_seed: str, seed_hash: str, metrics: Metrics) -> models.Seed:
    seed = session.execute(
        select(models.Seed).where(models.Seed.normalized_seed == norm_seed)
    ).scalar_one_or_none()
    if seed is None:
        seed = models.Seed(
            seed_text=raw_seed,
            normalized_seed=norm_seed,
            seed_hash=seed_hash,
        )
        session.add(seed)
        metrics.seeds_new += 1
        session.flush()
    else:
        metrics.seeds_existing += 1
    return seed


def _get_or_create_variation(
    session: Session,
    seed: models.Seed,
    raw_variation: str,
    norm_variation: str,
    variation_hash: str,
    metrics: Metrics,
) -> models.Variation:
    var = session.execute(
        select(models.Variation).where(
            models.Variation.seed_id == seed.id,
            models.Variation.normalized_variation == norm_variation,
        )
    ).scalar_one_or_none()
    if var is None:
        var = models.Variation(
            seed_id=seed.id,
            variation_text=raw_variation,
            normalized_variation=norm_variation,
            variation_hash=variation_hash,
        )
        session.add(var)
        metrics.variations_new += 1
        session.flush()
    else:
        metrics.variations_existing += 1
    return var


def _get_or_create_miner(session: Session, ext_id: str | None) -> Optional[models.Miner]:
    if not ext_id:
        return None
    miner = session.execute(
        select(models.Miner).where(models.Miner.miner_external_id == ext_id)
    ).scalar_one_or_none()
    if miner is None:
        miner = models.Miner(miner_external_id=ext_id)
        session.add(miner)
        session.flush()
    return miner


def ingest_batch(
    batch_name: str,
    files: Iterable[Path],
    adapter_name: str,
    *,
    dry_run: bool = False,
    resume: bool = True,
    workers: int = 1,
) -> Metrics:
    """Ingest a batch of JSON files.

    This function reads each file, parses it using the selected adapter,
    validates and normalises the records, upserts seeds, variations and
    miners, and inserts observations into the database.  It returns a
    `Metrics` object describing what occurred.

    Args:
        batch_name: A human friendly identifier for the batch.  Batches are
            idempotent; if you re‑ingest with the same name files will be
            skipped if their checksum matches a previously processed file.
        files: An iterable of `Path` objects pointing to JSON documents.
        adapter_name: The name of the adapter registered in
            `seed_pipeline.adapters.registry` to use for parsing the files.
        dry_run: If True, the database will not be modified.  Useful for
            validating files without persisting anything.
        resume: If True, files that have already been processed in this
            batch (determined by checksum) will be skipped.
        workers: Reserved for future use when parallelising ingestion.
    Returns:
        A `Metrics` instance summarising the ingestion operation.
    """
    metrics = Metrics()
    adapter = get_adapter(adapter_name)
    # Acquire a session
    with SessionLocal() as session:
        # Ensure batch exists
        batch = _get_or_create_batch(session, batch_name)
        for path in files:
            # Only process plain files
            if not path.is_file():
                continue
            checksum = compute_checksum(path)
            # Check if we've already processed this file in this batch
            if resume:
                existing_file = session.execute(
                    select(models.SourceFile).where(
                        models.SourceFile.batch_id == batch.id,
                        models.SourceFile.file_checksum == checksum,
                    )
                ).scalar_one_or_none()
                if existing_file is not None:
                    metrics.files_skipped += 1
                    continue
            # Load JSON
            try:
                data = load_json(path)
            except Exception:
                metrics.invalid_records += 1
                continue
            # Create SourceFile entry now (but defer commit until after records)
            src_file: Optional[models.SourceFile] = None
            if not dry_run:
                src_file = models.SourceFile(
                    batch_id=batch.id,
                    file_path=str(path),
                    file_checksum=checksum,
                )
                session.add(src_file)
                session.flush()
            # Parse records
            record_count = 0
            for rec in adapter(data):
                valid, reason = validate_record(rec)
                if not valid:
                    metrics.invalid_records += 1
                    continue
                # Normalise
                raw_seed = rec["seed"]
                raw_variation = rec["variation"]
                norm_seed = normalize_seed(raw_seed)
                norm_variation = normalize_variation(raw_variation)
                # Compute hashes
                seed_hash = md5_hex(norm_seed)
                var_hash = md5_hex(norm_variation)
                # Upsert seed and variation
                seed = _get_or_create_seed(session, raw_seed, norm_seed, seed_hash, metrics)
                variation = _get_or_create_variation(
                    session,
                    seed,
                    raw_variation,
                    norm_variation,
                    var_hash,
                    metrics,
                )
                # Upsert miner
                miner = None
                miner_ext_id = rec.get("miner_ext_id")
                if miner_ext_id:
                    miner = _get_or_create_miner(session, miner_ext_id)
                # Insert observation
                if not dry_run:
                    obs = models.Observation(
                        seed_id=seed.id,
                        variation_id=variation.id,
                        miner_id=miner.id if miner else None,
                        batch_id=batch.id,
                        source_file_id=src_file.id if src_file else None,
                        score=rec.get("score"),
                        raw_payload=json.dumps(rec["raw"]) if rec.get("raw") else None,
                    )
                    session.add(obs)
                metrics.observations_inserted += 1
                record_count += 1
            # Update record_count and commit changes
            if not dry_run and src_file:
                src_file.record_count = record_count
            metrics.files_processed += 1
            # Commit per file to avoid huge transactions
            if not dry_run:
                session.commit()
        return metrics