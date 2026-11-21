"""Cell covers (G07 step 7, footprint-model.md §2): footprint -> H3 r10 cells with fractions.

A cover lists the r10 cells that make up a footprint. Cells are equal in area, so a footprint's
`fraction` per cell is its share of the footprint's area: 1 / (cells in the footprint) for whole
GNs. Footprints are composed from whole GNs (weights come from the relation files; a GN split
between units contributes its share). Fractions per footprint sum to 1.

Families: `admin` (GN, DS, district, province), `electoral_ed` (22 EDs, public composition from
districts), `la` and `moh` (from nuuuwan gig-data, rights unclear, D-046: written with the
`_internal` suffix and never published). PD has no persisted GN membership and is not built.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

LEVEL_NAMES = {1: "province", 2: "district", 3: "ds", 4: "gn"}


def _members_from_relations(
    rel: Any, units_prefix: str | None = None
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for row in rel[rel["relation"] == "composed_of"].to_dict("records"):
        unit = str(row["geography_id"])
        if units_prefix and not unit.startswith(units_prefix):
            continue
        out.setdefault(unit, {})[str(row["related_id"])] = float(row["weight"])
    return out


def admin_members(geographies: Any) -> dict[str, dict[str, float]]:
    """GN share of every admin unit above GN level (descendants by parent_id), and GN itself."""
    parent = dict(zip(geographies["geography_id"], geographies["parent_id"], strict=True))
    level = dict(zip(geographies["geography_id"], geographies["level"], strict=True))
    members: dict[str, dict[str, float]] = {}
    for gid, lv in level.items():
        if lv != 4:
            continue
        members.setdefault(str(gid), {})[str(gid)] = 1.0
        node = parent.get(gid)
        while isinstance(node, str) and level.get(node, 0) >= 1:
            members.setdefault(node, {})[str(gid)] = 1.0
            node = parent.get(node)
    return members


def expand_districts(
    ed_members: Mapping[str, Mapping[str, float]], admin: Mapping[str, Mapping[str, float]]
) -> dict[str, dict[str, float]]:
    """ED composed of districts -> ED composed of GNs."""
    out: dict[str, dict[str, float]] = {}
    for ed, parts in ed_members.items():
        gns: dict[str, float] = {}
        for district, share in parts.items():
            for gid, w in admin.get(district, {}).items():
                gns[gid] = gns.get(gid, 0.0) + share * w
        out[ed] = gns
    return out


def cover(
    members: Mapping[str, Mapping[str, float]], gn_cells: Mapping[str, list[str]]
) -> pd.DataFrame:
    """One row per (footprint, cell) with `fraction`; fractions per footprint sum to 1."""
    refs: list[str] = []
    cells: list[str] = []
    fractions: list[float] = []
    for unit, gns in sorted(members.items()):
        pairs = [
            (c, share / len(gn_cells[g])) for g, share in gns.items() for c in gn_cells.get(g, [])
        ]
        total = sum(f for _, f in pairs)
        if total == 0:
            continue
        for c, f in pairs:
            refs.append(unit)
            cells.append(c)
            fractions.append(f / total)
    return pd.DataFrame({"footprint_ref": refs, "h3": cells, "fraction": fractions})


def check(cov: Any) -> dict[str, Any]:
    sums = cov.groupby("footprint_ref")["fraction"].sum()
    return {
        "footprints": int(sums.size),
        "rows": len(cov),
        "max_fraction_sum_error": float(abs(sums - 1.0).max()) if len(sums) else 0.0,
    }


def build(
    spine_dir: Path,
    weights_parquet: Path,
    catalog_dir: Path,
    out_dir: Path,
    internal_dirs: Mapping[str, Path],
) -> dict[str, Any]:
    """Write `cover_{family}_h3r10.parquet` for each family; return a QA summary."""
    geographies = pd.read_parquet(spine_dir / "geographies.parquet")
    cells = pd.read_parquet(weights_parquet, columns=["geography_id", "h3"])
    gn_cells: dict[str, list[str]] = {
        str(k): list(v) for k, v in cells.groupby("geography_id")["h3"].agg(list).items()
    }
    admin = admin_members(geographies)
    ed_rel = pd.read_csv(catalog_dir / "geographies/relations/electoral_ec-2024.csv")
    families: dict[str, tuple[dict[str, dict[str, float]], str]] = {
        "admin": (admin, "public"),
        "electoral_ed": (
            expand_districts(_members_from_relations(ed_rel, "LK-ED-"), admin),
            "public",
        ),
    }
    for family, rel_path in internal_dirs.items():
        families[family] = (_members_from_relations(pd.read_csv(rel_path)), "internal")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {}
    for family, (members, rights) in families.items():
        cov = cover(members, gn_cells)
        name = f"cover_{family}_h3r10" + ("_internal" if rights == "internal" else "") + ".parquet"
        cov.to_parquet(out_dir / name, index=False)
        stats = check(cov)
        gn_without_cells = sorted({g for gns in members.values() for g in gns} - set(gn_cells))
        stats.update(
            {
                "units_without_cells": sorted(set(members) - set(cov["footprint_ref"])),
                "member_gn_without_cells": gn_without_cells,
                "rights": rights,
                "file": name,
            }
        )
        summary[family] = stats
    (out_dir / "covers_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
