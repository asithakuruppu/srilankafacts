"""Catalogue validator (prompt F02).

Checks every YAML and CSV file in catalog/ and overrides/ against slf.schemas, then checks the
links between them (dataset → source, indicator → component indicators, override → dataset,
dataset → geography scheme), unique IDs, and the publishing rules: rights recorded (AGENTS rule 4)
and a confirmed source CRS in the spatial block (spatial-first-analytics.md §3).

Errors fail CI. "Not publishable" findings are reported but don't fail: proposed datasets are
allowed to have unclear rights; they just can't enter a release.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from slf.schemas import (
    EXPORTED_SCHEMAS,
    Dataset,
    GeoCodeRow,
    GeographySchemes,
    GeoRelationRow,
    Indicator,
    ManualMatchRow,
    OverrideRow,
    ProvisionalGeographyRow,
    Rights,
    Source,
    VectorSpace,
)

CATALOG_DIRS = ("sources", "datasets", "indicators", "geographies", "spaces")


@dataclass
class CatalogReport:
    errors: list[str] = field(default_factory=list)
    not_publishable: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class Catalog:
    sources: dict[str, Source] = field(default_factory=dict)
    datasets: dict[str, Dataset] = field(default_factory=dict)
    indicators: dict[str, Indicator] = field(default_factory=dict)
    spaces: dict[str, VectorSpace] = field(default_factory=dict)
    schemes: GeographySchemes | None = None
    codes: list[GeoCodeRow] = field(default_factory=list)
    relations: list[GeoRelationRow] = field(default_factory=list)
    provisional: list[ProvisionalGeographyRow] = field(default_factory=list)
    manual_matches: list[ManualMatchRow] = field(default_factory=list)
    overrides: list[OverrideRow] = field(default_factory=list)


def _fmt(path: Path, exc: ValidationError, row: int | None = None) -> list[str]:
    where = f"{path}" + (f" row {row}" if row is not None else "")
    out = []
    for e in exc.errors():
        loc = ".".join(str(p) for p in e["loc"]) or "(file)"
        out.append(f"{where}: {loc}: {e['msg']}")
    return out


def _load_yaml(path: Path, report: CatalogReport) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        report.errors.append(f"{path}: invalid YAML ({exc})")
        return None


def _load_models[M: BaseModel](folder: Path, model: type[M], report: CatalogReport) -> dict[str, M]:
    out: dict[str, M] = {}
    for path in sorted(folder.glob("*.yaml")):
        data = _load_yaml(path, report)
        if data is None:
            continue
        try:
            obj = model.model_validate(data)
        except ValidationError as exc:
            report.errors.extend(_fmt(path, exc))
            continue
        obj_id: str = getattr(obj, "id")  # noqa: B009 - every catalogue model has an id
        if path.stem != obj_id:
            report.errors.append(f"{path}: id '{obj_id}' must match the file name")
        if obj_id in out:
            report.errors.append(f"{path}: duplicate id '{obj_id}'")
        out[obj_id] = obj
    return out


def _load_csv_file[M: BaseModel](path: Path, model: type[M], report: CatalogReport) -> list[M]:
    rows: list[M] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for i, raw in enumerate(csv.DictReader(fh), start=2):  # row 1 is the header
            clean = {k: (v if v != "" else None) for k, v in raw.items()}
            try:
                rows.append(model.model_validate(clean))
            except ValidationError as exc:
                report.errors.extend(_fmt(path, exc, row=i))
    return rows


def _load_csv_rows[M: BaseModel](folder: Path, model: type[M], report: CatalogReport) -> list[M]:
    rows: list[M] = []
    if not folder.is_dir():
        return rows
    for path in sorted(folder.glob("*.csv")):
        rows.extend(_load_csv_file(path, model, report))
    return rows


def load_catalog(root: Path, overrides_root: Path | None, report: CatalogReport) -> Catalog:
    cat = Catalog()
    for name in CATALOG_DIRS:
        if not (root / name).is_dir():
            report.errors.append(f"missing folder: {root / name}")
    cat.sources = _load_models(root / "sources", Source, report)
    cat.datasets = _load_models(root / "datasets", Dataset, report)
    cat.indicators = _load_models(root / "indicators", Indicator, report)
    cat.spaces = _load_models(root / "spaces", VectorSpace, report)
    schemes_path = root / "geographies" / "schemes.yaml"
    if schemes_path.exists():
        data = _load_yaml(schemes_path, report)
        if data is not None:
            try:
                cat.schemes = GeographySchemes.model_validate(data)
            except ValidationError as exc:
                report.errors.extend(_fmt(schemes_path, exc))
    cat.codes = _load_csv_rows(root / "geographies" / "codes", GeoCodeRow, report)
    cat.relations = _load_csv_rows(root / "geographies" / "relations", GeoRelationRow, report)
    prov = root / "geographies" / "provisional.csv"
    if prov.exists():
        cat.provisional = _load_csv_file(prov, ProvisionalGeographyRow, report)
    mm = root / "geographies" / "manual-matches.csv"
    if mm.exists():
        cat.manual_matches = _load_csv_file(mm, ManualMatchRow, report)
    if overrides_root is not None:
        cat.overrides = _load_csv_rows(overrides_root, OverrideRow, report)
    return cat


def effective_rights(cat: Catalog, ds: Dataset) -> Rights | None:
    if isinstance(ds.rights, Rights):
        return ds.rights
    src = cat.sources.get(ds.source)
    return src.rights if src else None


DECISION_RE = re.compile(r"^## (D-\d{3}):.*?\n- \*\*Status:\*\* (\w+)", re.MULTILINE | re.DOTALL)


def load_decisions(path: Path) -> dict[str, str] | None:
    """Map decision id to its status word (Accepted, Proposed, ...) from the decision log."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for block in re.split(r"(?m)^(?=## D-\d{3}:)", text):
        m = DECISION_RE.match(block)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def decision_log_path(catalog_root: Path) -> Path:
    return catalog_root.parent / "docs" / "decisions" / "decision-log.md"


def check_links(
    cat: Catalog, report: CatalogReport, decisions: dict[str, str] | None = None
) -> None:
    scheme_ids = {s.id for s in cat.schemes.schemes} if cat.schemes else set()
    levels = {s.id: {lv.id for lv in s.levels} for s in cat.schemes.schemes} if cat.schemes else {}
    if cat.schemes:
        seen: set[str] = set()
        for s in cat.schemes.schemes:
            if s.id in seen:
                report.errors.append(f"schemes.yaml: duplicate scheme '{s.id}'")
            seen.add(s.id)

    for ds in cat.datasets.values():
        where = f"datasets/{ds.id}.yaml"
        if ds.source not in cat.sources:
            report.errors.append(f"{where}: source '{ds.source}' not found in catalog/sources")
        for ind in ds.indicators:
            if ind not in cat.indicators:
                report.errors.append(f"{where}: indicator '{ind}' not found in catalog/indicators")
        for scheme in {ds.geography_scheme, ds.spatial.scheme} - {None}:
            if scheme_ids and scheme not in scheme_ids:
                report.errors.append(f"{where}: geography scheme '{scheme}' not in schemes.yaml")
        sp = ds.spatial
        if sp.scheme in levels and sp.level and sp.level not in levels[sp.scheme]:
            report.errors.append(
                f"{where}: spatial.level '{sp.level}' is not a level of scheme '{sp.scheme}' "
                f"({', '.join(sorted(levels[sp.scheme]))})"
            )

        rights = effective_rights(cat, ds)
        pub = ds.publication
        if pub is not None and (rights is None or rights.status != "unclear"):
            report.errors.append(
                f"{where}: publication decision {pub.decision} applies only while rights are "
                f"unclear (rights are {rights.status if rights else 'missing'})"
            )
        elif pub is not None and decisions is not None:
            status = decisions.get(pub.decision)
            if status != "Accepted":
                report.errors.append(
                    f"{where}: publication decision {pub.decision} is "
                    f"{status or 'not in the decision log'}, not Accepted"
                )
        if rights is None or (rights.status == "unclear" and pub is None):
            report.not_publishable.append(f"{ds.id}: rights unclear")
        elif rights.status == "restricted":
            report.not_publishable.append(f"{ds.id}: rights restricted")
        if ds.spatial.crs_source in (None, "unconfirmed") and ds.spatial.support != "national":
            report.not_publishable.append(f"{ds.id}: source CRS not confirmed")

    for ind in cat.indicators.values():
        for role in ("numerator", "denominator"):
            ref = getattr(ind, role)
            if ref and ref not in cat.indicators:
                report.errors.append(f"indicators/{ind.id}.yaml: {role} '{ref}' not found")

    for ov in cat.overrides:
        if ov.dataset_id not in cat.datasets:
            report.errors.append(f"override {ov.override_id}: dataset '{ov.dataset_id}' not found")
    ov_ids = Counter(o.override_id for o in cat.overrides)
    for dup in sorted(i for i, n in ov_ids.items() if n > 1):
        report.errors.append(f"overrides: duplicate override_id '{dup}'")

    prov_ids = Counter(p.geography_id for p in cat.provisional)
    for dup in sorted(i for i, n in prov_ids.items() if n > 1):
        report.errors.append(
            f"provisional.csv: duplicate id '{dup}' (provisional ids are never reused)"
        )
    prov_set = set(prov_ids)
    for m in cat.manual_matches:
        if (
            m.geography_id
            and m.geography_id.startswith("LK-ADM")
            and m.geography_id not in prov_set
        ):
            report.errors.append(f"manual-matches: {m.geography_id} is not in provisional.csv")
    mm_keys = Counter((m.system, m.code) for m in cat.manual_matches)
    for dup in sorted(k for k, n in mm_keys.items() if n > 1):
        report.errors.append(f"manual-matches: duplicate decision for {dup}")
    composed = Counter(r.geography_id for r in cat.relations if r.relation == "composed_of")
    for p in cat.provisional:
        if p.status == "provisional" and not composed.get(p.geography_id):
            report.errors.append(f"provisional unit {p.geography_id} has no composed_of relations")

    edges = Counter((r.geography_id, r.related_id, r.relation, r.vintage) for r in cat.relations)
    for dup in sorted(e for e, n in edges.items() if n > 1):
        report.errors.append(f"relations: duplicate edge {dup}")


def validate_catalog(root: Path, overrides_root: Path | None = None) -> CatalogReport:
    report = CatalogReport()
    if not root.is_dir():
        report.errors.append(f"catalogue folder not found: {root}")
        return report
    cat = load_catalog(root, overrides_root, report)
    check_links(cat, report, load_decisions(decision_log_path(root)))
    report.counts = {
        "sources": len(cat.sources),
        "datasets": len(cat.datasets),
        "indicators": len(cat.indicators),
        "schemes": len(cat.schemes.schemes) if cat.schemes else 0,
        "spaces": len(cat.spaces),
        "code rows": len(cat.codes),
        "relation rows": len(cat.relations),
        "overrides": len(cat.overrides),
        "provisional units": len(cat.provisional),
        "manual matches": len(cat.manual_matches),
    }
    return report


def export_json_schemas(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, model in EXPORTED_SCHEMAS.items():
        path = out_dir / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written
