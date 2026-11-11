"""Audit-log and data-quality (DQ) helpers.

Design (functional style): processing functions never write to a global log.
They *return* lists of small event dictionaries next to their results, and the
pipeline collects and persists them.  This keeps every function pure and easy
to test.

Two event kinds:
    * lineage events  -> "what went where"  (audit_log.parquet)
    * dq events       -> "what was changed / flagged / excluded"  (dq_log.parquet)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

logger = logging.getLogger(__name__)

SEVERITIES = ("info", "warning", "error")
MAX_EXAMPLES = 10

DQ_COLUMNS = ["run_id", "source_id", "table", "rule", "severity", "rows_affected", "example_ids", "detail"]
AUDIT_COLUMNS = ["run_id", "timestamp", "stage", "source_id", "input", "output", "rows_in", "rows_out", "detail"]


def dq_event(
    source_id: str,
    table: str,
    rule: str,
    rows_affected: int,
    severity: str = "warning",
    examples: Iterable[Any] | None = None,
    detail: str = "",
) -> dict:
    """Build one data-quality event.  Also emits a log line so the console tells the story."""
    if severity not in SEVERITIES:
        raise ValueError(f"severity must be one of {SEVERITIES}, got {severity!r}")
    example_text = ""
    if examples is not None:
        example_text = "; ".join(str(e) for e in list(examples)[:MAX_EXAMPLES])
    event = {
        "source_id": source_id,
        "table": table,
        "rule": rule,
        "severity": severity,
        "rows_affected": int(rows_affected),
        "example_ids": example_text,
        "detail": detail,
    }
    level = {"info": logging.INFO, "warning": logging.WARNING, "error": logging.ERROR}[severity]
    logger.log(level, "[DQ] %s/%s: %s (%d rows) %s", source_id, table, rule, rows_affected, detail)
    return event


def audit_event(
    stage: str,
    source_id: str,
    input_name: str,
    output_name: str,
    rows_in: int | None = None,
    rows_out: int | None = None,
    detail: str = "",
) -> dict:
    """Build one lineage event (raw file -> staging table -> canonical table -> export)."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": stage,
        "source_id": source_id,
        "input": input_name,
        "output": output_name,
        "rows_in": rows_in,
        "rows_out": rows_out,
        "detail": detail,
    }


def events_to_frame(events: list[dict], columns: list[str], run_id: str) -> pd.DataFrame:
    """Turn event dictionaries into a typed DataFrame (always has all columns, even when empty)."""
    frame = pd.DataFrame(events)
    frame["run_id"] = run_id
    for col in columns:
        if col not in frame.columns:
            frame[col] = pd.NA
    frame = frame[columns].copy()
    for col in ("rows_affected", "rows_in", "rows_out"):
        if col in frame.columns:
            frame[col] = frame[col].astype("Int64")
    return frame


def append_parquet_log(events: list[dict], path: Path, columns: list[str], run_id: str) -> None:
    """Append events to a Parquet log (read-concat-write; logs are small)."""
    if not events:
        return
    new = events_to_frame(events, columns, run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = pd.read_parquet(path)
        new = pd.concat([old, new], ignore_index=True)
    new.to_parquet(path, engine="pyarrow", index=False)


def make_run_id() -> str:
    """Timestamp based run id, e.g. 20261101T145501Z."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
