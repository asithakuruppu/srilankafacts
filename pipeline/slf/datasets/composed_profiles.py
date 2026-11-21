"""Profile content for GN-composed units (local authorities, MOH areas): G05 step 6.

Reads the ``<scheme>_denominators*.csv`` that ``slf composition build`` wrote (counts that are
already sum(weight x GN value)) plus its QA tables, and writes one JSON with a profile per unit.
Every rate is **recomputed from counts** (never averaged across GNs). The output carries
``publishable``: false for an internal run, and the website renders nothing from such a file.

Rule 5/6: units are keyed by composition ids, never matched by name; units with no census GN
are kept in the file with null values and a flag, not dropped.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, cast

import pandas as pd

COUNT_FIELDS = [
    "population_total",
    "population_age_0_4",
    "population_age_5_9",
    "population_age_10_14",
    "population_age_15_19",
    "population_age_15_plus",
    "population_age_20_plus",
    "households_total",
    "occupied_housing_units",
]

# Quality flags: thresholds are descriptive labels for readers, not corrections.
IOU_LOW = 0.9
TYPE_SHARE_LOW = 0.9


def _num(value: Any) -> float | None:
    if value is None:
        return None
    f = float(value)
    return None if math.isnan(f) else f


def _ratio(num: float | None, den: float | None) -> float | None:
    if num is None or den is None or den <= 0:
        return None
    return num / den


def unit_profile(row: pd.Series, iou: float | None, type_share: float | None) -> dict[str, Any]:
    counts = {k: _num(row.get(k)) for k in COUNT_FIELDS}
    pop = counts["population_total"]
    young = None
    parts = [
        counts[k] for k in ("population_age_0_4", "population_age_5_9", "population_age_10_14")
    ]
    if all(p is not None for p in parts):
        young = float(sum(p for p in parts if p is not None))
    members = int(cast(Any, row["gn_members"]))
    with_census = int(cast(Any, row["gn_with_census"]))
    flags: list[str] = []
    if with_census == 0:
        flags.append("no_census_gn")
    elif with_census < members:
        flags.append("some_gn_without_census")
    if iou is not None and iou < IOU_LOW:
        flags.append("shape_disagrees_with_gn_union")
    if type_share is not None and type_share < TYPE_SHARE_LOW:
        flags.append("dcs_local_authority_type_mismatch")
    return {
        "id": str(row["geography_id"]),
        "name": row.get("name"),
        "gn_members": members,
        "gn_with_census": with_census,
        "counts": counts,
        "rates": {
            "share_aged_0_14": _ratio(young, pop),
            "share_aged_15_plus": _ratio(counts["population_age_15_plus"], pop),
            "population_per_household": _ratio(pop, counts["households_total"]),
            "occupied_units_per_household": _ratio(
                counts["occupied_housing_units"], counts["households_total"]
            ),
        },
        "iou_shape_vs_gn_union": iou,
        "share_in_own_dcs_la_type": type_share,
        "flags": flags,
    }


def build_profiles(
    build_dir: Path,
    scheme: str,
    *,
    publishable: bool,
    source_note: str,
    attribution: str | None = None,
    notice: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Write ``<scheme>_profiles[_internal].json`` next to the composition build; return summary."""
    tag = "" if publishable else "_internal"
    den = pd.read_csv(build_dir / f"{scheme}_denominators{tag}.csv")
    iou_path = build_dir / f"{scheme}_iou{tag}.csv"
    iou = pd.read_csv(iou_path).set_index("unit")["iou"].to_dict() if iou_path.exists() else {}
    type_path = build_dir / f"{scheme}_census_type_check{tag}.csv"
    types = (
        pd.read_csv(type_path).set_index("geography_id")["share_in_own_kind"].to_dict()
        if type_path.exists()
        else {}
    )
    gap_path = build_dir / f"{scheme}_spine_gn_without_unit{tag}.csv"
    gaps = len(pd.read_csv(gap_path)) if gap_path.exists() else None
    profiles = [
        unit_profile(row, _num(iou.get(row["geography_id"])), _num(types.get(row["geography_id"])))
        for _, row in den.iterrows()
    ]
    flag_counts: dict[str, int] = {}
    for p in profiles:
        for f in p["flags"]:
            flag_counts[f] = flag_counts.get(f, 0) + 1
    doc = {
        "scheme": scheme,
        "publishable": publishable,
        "source": source_note,
        "method": "docs/methods/denominators-la-moh.md",
        "support": "sum(weight x GN value) over Census 2024 GN tables; rates from counts",
        "attribution": attribution,
        "notice": notice,
        "spine_gns_without_unit": gaps,
        "units": profiles,
    }
    out = build_dir / f"{scheme}_profiles{tag}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return out, {
        "units": len(profiles),
        "units_with_flags": sum(1 for p in profiles if p["flags"]),
        "flag_counts": flag_counts,
    }
