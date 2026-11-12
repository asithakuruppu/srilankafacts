"""Build an immutable, deterministic release (prompt D04).

A release is assembled only from datasets that pass validation. Public releases additionally
require recorded rights that allow publication. A private preview may include rights-unclear
datasets, but every manifest, API response and page then says `publishable: false`; a preview is
never presented as a public release.

The build has no wall-clock timestamp: the version is the release identity, and two runs from the
same inputs produce the same bytes and checksums.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import pyogrio

from slf import corrections, profile_release, sources
from slf.catalog import (
    Catalog,
    CatalogReport,
    decision_log_path,
    effective_rights,
    load_catalog,
    load_decisions,
)
from slf.datasets import REGISTRY
from slf.enrich import build_spatial_context
from slf.storage import LocalStorage

LEVEL_NAMES = {
    0: "country",
    1: "province",
    2: "district",
    3: "ds",
    4: "gn",
}

SIMPLIFY_TOLERANCE = {
    0: 0.001,
    1: 0.01,
    2: 0.005,
    3: 0.002,
    4: 0.001,
}


def _release_month(version: str) -> str:
    match = re.match(r"v(\d{4})\.(\d{2})\.", version)
    if not match:
        return "1970-01-01T00:00:00.000Z"
    return f"{match.group(1)}-{match.group(2)}-01T00:00:00.000Z"


@dataclass
class ReleaseResult:
    version: str
    path: Path
    preview: bool
    publishable: bool
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _json_safe(value: Any) -> Any:
    """Replace values JSON cannot represent (NaN, NaT, numpy scalars) with null/native.

    Python's json module writes bare ``NaN`` by default, which is not valid JSON for
    browsers or most parsers. Every release file must be strict JSON.
    """
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None:
        return None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, bool, int)):
        return value
    if value is pd.NA or value is pd.NaT:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return _json_safe(value.item())
        except (TypeError, ValueError):
            pass
    return value


def _json_bytes(obj: Any) -> bytes:
    return (
        json.dumps(
            _json_safe(obj),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as fh:
        fh.write(data)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    columns = [str(column) for column in frame.columns]
    return [
        dict(zip(columns, row, strict=False)) for row in frame.itertuples(index=False, name=None)
    ]


def _sorted_records(frame: pd.DataFrame, column: str) -> list[dict[str, Any]]:
    return sorted(_records(frame), key=lambda row: str(row[column]))


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _level_of(level: int, status: str = "current") -> str:
    if level == 3 and status == "provisional":
        return "ds-provisional"
    return LEVEL_NAMES[level]


def public_release_refusals(
    catalog: Catalog, dataset_ids: list[str], decisions: dict[str, str] | None
) -> list[str]:
    """Why a public release of these datasets must be refused (empty list: allowed).

    Open or conditionally permitted rights allow publication. Unclear rights allow it only with a
    `publication` decision that is Accepted in the decision log (D-030); restricted never does.
    """
    refusals: list[str] = []
    for dataset_id in dataset_ids:
        ds = catalog.datasets.get(dataset_id)
        rights = effective_rights(catalog, ds) if ds else None
        if ds is None or rights is None:
            refusals.append(f"{dataset_id}: rights missing; refusing a public release")
            continue
        if rights.status in ("open", "permitted_with_conditions"):
            continue
        pub = ds.publication
        if rights.status == "unclear" and pub is not None:
            status = (decisions or {}).get(pub.decision)
            if status == "Accepted":
                continue
            refusals.append(
                f"{dataset_id}: rights unclear and publication decision {pub.decision} is "
                f"{status or 'not in the decision log'}; refusing a public release"
            )
            continue
        refusals.append(
            f"{dataset_id}: rights {rights.status}; refusing a public release "
            "(use --preview for a private, non-publishable build)"
        )
    return refusals


def release_use(datasets: list[dict[str, Any]]) -> str:
    """`non_commercial` if any dataset is published only for non-commercial use."""
    return "non_commercial" if any(d["use"] == "non_commercial" for d in datasets) else "any"


def release_notices(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "dataset_id": d["dataset_id"],
            "use": d["use"],
            "attribution": d["attribution"],
            "notice": d["notice"],
            "decision": d["publication_decision"],
        }
        for d in datasets
        if d["notice"]
    ]


def _dataset_rights(catalog: Catalog, dataset_id: str) -> dict[str, Any]:
    ds = catalog.datasets[dataset_id]
    rights = effective_rights(catalog, ds)
    source = catalog.sources.get(ds.source)
    pub = ds.publication
    commercial = rights.commercial_reuse if rights else "unknown"
    return {
        "dataset_id": ds.id,
        "title": ds.title,
        "source_id": ds.source,
        "source_name": source.name if source else None,
        "source_homepage": str(source.homepage) if source and source.homepage else None,
        "rights_status": rights.status if rights else "unclear",
        "licence": rights.licence if rights else None,
        "commercial_reuse": commercial,
        "use": pub.use if pub else ("any" if commercial == "yes" else "non_commercial"),
        "attribution": (rights.attribution if rights else None)
        or (pub.attribution if pub else None),
        "notice": pub.notice if pub else None,
        "publication_decision": pub.decision if pub else None,
        "takedown_days": pub.takedown_days if pub else None,
        "rights_evidence": rights.evidence if rights else [],
    }


def _notice_markdown(notices: list[dict[str, Any]]) -> str:
    if not notices:
        return ""
    lines = ["# Notice", ""]
    for n in notices:
        lines += [
            f"## {n['dataset_id']}",
            "",
            f"- Use: {n['use'].replace('_', '-')} only",
            f"- Attribution: {n['attribution']}",
            f"- Notice: {n['notice']}",
            f"- Basis: Sri Lanka Facts decision {n['decision']}. This is not a licence from "
            "the source.",
            "",
        ]
    return "\n".join(lines)


def _citation(version: str, preview: bool) -> str:
    kind = "private preview" if preview else "release"
    return f"Sri Lanka Facts. Census Atlas 2024 {kind} ({version})."


def _load_observations(
    dataset_ids: list[str], catalog: Catalog, storage: LocalStorage
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[str], list[str]]:
    frames: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    for dataset_id in dataset_ids:
        if dataset_id not in REGISTRY:
            errors.append(f"{dataset_id}: no pipeline module registered")
            continue
        if dataset_id not in catalog.datasets:
            errors.append(f"{dataset_id}: not in the catalogue")
            continue
        dataset = REGISTRY[dataset_id]()
        ref = dataset.snapshot(storage)
        observations = dataset.harmonise(dataset.extract(storage, ref), ref)
        report = dataset.validate(observations)
        reports.append(
            {
                "dataset_id": dataset_id,
                "checked": report.checked,
                "errors": len(report.errors),
                "warnings": report.warnings,
            }
        )
        warnings.extend(f"{dataset_id}: {w}" for w in report.warnings)
        if not report.ok:
            errors.extend(f"{dataset_id}: {e}" for e in report.errors)
            continue
        frame = pd.DataFrame(observations)
        frame["release"] = None
        frames.append(frame)
    if not frames:
        return pd.DataFrame(), reports, warnings, errors
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(
        ["geography_id", "indicator_id", "period", "claim_id"], kind="stable"
    ).reset_index(drop=True)
    return combined, reports, warnings, errors


def _geographies(spine_dir: Path) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    geographies = pd.read_parquet(spine_dir / "geographies.parquet")
    versions = gpd.GeoDataFrame(gpd.read_parquet(spine_dir / "geography_versions.geoparquet"))
    return geographies, versions


def _boundary_frames(
    versions: gpd.GeoDataFrame, geographies: pd.DataFrame
) -> dict[int, gpd.GeoDataFrame]:
    geo_records = _records(geographies)
    parent_by_id = {
        str(row["geography_id"]): (
            None
            if row["parent_id"] is None or bool(pd.isna(row["parent_id"]))
            else str(row["parent_id"])
        )
        for row in geo_records
    }
    name_by_id = {str(row["geography_id"]): row for row in geo_records}
    frames: dict[int, gpd.GeoDataFrame] = {}
    for level in sorted({int(value) for value in versions["level"].tolist()}):
        frame = versions[versions["level"] == level].copy()
        tolerance = SIMPLIFY_TOLERANCE.get(level, 0.0)
        if tolerance:
            frame["geometry"] = frame.geometry.simplify(tolerance, preserve_topology=True)
        frame["name_en"] = [
            name_by_id.get(str(geo), {}).get("name_en") for geo in frame["geography_id"]
        ]
        frame["name_si"] = [
            name_by_id.get(str(geo), {}).get("name_si") for geo in frame["geography_id"]
        ]
        frame["name_ta"] = [
            name_by_id.get(str(geo), {}).get("name_ta") for geo in frame["geography_id"]
        ]
        frame["level_name"] = [
            _level_of(level, "current" if pd.isna(status) else str(status))
            for status in frame["status"]
        ]
        frame["parent_id"] = [parent_by_id.get(str(geo)) for geo in frame["geography_id"]]
        frame["area_km2"] = [_float_or_none(value) for value in frame["area_km2"]]
        columns = [
            "geography_id",
            "name_en",
            "name_si",
            "name_ta",
            "level",
            "level_name",
            "parent_id",
            "status",
            "area_km2",
            "geometry",
        ]
        frames[level] = frame.iloc[
            sorted(range(len(frame)), key=lambda i: str(frame.iloc[i]["geography_id"]))
        ][columns]
    return frames


def _boundary_files(frames: dict[int, gpd.GeoDataFrame], out: Path) -> list[str]:
    written: list[str] = []
    for level, frame in sorted(frames.items()):
        geojson = json.loads(
            frame.to_json(  # pyright: ignore[reportCallIssue]
                to_wgs84=False, sort_keys=True
            )
        )
        data = _json_bytes(geojson)
        rel = f"boundaries/admin{level}.geojson"
        _write(out / rel, data)
        written.append(rel)
    return written


def _geopackage(frames: dict[int, gpd.GeoDataFrame], out: Path, version: str) -> str:
    """Write all levels as layers in one GeoPackage.

    GeoPackage records a `last_change` timestamp in its metadata. To keep releases
    bit-for-bit reproducible we set it from the release version (first day of the release
    month), not from the wall clock; it is not a build timestamp.
    """
    rel = "geographies.gpkg"
    path = out / rel
    pyogrio.set_gdal_config_options({"OGR_CURRENT_DATE": _release_month(version)})
    try:
        for index, (level, frame) in enumerate(sorted(frames.items())):
            frame.to_file(
                path,
                layer=f"admin{level}",
                driver="GPKG",
                engine="pyogrio",
                append=index > 0,
            )
    finally:
        pyogrio.set_gdal_config_options({"OGR_CURRENT_DATE": None})
    return rel


def _clean_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for record in records:
        clean: dict[str, Any] = {}
        for key, value in record.items():
            if isinstance(value, (list, dict)):
                clean[key] = value
            elif value is None or pd.isna(value):
                clean[key] = None
            elif hasattr(value, "item"):
                clean[key] = value.item()
            else:
                clean[key] = value
        cleaned.append(clean)
    return cleaned


def _float_or_none(value: Any) -> float | None:
    if value is None or bool(pd.isna(value)):
        return None
    return float(value)


def _place_payload(
    geography: dict[str, Any],
    values: list[dict[str, Any]],
    *,
    version: str,
    preview: bool,
    datasets: list[dict[str, Any]],
    citation: str,
    profile: dict[str, Any] | None = None,
    comparisons: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    level = int(geography["level"])
    status = str(geography["status"])
    parent = geography["parent_id"]
    return {
        "release": version,
        "publishable": not preview,
        "use": release_use(datasets),
        "notices": release_notices(datasets),
        "citation": citation,
        "geography": {
            "geography_id": geography["geography_id"],
            "name_en": geography["name_en"],
            "name_si": geography["name_si"],
            "name_ta": geography["name_ta"],
            "level": level,
            "level_name": _level_of(level, status),
            "parent_id": None if parent is None or pd.isna(parent) else str(parent),
            "status": status,
        },
        "values": values,
        **({"profile": profile} if profile is not None else {}),
        **({"source_comparisons": comparisons} if comparisons else {}),
        "datasets": datasets,
    }


def _write_api(
    out: Path,
    *,
    version: str,
    preview: bool,
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    catalog: Catalog,
    datasets: list[dict[str, Any]],
    citation: str,
    profiles: dict[str, dict[str, Any]] | None = None,
    comparisons: dict[str, list[dict[str, Any]]] | None = None,
) -> list[str]:
    written: list[str] = []
    meta = geographies.set_index("geography_id")
    level_by_id = meta["level"].to_dict()
    status_by_id = meta["status"].to_dict()
    observations = observations.copy()
    observations["level"] = [
        level_by_id.get(str(geo)) for geo in observations["geography_id"].tolist()
    ]
    observations["level_name"] = [
        _level_of(int(level), str(status_by_id.get(str(geo), "current")))
        for geo, level in zip(
            observations["geography_id"].tolist(),
            observations["level"].tolist(),
            strict=False,
        )
    ]

    value_columns = [
        "indicator_id",
        "value",
        "value_status",
        "unit",
        "period",
        "time_start",
        "time_end",
        "claim_id",
        "dataset_id",
        "snapshot_sha256",
        "source_locator",
        "verification",
        "support_type",
        "information_footprint_ref",
    ]
    values_by_geo: dict[str, list[dict[str, Any]]] = {}
    for record in _clean_records(_records(observations)):
        values_by_geo.setdefault(str(record["geography_id"]), []).append(
            {column: record[column] for column in value_columns}
        )

    base = {
        "release": version,
        "publishable": not preview,
        "use": release_use(datasets),
        "notices": release_notices(datasets),
        "citation": citation,
    }

    places_dir = out / "api" / "v1" / "places"
    for geography in _sorted_records(geographies, "geography_id"):
        geo_id = geography["geography_id"]
        payload = _place_payload(
            geography,
            values_by_geo.get(str(geo_id), []),
            version=version,
            preview=preview,
            datasets=datasets,
            citation=citation,
            profile=(profiles or {}).get(str(geo_id)),
            comparisons=(comparisons or {}).get(str(geo_id)),
        )
        rel = f"api/v1/places/{geo_id}.json"
        _write(places_dir / f"{geo_id}.json", _json_bytes(payload))
        written.append(rel)

    indicators = []
    for indicator_id, indicator in sorted(catalog.indicators.items()):
        rows = observations[observations["indicator_id"] == indicator_id]
        levels = sorted({str(value) for value in rows["level_name"].tolist() if not pd.isna(value)})
        periods = sorted({str(value) for value in rows["period"].tolist() if not pd.isna(value)})
        entry = {
            "id": indicator.id,
            "name": indicator.name,
            "short_name": indicator.short_name,
            "unit": indicator.unit,
            "measure_type": indicator.measure_type,
            "definition": indicator.definition,
            "decimals": indicator.decimals,
            "higher_is": indicator.higher_is,
            "levels": levels,
            "period": periods,
            "value_count": sum(1 for value in rows["value"].tolist() if not pd.isna(value)),
        }
        indicators.append(entry)
        payload = {**base, "indicator": entry}
        _write(out / "api" / "v1" / "indicators" / f"{indicator_id}.json", _json_bytes(payload))
        written.append(f"api/v1/indicators/{indicator_id}.json")
        for level_name in levels:
            level_rows = pd.DataFrame(rows[rows["level_name"] == level_name])
            values = [
                {
                    "geography_id": row["geography_id"],
                    "value": _float_or_none(row["value"]),
                    "value_status": row["value_status"],
                    "unit": row["unit"],
                    "period": row["period"],
                }
                for row in _sorted_records(level_rows, "geography_id")
            ]
            level_payload = {
                **base,
                "indicator_id": indicator_id,
                "level": level_name,
                "values": values,
            }
            rel = f"api/v1/indicators/{indicator_id}/{level_name}.json"
            _write(out / rel, _json_bytes(level_payload))
            written.append(rel)

    _write(out / "api" / "v1" / "indicators.json", _json_bytes({**base, "indicators": indicators}))
    written.append("api/v1/indicators.json")

    geography_index = [
        {
            "geography_id": row["geography_id"],
            "name_en": row["name_en"],
            "name_si": row["name_si"],
            "name_ta": row["name_ta"],
            "level": int(row["level"]),
            "level_name": _level_of(int(row["level"]), str(row["status"])),
            "parent_id": None if pd.isna(row["parent_id"]) else row["parent_id"],
            "status": row["status"],
        }
        for row in _sorted_records(geographies, "geography_id")
    ]
    _write(
        out / "api" / "v1" / "geographies" / "admin.json",
        _json_bytes({**base, "scheme": "admin", "geographies": geography_index}),
    )
    written.append("api/v1/geographies/admin.json")

    release_info = {
        **base,
        "version": version,
        "status": "preview" if preview else "public",
        "datasets": datasets,
        "observation_count": len(observations),
        "geography_count": len(geographies),
    }
    _write(out / "api" / "v1" / "releases" / "latest.json", _json_bytes(release_info))
    written.append("api/v1/releases/latest.json")
    _write(out / "api" / "v1" / "releases" / f"{version}.json", _json_bytes(release_info))
    written.append(f"api/v1/releases/{version}.json")

    openapi = {
        "openapi": "3.1.0",
        "info": {
            "title": "Sri Lanka Facts static API",
            "version": version,
            "description": "Generated files; GET only. Each response carries the release, "
            "citation and provenance for every value.",
        },
        "paths": {
            "/api/v1/places/{geoId}.json": {
                "get": {
                    "parameters": [
                        {
                            "name": "geoId",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Place profile"}},
                }
            },
            "/api/v1/indicators.json": {
                "get": {"responses": {"200": {"description": "Indicator index"}}}
            },
            "/api/v1/indicators/{id}.json": {
                "get": {"responses": {"200": {"description": "Indicator metadata"}}}
            },
            "/api/v1/indicators/{id}/{level}.json": {
                "get": {"responses": {"200": {"description": "Values for one level"}}}
            },
            "/api/v1/geographies/admin.json": {
                "get": {"responses": {"200": {"description": "Admin geography index"}}}
            },
            "/api/v1/releases/latest.json": {
                "get": {"responses": {"200": {"description": "Current release pointer"}}}
            },
        },
    }
    _write(out / "api" / "openapi.json", _json_bytes(openapi))
    written.append("api/openapi.json")
    return written


def _changelog(
    observations: pd.DataFrame, previous: Path | None, version: str
) -> tuple[str, dict[str, Any]]:
    if previous is None:
        return (
            f"# Changelog {version}\n\nFirst release in this build directory; no previous "
            "release was supplied for comparison.\n",
            {"previous": None, "new": len(observations), "changed": 0, "removed": 0},
        )
    prev = pd.read_parquet(previous)
    current_by_id = observations.set_index("claim_id")
    prev_by_id = prev.set_index("claim_id")
    new_ids = sorted(set(current_by_id.index) - set(prev_by_id.index))
    removed_ids = sorted(set(prev_by_id.index) - set(current_by_id.index))
    common = sorted(set(current_by_id.index) & set(prev_by_id.index))
    changed = []
    for claim_id in common:
        a = current_by_id.loc[claim_id, "value"]
        b = prev_by_id.loc[claim_id, "value"]
        if pd.isna(a) and pd.isna(b):
            continue
        if a != b:
            changed.append(claim_id)
    lines = [
        f"# Changelog {version}",
        "",
        f"- Previous release: `{previous}`",
        f"- New claims: {len(new_ids)}",
        f"- Changed values: {len(changed)}",
        f"- Removed claims: {len(removed_ids)}",
        "",
    ]
    for title, ids in (
        ("New claims", new_ids),
        ("Changed values", changed),
        ("Removed claims", removed_ids),
    ):
        if ids:
            lines += [f"## {title}", "", *[f"- `{i}`" for i in ids[:200]]]
            if len(ids) > 200:
                lines.append(f"- … and {len(ids) - 200} more (see changes.json)")
            lines.append("")
    payload = {
        "previous": str(previous),
        "new": len(new_ids),
        "changed": len(changed),
        "removed": len(removed_ids),
        "new_claims": new_ids,
        "changed_claims": changed,
        "removed_claims": removed_ids,
    }
    return "\n".join(lines), payload


def _datapackage(
    out: Path,
    version: str,
    preview: bool,
    datasets: list[dict[str, Any]],
    files: list[str],
) -> dict[str, Any]:
    resources = []
    for rel in files:
        path = out / rel
        if rel == "datapackage.json" or not path.is_file():
            continue
        resources.append(
            {
                "name": rel.replace("/", "-").replace(".", "-"),
                "path": rel,
                "bytes": path.stat().st_size,
                "hash": f"sha256:{_file_sha256(path)}",
            }
        )
    licences = sorted({d["licence"] for d in datasets if d.get("licence")})
    return {
        "name": "sri-lanka-facts-census-atlas-2024",
        "title": "Sri Lanka Facts: Census Atlas 2024",
        "version": version,
        "publishable": not preview,
        "access": "private_preview" if preview else "public",
        "use": release_use(datasets),
        "notices": release_notices(datasets),
        "licenses": [{"name": licence} for licence in licences] or [{"name": "rights unclear"}],
        "sources": [
            {
                "title": d["source_name"] or d["source_id"],
                "path": d["source_homepage"],
                "dataset": d["dataset_id"],
            }
            for d in datasets
        ],
        "resources": resources,
    }


@dataclass
class _Compared:
    table: pd.DataFrame
    by_place: dict[str, list[dict[str, Any]]]
    files: list[str]
    warnings: list[str]


def _source_comparisons(
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    catalog_root: Path,
    data_dir: Path,
    out: Path,
) -> _Compared:
    """D-019 comparisons; skipped with a warning when an input is missing."""
    report_csv = catalog_root / "references" / "dcs-cph2024-final-report-tables.csv"
    census = observations.loc[observations["dataset_id"] == "census-2024-gnd-tables"]
    cell = census["source_locator"].astype(str).str.startswith("GN_population.xlsx, sheet")
    pop_sha = census.loc[cell, "snapshot_sha256"]
    if census.empty or pop_sha.empty or not report_csv.exists():
        return _Compared(pd.DataFrame(), {}, [], ["source comparisons skipped: inputs missing"])
    raw = data_dir / "raw" / "dcs" / "census-2024-gnd-tables"
    pop_xlsx = next(
        (p for p in sorted(raw.rglob("GN_population.xlsx")) if _file_sha256(p) == pop_sha.iloc[0]),
        None,
    )
    if pop_xlsx is None:
        return _Compared(
            pd.DataFrame(), {}, [], ["source comparisons skipped: GN workbook snapshot not found"]
        )
    compared = sources.compare(observations, geographies, pop_xlsx, report_csv)
    (out / "stats").mkdir(parents=True, exist_ok=True)
    compared.table.to_parquet(out / "stats" / "source_comparisons.parquet", index=False)
    _write(out / "qa" / "source-comparisons.md", sources.qa_markdown(compared).encode("utf-8"))
    return _Compared(
        compared.table,
        compared.by_place,
        ["stats/source_comparisons.parquet", "qa/source-comparisons.md"],
        compared.warnings,
    )


def build_release(
    *,
    version: str,
    dataset_ids: list[str],
    catalog_root: Path,
    data_dir: Path,
    spine_dir: Path,
    out_dir: Path,
    notes: str,
    preview: bool = False,
    previous: Path | None = None,
    profile_dir: Path | None = None,
    corrections_path: Path | None = None,
) -> ReleaseResult:
    out = out_dir / version
    result = ReleaseResult(version=version, path=out, preview=preview, publishable=not preview)
    if out.exists():
        result.errors.append(f"release already exists and is immutable: {out}")
        return result

    report = CatalogReport()
    catalog = load_catalog(catalog_root, catalog_root.parent / "overrides", report)
    if not report.ok:
        result.errors.extend(f"catalogue: {e}" for e in report.errors)
        return result

    if not preview:
        decisions = load_decisions(decision_log_path(catalog_root))
        result.errors.extend(public_release_refusals(catalog, dataset_ids, decisions))
        if result.errors:
            return result

    storage = LocalStorage(data_dir)
    observations, reports, warnings, errors = _load_observations(dataset_ids, catalog, storage)
    result.warnings.extend(warnings)
    result.errors.extend(errors)
    if result.errors:
        return result
    if observations.empty:
        result.errors.append("no observations to release")
        return result

    geographies, versions = _geographies(spine_dir)
    known = set(geographies["geography_id"])
    unknown = sorted(set(observations["geography_id"]) - known)
    if unknown:
        result.errors.append(f"observations reference unknown geographies: {unknown[:10]}")
        return result

    corrections_log = None
    if corrections_path is not None:
        try:
            corrections_log = corrections.load(corrections_path)
        except (OSError, ValueError) as exc:
            result.errors.append(f"corrections log {corrections_path}: {exc}")
            return result
        drafts = corrections.unapproved(corrections_log)
        if drafts and not preview:
            result.errors.append(f"corrections log has entries the lead has not approved: {drafts}")
            return result

    datasets = [_dataset_rights(catalog, dataset_id) for dataset_id in dataset_ids]
    citation = _citation(version, preview)
    observations["release"] = version
    out.mkdir(parents=True)

    observation_files: list[str] = []
    (out / "observations").mkdir(parents=True)
    for dataset_id in dataset_ids:
        rows = observations[observations["dataset_id"] == dataset_id].copy()
        if rows.empty:
            continue
        rel_base = f"observations/{dataset_id}"
        parquet = out / f"{rel_base}.parquet"
        rows.to_parquet(parquet, index=False, compression="zstd")
        observation_files.append(f"{rel_base}.parquet")
        csv_path = out / f"{rel_base}.csv"
        rows.to_csv(csv_path, index=False, lineterminator="\n")
        observation_files.append(f"{rel_base}.csv")

    boundary_frames = _boundary_frames(versions, geographies)
    boundary_files = _boundary_files(boundary_frames, out)
    geopackage_file = _geopackage(boundary_frames, out, version)
    shutil.copyfile(spine_dir / "geographies.parquet", out / "geographies.parquet")
    shutil.copyfile(
        spine_dir / "geography_versions.geoparquet", out / "geography_versions.geoparquet"
    )

    spatial = build_spatial_context(
        observations=observations,
        geographies=geographies,
        catalog=catalog,
        spine_dir=spine_dir,
        out=out,
    )
    result.warnings.extend(spatial.warnings)
    result.errors.extend(spatial.errors)
    if spatial.errors:
        return result

    profiles = None
    if profile_dir is not None:
        packaged = profile_release.build(profile_dir, catalog_root, out, geographies)
        result.warnings.extend(packaged.warnings)
        result.errors.extend(packaged.errors)
        if packaged.errors:
            return result
        profiles = packaged
    compared = _source_comparisons(observations, geographies, catalog_root, data_dir, out)
    result.warnings.extend(compared.warnings)

    qa_lines = [
        f"# Release QA: {version}",
        "",
        "| dataset | checked | errors | warnings |",
        "|---|---|---|---|",
    ]
    for item in reports:
        qa_lines.append(
            f"| {item['dataset_id']} | {item['checked']} | {item['errors']} | "
            f"{len(item['warnings'])} |"
        )
    qa_lines += ["", "## Warnings", ""]
    qa_lines += [f"- {w}" for w in warnings] or ["- none"]
    qa_lines += [
        "",
        "## Spatial context",
        "",
        "Neighbour, parent and national comparisons plus local Moran classes are in "
        "`qa/spatial-context.md`; per-indicator tables are in `stats/`.",
    ]
    if profiles is not None:
        qa_lines += profile_release.qa_lines(profiles)
    if not compared.table.empty:
        pairs = compared.table.drop_duplicates(["geography_id", "indicator_id"])
        differ = pairs["agree"].tolist().count(False)
        qa_lines += [
            "",
            "## Source comparisons (D-019)",
            "",
            f"{differ} of {len(pairs)} place-indicator pairs differ between publishable sources; "
            "see `qa/source-comparisons.md`.",
        ]
    notices = release_notices(datasets)
    if preview:
        qa_lines += [
            "",
            "## Access",
            "",
            "Private preview: not publishable. Built with --preview, so no public-release rights "
            "check was applied.",
        ]
    if notices:
        qa_lines += ["", "## Use and notices", ""] + [
            f"- {n['dataset_id']}: {n['use']} use only ({n['decision']}). {n['notice']}"
            for n in notices
        ]
    _write(out / "qa" / "summary.md", ("\n".join(qa_lines) + "\n").encode("utf-8"))
    for item in reports:
        _write(
            out / "qa" / f"{item['dataset_id']}.md",
            (
                f"# QA report: {item['dataset_id']}\n\n"
                f"- Observations checked: {item['checked']}\n"
                f"- Errors: {item['errors']}\n"
                f"- Warnings: {len(item['warnings'])}\n"
            ).encode(),
        )

    api_files = _write_api(
        out,
        version=version,
        preview=preview,
        observations=observations,
        geographies=geographies,
        catalog=catalog,
        datasets=datasets,
        citation=citation,
        profiles=profiles.payloads if profiles is not None else None,
        comparisons=compared.by_place,
    )

    if corrections_log is not None:
        _write(
            out / "api" / "v1" / "corrections.json",
            _json_bytes(corrections.payload(corrections_log, version)),
        )
        api_files = [*api_files, "api/v1/corrections.json"]

    changelog, changes = _changelog(observations, previous, version)
    _write(out / "CHANGELOG.md", changelog.encode("utf-8"))
    _write(out / "changes.json", _json_bytes(changes))
    notice_md = _notice_markdown(notices)
    _write(
        out / "CITATION.md",
        (
            f"# Citation\n\n{citation}\n\n"
            "Cite individual values with the release version, dataset id, snapshot sha256 and "
            "source locator recorded in each observation.\n"
            + ("\n" + notice_md if notice_md else "")
        ).encode(),
    )
    if notice_md:
        _write(out / "NOTICE.md", notice_md.encode("utf-8"))
    _write(
        out / "README.md",
        (
            (notes.rstrip() + "\n\n" if notes else "# Release\n\n")
            + ("See NOTICE.md: some values are for non-commercial use only.\n\n" if notices else "")
            + "All files are reproducible from the same inputs. The GeoPackage layer metadata "
            "date is derived from the release version (first day of the release month); it is "
            "not a build timestamp.\n"
        ).encode("utf-8"),
    )

    files = (
        observation_files
        + boundary_files
        + spatial.files
        + (profiles.files if profiles is not None else [])
        + compared.files
        + [
            geopackage_file,
            "geographies.parquet",
            "geography_versions.geoparquet",
            "qa/summary.md",
            *[f"qa/{item['dataset_id']}.md" for item in reports],
            *api_files,
            "CHANGELOG.md",
            "changes.json",
            "CITATION.md",
            "README.md",
            *(["NOTICE.md"] if notice_md else []),
        ]
    )
    package = _datapackage(out, version, preview, datasets, files)
    _write(out / "datapackage.json", _json_bytes(package))

    all_files = sorted([*files, "datapackage.json"])
    checksum_lines = []
    for rel in all_files:
        path = out / rel
        checksum_lines.append(f"{_file_sha256(path)}  {rel}")
    _write(out / "CHECKSUMS.sha256", ("\n".join(checksum_lines) + "\n").encode("utf-8"))
    result.files = [*all_files, "CHECKSUMS.sha256"]
    return result
