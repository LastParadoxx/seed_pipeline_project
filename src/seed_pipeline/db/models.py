"""ORM models for the seed pipeline.

This module defines the SQLAlchemy ORM models representing the
normalised schema.  Each entity corresponds to one table in the
database.  Relationships are defined to enable convenient traversal
between seeds, variations and observations.

Uniqueness constraints ensure that each seed is stored once, and that
variations are unique per seed.  Observations log each time a
variation is reported by a miner, along with the batch and source file
it originated from.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Seed(Base):
    __tablename__ = "seeds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    seed_text: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    normalized_seed: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    seed_hash: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    # Relationships
    variations: Mapped[list[Variation]] = relationship(
        "Variation", back_populates="seed", cascade="all, delete-orphan"
    )
    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="seed", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Seed(id={self.id!r}, seed_text={self.seed_text!r})"


class Variation(Base):
    __tablename__ = "variations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    seed_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("seeds.id"), nullable=False)
    variation_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_variation: Mapped[str] = mapped_column(Text, nullable=False)
    variation_hash: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    seed: Mapped[Seed] = relationship("Seed", back_populates="variations")
    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="variation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "seed_id", "normalized_variation", name="uq_variation_per_seed"
        ),
        Index("ix_variation_seed", "seed_id"),
        Index("ix_variation_norm", "normalized_variation"),
    )

    def __repr__(self) -> str:
        return f"Variation(id={self.id!r}, text={self.variation_text!r})"


class Miner(Base):
    __tablename__ = "miners"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    miner_external_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="miner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Miner(id={self.id!r}, miner_external_id={self.miner_external_id!r})"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source_system: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingested_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    meta: Mapped[str | None] = mapped_column(Text, nullable=True)

    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="batch", cascade="all, delete-orphan"
    )
    source_files: Mapped[list[SourceFile]] = relationship(
        "SourceFile", back_populates="batch", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Batch(id={self.id!r}, name={self.batch_name!r})"


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("batches.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=True)
    processed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )

    batch: Mapped[Batch] = relationship("Batch", back_populates="source_files")
    observations: Mapped[list[Observation]] = relationship(
        "Observation", back_populates="source_file", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"SourceFile(id={self.id!r}, path={self.file_path!r})"


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    seed_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("seeds.id"), nullable=False)
    variation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("variations.id"), nullable=False
    )
    miner_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("miners.id"), nullable=True
    )
    batch_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("batches.id"), nullable=True
    )
    source_file_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("source_files.id"), nullable=True
    )
    score: Mapped[float | None] = mapped_column(
        nullable=True
    )
    observed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=dt.datetime.utcnow, nullable=False
    )
    raw_payload: Mapped[str | None] = mapped_column(Text, nullable=True)

    seed: Mapped[Seed] = relationship("Seed", back_populates="observations")
    variation: Mapped[Variation] = relationship("Variation", back_populates="observations")
    miner: Mapped[Miner | None] = relationship("Miner", back_populates="observations")
    batch: Mapped[Batch | None] = relationship("Batch", back_populates="observations")
    source_file: Mapped[SourceFile | None] = relationship(
        "SourceFile", back_populates="observations"
    )

    __table_args__ = (
        Index("ix_observation_seed_var", "seed_id", "variation_id"),
        Index("ix_observation_seed_score", "seed_id", "score"),
        Index("ix_observation_batch", "batch_id"),
        Index("ix_observation_miner", "miner_id"),
    )

    def __repr__(self) -> str:
        return f"Observation(id={self.id!r}, seed_id={self.seed_id!r}, variation_id={self.variation_id!r})"