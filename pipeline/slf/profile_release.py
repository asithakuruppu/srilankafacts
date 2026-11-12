"""Package the profile space into a release (D-031).

What ships, per D-031:
- DS divisions: axis positions, distance from the national centre, and similar places with reasons.
- GN divisions: axis positions and distance from the national centre, plus a pointer to their DS
  division's similar places. No GN similar-places list.

Every payload records `space_id` and `space_version` (AGENTS rule 13) and the axis labels'
`label_status` (machine-generated drafts until the lead writes them; rule 7). This module reads the
files `slf profile build` wrote; it does not refit anything.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from slf import profile

PERIOD = profile.PERIOD
SIMILAR_SHOWN = 10  # of the 20 computed; the list is a similarity statement, not a ranking
NOTE = (
    "Machine-computed similarity in the profile space (D-025, D-029). A distance is a similarity "
    "statement, not a fact and not a ranking. Axis labels are machine-generated drafts, not yet "
    "reviewed by a person."
)
GN_NOTE = (
    "Similar-place lists are not published for GN divisions: they change too much under ordinary "
    "small-number variation (D-031). See the DS division's similar places."
)


@dataclass
class ProfileRelease:
    files: list[str] = field(default_factory=list)
    payloads: dict[str, dict[str, Any]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


def _version() -> str:
    return profile.SPACE_VERSION


def shipped_files(version: str) -> list[str]:
    return [
        f"profile_v{version}.parquet",
        f"profile_v{version}_axes.parquet",
        f"similar_ds_{PERIOD}.json",
        f"unusual_ds_{PERIOD}.parquet",
        f"unusual_gn_{PERIOD}.parquet",
    ]


def _axes(axes: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    kept = axes.loc[axes["retained"]]
    for level, rows in kept.groupby("level", sort=True):
        firsts = rows.drop_duplicates("axis").sort_values("axis")
        out[str(level)] = [
            {
                "axis": int(r["axis"]),
                "variance_explained": round(float(r["variance_explained"]), 4),
                "draft_label": str(r["draft_label"]),
                "label_status": str(r["label_status"]),
            }
            for r in firsts.to_dict("records")
        ]
    return out


def build(
    profile_dir: Path, catalog_root: Path, out: Path, geographies: pd.DataFrame
) -> ProfileRelease:
    result = ProfileRelease()
    version = _version()
    vectors = profile_dir / "vectors"
    missing = [f for f in shipped_files(version) if not (vectors / f).exists()]
    if missing:
        result.errors.append(
            f"profile build incomplete in {vectors}: missing {missing}; run `slf profile build`"
        )
        return result
    space = profile.load_space(catalog_root)  # refuses a recipe/version mismatch
    vec = pd.read_parquet(vectors / f"profile_v{version}.parquet")
    found = sorted(set(vec["space_version"].astype(str)))
    if found != [space.version]:
        result.errors.append(f"profile vectors are version {found}, catalogue says {space.version}")
        return result

    dest = out / "vectors"
    dest.mkdir(parents=True, exist_ok=True)
    for name in shipped_files(version):
        shutil.copyfile(vectors / name, dest / name)
        result.files.append(f"vectors/{name}")

    names = dict(zip(geographies["geography_id"], geographies["name_en"], strict=False))
    parents = dict(zip(geographies["geography_id"], geographies["parent_id"], strict=False))
    axes = _axes(pd.read_parquet(vectors / f"profile_v{version}_axes.parquet"))
    similar = json.loads((vectors / f"similar_ds_{PERIOD}.json").read_text(encoding="utf-8"))
    indicators: list[str] = similar["indicators"]
    unusual = {
        level: pd.read_parquet(vectors / f"unusual_{level}_{PERIOD}.parquet").set_index(
            "geography_id"
        )
        for level in ("gn", "ds")
    }

    places = vec.loc[vec["entity_type"] == "place"]
    for row in places.to_dict("records"):
        geo, level = str(row["entity_id"]), str(row["level"])
        u = unusual[level].loc[geo]
        block: dict[str, Any] = {
            "space_id": space.id,
            "space_version": space.version,
            "period": PERIOD,
            "level": level,
            "note": NOTE,
            "axes": [
                {**a, "score": round(float(s), 4)}
                for a, s in zip(axes[level], list(row["vector"]), strict=True)
            ],
            "distance_from_centre": round(float(u["distance_from_centre"]), 4),
            "percentile": float(u["percentile"]),
            "unusual_indicators": [str(i) for i in list(u["top_indicators"])],
        }
        if level == "ds":
            block["similar"] = [
                {
                    "geography_id": n,
                    "name_en": names.get(n),
                    "distance": d,
                    "alike": [indicators[i] for i, _ in alike],
                    "different": [indicators[i] for i, _ in diff],
                }
                for n, d, alike, diff in similar["places"].get(geo, [])[:SIMILAR_SHOWN]
            ]
        else:
            parent = parents.get(geo)
            block["similar"] = None
            block["similar_note"] = GN_NOTE
            block["similar_via"] = None if parent is None or pd.isna(parent) else str(parent)
        result.payloads[geo] = block

    counts = places["level"].value_counts().to_dict()
    result.summary = {
        "space_id": space.id,
        "space_version": space.version,
        "places": {str(k): int(v) for k, v in sorted(counts.items())},
        "ds_with_similar": sum(1 for p in result.payloads.values() if p["similar"]),
        "axes": {k: len(v) for k, v in axes.items()},
    }
    excluded = profile_dir / "excluded_places.csv"
    if excluded.exists():
        n = len(pd.read_csv(excluded))
        result.summary["excluded"] = n
    return result


def qa_lines(p: ProfileRelease) -> list[str]:
    s = p.summary
    lines = [
        "",
        "## Profile space (D-031)",
        "",
        f"- Space `{s['space_id']}` v{s['space_version']}; places with vectors: "
        + ", ".join(f"{k} {v:,}" for k, v in s["places"].items())
        + f"; excluded: {s.get('excluded', 'n/a')} (listed in the profile build).",
        f"- Similar places shown for {s['ds_with_similar']} DS divisions (top {SIMILAR_SHOWN} of "
        "20). GN divisions show axis positions and distance from the centre only (D-031).",
        "- Axis labels are machine-generated drafts (`label_status: machine_generated_draft`).",
    ]
    return lines
