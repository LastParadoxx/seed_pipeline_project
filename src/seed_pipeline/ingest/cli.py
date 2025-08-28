"""Command line interface for the ingestion pipeline.

This module uses click to expose the batch ingestion function as a
command.  Run `python -m seed_pipeline.ingest.cli ingest --help` for
usage information.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click

from .batch import ingest_batch
from ..adapters.registry import get_adapter_names
from ..ingest.metrics import Metrics


@click.group()
def cli() -> None:
    """Seed pipeline management commands."""
    pass


@cli.command()
@click.option("--batch-name", required=True, help="Name of this ingest batch")
@click.option(
    "--adapter",
    required=True,
    type=click.Choice(get_adapter_names()),
    help="Name of the adapter to use",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Path to a directory containing JSON files to ingest",
)
@click.option("--dry-run", is_flag=True, help="Validate files without modifying the database")
@click.option(
    "--no-resume",
    is_flag=True,
    help="Reprocess all files even if their checksum exists in the batch",
)
@click.option(
    "--workers",
    default=1,
    show_default=True,
    help="Number of worker threads (reserved for future use)",
)
def ingest(batch_name: str, adapter: str, path: Path, dry_run: bool, no_resume: bool, workers: int) -> None:
    """Ingest all JSON files in a directory into the database."""
    files = [p for p in path.iterdir() if p.suffix.lower() == ".json"]
    if not files:
        click.echo(f"No JSON files found in {path}")
        sys.exit(1)
    resume = not no_resume
    metrics: Metrics = ingest_batch(
        batch_name=batch_name,
        files=files,
        adapter_name=adapter,
        dry_run=dry_run,
        resume=resume,
        workers=workers,
    )
    click.echo(metrics.summary())


if __name__ == "__main__":
    cli()