"""Valid and invalid examples for each catalogue schema (F02)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from slf.catalog import export_json_schemas
from slf.schemas import (
    EXPORTED_SCHEMAS,
    Dataset,
    GeoCodeRow,
    GeographySchemes,
    GeoRelationRow,
    Indicator,
    Observation,
    OverrideRow,
    Source,
    VectorSpace,
)

RIGHTS_UNCLEAR = {"status": "unclear", "last_reviewed": "2026-11-07"}

SOURCE = {
    "id": "dcs",
    "name": "Department of Census and Statistics",
    "publisher_type": "government",
    "homepage": "https://www.statistics.gov.lk",
    "access_classes": ["pdf"],
    "rights": RIGHTS_UNCLEAR,
}
SPATIAL = {"support": "area", "scheme": "admin", "level": "gn", "crs_source": "not_applicable"}
DATASET = {"id": "census-2024", "source": "dcs", "title": "Census", "spatial": SPATIAL}
INDICATOR = {
    "id": "share_x",
    "name": "Share X",
    "measure_type": "share",
    "unit": "percent",
    "numerator": "x",
    "denominator": "total",
    "aggregation": "recompute_from_components",
    "definition": "x / total",
}
SCHEMES = {
    "schemes": [
        {
            "id": "admin",
            "name": "Admin",
            "stage": "0",
            "levels": [{"level": 0, "id": "country", "name": "Country"}],
        }
    ]
}
CODE = {
    "geography_id": "LK11",
    "vintage": "cod-ab-v03",
    "code_system": "dcs",
    "external_code": "11",
    "match_method": "exact_code",
    "confidence": 1,
}
RELATION = {
    "geography_id": "LK1",
    "related_id": "LK11",
    "relation": "parent",
    "vintage": "cod-ab-v03",
    "method": "attribute",
    "source": "cod-ab-lka",
}
OVERRIDE = {
    "override_id": "ov-1",
    "dataset_id": "census-2024",
    "target": "claim-1",
    "field": "value",
    "reason": "typo in PDF table",
    "evidence": "Final report p.47",
    "reviewer": "lead",
    "date": "2026-11-07",
}
SPACE = {
    "id": "geo",
    "version": "0.1",
    "title": "Geo",
    "entity_types": ["place"],
    "metric": "euclidean",
    "inputs": [{"id": "label_point", "kind": "geometry"}],
    "method_notes": "unit vectors",
}
OBS = {
    "claim_id": "c1",
    "indicator_id": "population_total",
    "geography_vintage": "2024",
    "period": "2024",
    "time_start": "2024-01-01",
    "time_end": "2024-12-31",
    "time_support": "snapshot",
    "support_type": "area_total",
    "footprint_ref": "LK11",
    "value": 10.0,
    "value_status": "normal",
    "data_nature": "census_count",
    "verification": "machine_extracted",
    "dataset_id": "census-2024",
    "snapshot_sha256": "a" * 64,
    "source_locator": "Table 1",
}

VALID: list[tuple[type[BaseModel], dict[str, Any]]] = [
    (Source, SOURCE),
    (Dataset, DATASET),
    (Indicator, INDICATOR),
    (GeographySchemes, SCHEMES),
    (GeoCodeRow, CODE),
    (GeoRelationRow, RELATION),
    (OverrideRow, OVERRIDE),
    (VectorSpace, SPACE),
    (Observation, OBS),
]


@pytest.mark.parametrize(("model", "data"), VALID, ids=lambda x: getattr(x, "__name__", ""))
def test_valid_examples(model: type[BaseModel], data: dict[str, Any]) -> None:
    model.model_validate(data)


def changed(base: dict[str, Any], **edits: Any) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in edits.items():
        if v is ...:
            out.pop(k, None)
        else:
            out[k] = v
    return out


INVALID: list[tuple[str, type[BaseModel], dict[str, Any], str]] = [
    ("unknown key (typo)", Source, changed(SOURCE, homepge="x"), "Extra inputs"),
    ("bad publisher type", Source, changed(SOURCE, publisher_type="ngo"), "publisher_type"),
    ("bad URL", Source, changed(SOURCE, homepage="statistics.gov.lk"), "homepage"),
    (
        "open rights without evidence",
        Source,
        changed(SOURCE, rights={"status": "open", "last_reviewed": "2026-11-07"}),
        "evidence",
    ),
    ("missing spatial block", Dataset, changed(DATASET, spatial=...), "spatial"),
    (
        "area support without level",
        Dataset,
        changed(DATASET, spatial={"support": "area", "scheme": "admin"}),
        "scheme and level",
    ),
    (
        "grid without resolution",
        Dataset,
        changed(DATASET, spatial={"support": "grid"}),
        "resolution",
    ),
    (
        "CRS not an EPSG code",
        Dataset,
        changed(DATASET, spatial=changed(SPATIAL, crs_source="WGS84")),
        "crs_source",
    ),
    ("bad period", Dataset, changed(DATASET, reference_period="2024-13"), "reference_period"),
    ("share without components", Indicator, changed(INDICATOR, numerator=None), "numerator"),
    (
        "count recomputed",
        Indicator,
        changed(INDICATOR, measure_type="count"),
        "aggregated by 'sum'",
    ),
    ("confidence above 1", GeoCodeRow, changed(CODE, confidence=1.5), "confidence"),
    ("bad match method", GeoCodeRow, changed(CODE, match_method="fuzzy"), "match_method"),
    ("not a Sri Lanka id", GeoCodeRow, changed(CODE, geography_id="IN01"), "geography_id"),
    (
        "composed_of without weight",
        GeoRelationRow,
        changed(RELATION, relation="composed_of"),
        "weight",
    ),
    ("self relation", GeoRelationRow, changed(RELATION, related_id="LK1"), "itself"),
    ("override without evidence", OverrideRow, changed(OVERRIDE, evidence=...), "evidence"),
    (
        "space using ethnicity",
        VectorSpace,
        changed(SPACE, inputs=[{"id": "ethnicity_share", "kind": "indicator"}]),
        "D-015",
    ),
    ("time runs backwards", Observation, changed(OBS, time_end="2023-01-01"), "before time_start"),
    ("null value marked normal", Observation, changed(OBS, value=None), "value is null"),
    ("preferred without reason", Observation, changed(OBS, preferred=True), "preferred_reason"),
    ("bad support_type", Observation, changed(OBS, support_type="area"), "support_type"),
    (
        "uncertain location without radius",
        Observation,
        changed(OBS, support_type="location_uncertain"),
        "uncertainty_m",
    ),
    ("flow with one end", Observation, changed(OBS, origin_ref="LK11"), "destination_ref"),
    ("bad sha256", Observation, changed(OBS, snapshot_sha256="abc"), "snapshot_sha256"),
]


@pytest.mark.parametrize(("name", "model", "data", "expect"), INVALID, ids=[i[0] for i in INVALID])
def test_invalid_examples_fail_for_the_right_reason(
    name: str, model: type[BaseModel], data: dict[str, Any], expect: str
) -> None:
    with pytest.raises(ValidationError) as exc:
        model.model_validate(data)
    assert expect in str(exc.value), f"{name}: expected '{expect}' in:\n{exc.value}"


def test_seasons_and_weeks_are_valid_periods() -> None:
    for period in (
        "2024",
        "2024-Q3",
        "2024-07",
        "2024-W32",
        "2024-07-15",
        "2024/25-maha",
        "2025-yala",
    ):
        Observation.model_validate(changed(OBS, period=period))


def test_committed_json_schemas_are_up_to_date(tmp_path: Path) -> None:
    committed = Path(__file__).resolve().parents[2] / "catalog" / "schemas"
    export_json_schemas(tmp_path)
    for name in EXPORTED_SCHEMAS:
        fname = f"{name}.schema.json"
        fresh = json.loads((tmp_path / fname).read_text())
        assert (committed / fname).exists(), f"run `uv run slf catalog schemas` ({fname} missing)"
        assert json.loads((committed / fname).read_text()) == fresh, (
            f"{fname} is stale: run `uv run slf catalog schemas`"
        )
