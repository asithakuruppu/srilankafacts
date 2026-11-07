"""A trivial, synthetic dataset that shows the five-stage interface.

The data is invented for testing (unit codes TEST-001 to TEST-003). It is never published as
real data. Real datasets start with prompts G01 (geography) and D01 (census).
"""

from __future__ import annotations

import csv
import io
import json
from importlib import resources
from pathlib import Path

from slf.dataset import Dataset, QAReport, Row
from slf.snapshot import SnapshotRef, snapshot_bytes
from slf.storage import Storage


class ExampleDataset(Dataset):
    dataset_id = "example"
    source_id = "synthetic"

    def snapshot(self, storage: Storage) -> SnapshotRef:
        content = (resources.files("slf.datasets") / "fixtures" / "example_source.csv").read_bytes()
        return snapshot_bytes(
            storage,
            source=self.source_id,
            dataset=self.dataset_id,
            filename="example_source.csv",
            content=content,
            url=None,
            licence_note="synthetic test data",
        )

    def extract(self, storage: Storage, ref: SnapshotRef) -> list[Row]:
        text = storage.get(ref.key).decode("utf-8")
        return list(csv.DictReader(io.StringIO(text)))

    def harmonise(self, rows: list[Row], ref: SnapshotRef) -> list[Row]:
        observations: list[Row] = []
        for line, row in enumerate(rows, start=2):  # line 1 is the header
            for indicator, column in (
                ("households_total", "households"),
                ("households_cooking_firewood", "households_firewood"),
            ):
                raw = (row.get(column) or "").strip()
                observations.append(
                    {
                        "claim_id": f"{self.dataset_id}:{row['unit_code']}:{indicator}",
                        "indicator_id": indicator,
                        "footprint_ref": row["unit_code"],
                        "geography_vintage": "test",
                        "support_type": "area_total",
                        "period": "2024",
                        "time_start": "2024-01-01",
                        "time_end": "2024-01-01",
                        "time_support": "snapshot",
                        "breakdown": None,
                        "value": int(raw) if raw else None,
                        # Missing values are kept and labelled, never dropped (AGENTS.md rule 6).
                        "value_status": "normal" if raw else "not_available",
                        "data_nature": "census_count",
                        "verification": "machine_extracted",
                        "dataset_id": self.dataset_id,
                        "snapshot_sha256": ref.sha256,
                        "source_locator": f"example_source.csv line {line}, column {column}",
                        "preferred": False,
                        "preferred_reason": None,
                    }
                )
        return observations

    def validate(self, observations: list[Row]) -> QAReport:
        report = super().validate(observations)
        for obs in observations:
            value = obs.get("value")
            if isinstance(value, int) and value < 0:
                report.errors.append(f"{obs['claim_id']}: negative count {value}")
            if obs.get("value_status") == "not_available":
                report.warnings.append(f"{obs['claim_id']}: value not available in source")
        return report

    def publish(self, observations: list[Row], report: QAReport, out_dir: str) -> list[str]:
        if not report.ok:
            raise RuntimeError(f"refusing to publish {self.dataset_id}: QA report has errors")
        out = Path(out_dir) / self.dataset_id
        out.mkdir(parents=True, exist_ok=True)
        obs_path = out / "observations.json"
        qa_path = out / "qa.md"
        obs_path.write_text(json.dumps(observations, indent=2) + "\n")
        qa_path.write_text(report.to_markdown())
        return [str(obs_path), str(qa_path)]
