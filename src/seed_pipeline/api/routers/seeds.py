"""Seed‑related API endpoints."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...db import models
from ...normalize.text import normalize_seed, normalize_variation
from ..deps import get_db


router = APIRouter(prefix="/seeds", tags=["seeds"])


class SeedExistsRequest(BaseModel):
    seeds: List[str] = Field(..., min_items=1, description="List of seed names")


class SeedExistsResponseItem(BaseModel):
    seed: str
    exists: bool
    variation_count: int


@router.post("/exists", response_model=List[SeedExistsResponseItem])
def seeds_exists(payload: SeedExistsRequest, db: Session = Depends(get_db)) -> List[SeedExistsResponseItem]:
    """Return existence and variation counts for the given seeds."""
    results: List[SeedExistsResponseItem] = []
    # Normalise seeds first to reduce queries
    norm_map = {seed: normalize_seed(seed) for seed in payload.seeds}
    # Fetch all seeds in one query
    stmt = (
        select(models.Seed.id, models.Seed.seed_text, models.Seed.normalized_seed)
        .where(models.Seed.normalized_seed.in_(norm_map.values()))
    )
    found = {row.normalized_seed: row for row in db.execute(stmt).all()}
    # Precompute variation counts for found seeds
    if found:
        seed_ids = [row.id for row in found.values()]
        count_stmt = (
            select(models.Variation.seed_id, func.count(models.Variation.id))
            .where(models.Variation.seed_id.in_(seed_ids))
            .group_by(models.Variation.seed_id)
        )
        counts = {sid: cnt for sid, cnt in db.execute(count_stmt).all()}
    else:
        counts = {}
    # Build response preserving order
    for raw_seed, norm_seed in norm_map.items():
        row = found.get(norm_seed)
        if row:
            results.append(
                SeedExistsResponseItem(
                    seed=raw_seed,
                    exists=True,
                    variation_count=counts.get(row.id, 0),
                )
            )
        else:
            results.append(
                SeedExistsResponseItem(seed=raw_seed, exists=False, variation_count=0)
            )
    return results


class SeedDiffRequest(BaseModel):
    seed: str = Field(..., description="The seed name to check variations for")
    variations: List[str] = Field(..., min_items=1, description="Candidate variations to classify")


class SeedDiffResponse(BaseModel):
    existing: List[str]
    new: List[str]


@router.post("/diff", response_model=SeedDiffResponse)
def seed_diff(payload: SeedDiffRequest, db: Session = Depends(get_db)) -> SeedDiffResponse:
    """Given a seed and list of variations, return which are new vs existing."""
    seed_norm = normalize_seed(payload.seed)
    seed_row = db.execute(
        select(models.Seed.id).where(models.Seed.normalized_seed == seed_norm)
    ).scalar_one_or_none()
    # If seed doesn't exist then all variations are new
    if seed_row is None:
        return SeedDiffResponse(existing=[], new=payload.variations)
    seed_id = seed_row
    # Build normalised variation map
    norm_map = {var: normalize_variation(var) for var in payload.variations}
    # Fetch existing variations for this seed
    stmt = (
        select(models.Variation.normalized_variation)
        .where(
            models.Variation.seed_id == seed_id,
            models.Variation.normalized_variation.in_(norm_map.values()),
        )
    )
    existing_norms = {row[0] for row in db.execute(stmt).all()}
    existing: List[str] = []
    new: List[str] = []
    for raw_var, norm_var in norm_map.items():
        if norm_var in existing_norms:
            existing.append(raw_var)
        else:
            new.append(raw_var)
    return SeedDiffResponse(existing=existing, new=new)