"""Resolution manifest for the atlas bundle ("Finest view" page).

One row per catalogue dataset: the native resolution the source holds, what the platform
shows today, and the information floor. Nothing is guessed. Metres come only from an explicit
`information_unit` such as `grid-30m` or from a plain "<n> m" / "<n> km" in the catalogue's
`spatial.resolution`; anything else stays null and is shown as "not recorded".
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from slf.catalog import Catalog, CatalogReport, load_catalog
from slf.release import _dataset_rights

# H3 average edge length, from the H3 documentation (https://h3geo.org/docs/core-library/restable).
H3_EDGE_M = {7: 1220.0, 8: 461.0, 9: 174.0, 10: 66.0}

_UNIT = re.compile(r"^grid-(\d+(?:\.\d+)?)(m|km)$")
_TEXT = re.compile(r"(?:about\s+)?(\d+(?:\.\d+)?)\s*(m|km)\b")


def _metres(value: float, unit: str) -> float:
    return value * 1000.0 if unit == "km" else value


def native_metres(information_unit: str | None, resolution: str | None) -> float | None:
    """Native cell size in metres, or None when the catalogue does not state one plainly."""
    # The catalogue's own words are the more exact (about 1.2 m), the unit label the fallback.
    if resolution:
        h3 = re.match(r"^h3:(\d+)$", resolution)
        if h3:
            return H3_EDGE_M.get(int(h3.group(1)))
        m = _TEXT.search(resolution)
        if m:
            return _metres(float(m.group(1)), m.group(2))
    if information_unit:
        m = _UNIT.match(information_unit)
        if m:
            return _metres(float(m.group(1)), m.group(2))
    return None


def _shown_as(support: str, level: str | None, derived_by: str | None) -> str:
    """What the platform shows today for this dataset."""
    if derived_by and derived_by.startswith(("zonal", "sheet_overlap")):
        return "gn_zonal"
    if derived_by and derived_by.startswith("point_in_polygon"):
        return "points"
    if support == "point":
        return "points"
    if support in {"line", "grid"}:
        return "as_catalogued"
    if support == "national":
        return "national"
    return f"area_{level}" if level else "area"


def _tier(support: str, level: str | None, metres: float | None) -> str:
    if metres is not None:
        return "finer_than_gn"
    if support in {"point", "line"}:
        return "finer_than_gn"
    if support == "grid":
        return "unknown"
    if support == "national":
        return "national"
    return "gn" if level == "gn" else "coarser_than_gn"


def build_rows(catalog: Catalog) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ds in catalog.datasets.values():
        sp = ds.spatial
        if sp is None:
            continue
        metres = native_metres(sp.information_unit, sp.resolution)
        rights = _dataset_rights(catalog, ds.id)
        rows.append(
            {
                "dataset_id": ds.id,
                "title": ds.title,
                "status": ds.status,
                "support": sp.support,
                "level": sp.level,
                "native_resolution_text": sp.resolution,
                "native_resolution_m": metres,
                "information_unit": sp.information_unit,
                "information_count": sp.information_count,
                "tier": _tier(sp.support, sp.level, metres),
                "shown_as": _shown_as(sp.support, sp.level, sp.derived_by),
                "derived_by": sp.derived_by,
                "indicators": len(ds.indicators),
                "reference_period": ds.reference_period,
                "landing_page": str(ds.landing_page) if ds.landing_page else None,
                "source_name": rights["source_name"],
                "rights_status": rights["rights_status"],
                "use": rights["use"],
                "attribution": rights["attribution"],
            }
        )
    # Finest first; datasets with no recorded metres go after those with one, then by id.
    rows.sort(
        key=lambda r: (
            r["native_resolution_m"] is None,
            r["native_resolution_m"] or 0.0,
            r["dataset_id"],
        )
    )
    return rows


def build(catalog_dir: Path, target: Path) -> dict[str, Any]:
    """Write resolution.json into the bundle and return its manifest entry."""
    catalog = load_catalog(catalog_dir, catalog_dir.parent / "overrides", CatalogReport())
    rows = build_rows(catalog)
    payload = {
        "kind": "native resolution of each catalogue dataset (derived from catalog/datasets)",
        "note": (
            "native_resolution_m is stated only where the catalogue says it plainly; null means "
            "not recorded. Native resolution is not information: see information_unit."
        ),
        "datasets": rows,
    }
    (target / "resolution.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    return {
        "available": True,
        "datasets": len(rows),
        "with_metres": sum(r["native_resolution_m"] is not None for r in rows),
        "finer_than_gn": sum(r["tier"] == "finer_than_gn" for r in rows),
    }
