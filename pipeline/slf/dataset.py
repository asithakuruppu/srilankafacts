"""The five-stage interface every dataset module implements.

snapshot → extract → harmonise → validate → publish (docs/architecture/architecture-overview.md §3).

Observations follow the footprint model (docs/architecture/footprint-model.md): every value has a
where (footprint), a when (time footprint) and a what (indicator), plus value and provenance.
Rows are plain dicts here; the full row schema is slf.schemas.Observation (F02).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from slf.schemas import SUPPORT_TYPES, TIME_SUPPORTS
from slf.snapshot import SnapshotRef
from slf.storage import Storage

Row = dict[str, Any]

# Minimum fields every observation must carry (subset of data-model.md §5).
REQUIRED_OBSERVATION_FIELDS: tuple[str, ...] = (
    "claim_id",
    "indicator_id",
    "footprint_ref",
    "geography_vintage",
    "support_type",
    "period",
    "time_start",
    "time_end",
    "time_support",
    "value",
    "value_status",
    "data_nature",
    "verification",
    "dataset_id",
    "snapshot_sha256",
    "source_locator",
)


@dataclass
class QAReport:
    dataset_id: str
    checked: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_markdown(self) -> str:
        lines = [
            f"# QA report: {self.dataset_id}",
            "",
            f"- Observations checked: {self.checked}",
            f"- Errors: {len(self.errors)}",
            f"- Warnings: {len(self.warnings)}",
        ]
        for title, items in (("Errors", self.errors), ("Warnings", self.warnings)):
            if items:
                lines += ["", f"## {title}", "", *[f"- {i}" for i in items]]
        return "\n".join(lines) + "\n"


def check_observations(dataset_id: str, rows: list[Row]) -> QAReport:
    """Generic checks that apply to every dataset. Datasets add their own on top."""
    report = QAReport(dataset_id=dataset_id, checked=len(rows))
    seen_claims: set[str] = set()
    preferred: dict[tuple[Any, ...], int] = {}
    for i, row in enumerate(rows):
        # A null value is allowed only when value_status says why (not_available, suppressed...).
        optional = {"value"} if row.get("value_status") not in (None, "", "normal") else set()
        missing = [
            f for f in REQUIRED_OBSERVATION_FIELDS if f not in optional and row.get(f) in (None, "")
        ]
        if missing:
            report.errors.append(f"row {i}: missing {', '.join(missing)}")
            continue
        if row["support_type"] not in SUPPORT_TYPES:
            report.errors.append(f"row {i}: unknown support_type {row['support_type']!r}")
        if row["time_support"] not in TIME_SUPPORTS:
            report.errors.append(f"row {i}: unknown time_support {row['time_support']!r}")
        if row["claim_id"] in seen_claims:
            report.errors.append(f"row {i}: duplicate claim_id {row['claim_id']}")
        seen_claims.add(row["claim_id"])
        if row["time_start"] > row["time_end"]:
            report.errors.append(f"row {i}: time_start after time_end")
        box = (row["indicator_id"], row["footprint_ref"], row["period"], str(row.get("breakdown")))
        if row.get("preferred"):
            preferred[box] = preferred.get(box, 0) + 1
            if not row.get("preferred_reason"):
                report.errors.append(f"row {i}: preferred claim without preferred_reason")
    for box, count in preferred.items():
        if count > 1:
            report.errors.append(f"{count} preferred claims for {box}; at most one allowed")
    return report


class Dataset(ABC):
    """Base class for dataset modules."""

    dataset_id: str
    source_id: str

    @abstractmethod
    def snapshot(self, storage: Storage) -> SnapshotRef: ...

    @abstractmethod
    def extract(self, storage: Storage, ref: SnapshotRef) -> list[Row]: ...

    @abstractmethod
    def harmonise(self, rows: list[Row], ref: SnapshotRef) -> list[Row]: ...

    def validate(self, observations: list[Row]) -> QAReport:
        return check_observations(self.dataset_id, observations)

    @abstractmethod
    def publish(self, observations: list[Row], report: QAReport, out_dir: str) -> list[str]: ...
