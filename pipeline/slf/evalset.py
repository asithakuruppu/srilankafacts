"""AI evaluation set (A02), generated from a release.

Every expected answer is copied from the release's static API, with its geography id,
indicator, period, release and citation. Categories: direct lookup at district, DS and GN
level; comparison between two places; aggregation (the parent equals the sum of its
children, for counts); definition; and unanswerable questions, whose expected answer is
"not available". Questions avoid sensitive framing: no rankings of ethnic or religious
groups. Sampling is seeded, so the same release gives the same set.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

LOOKUP_INDICATORS = [
    ("population_total", "How many people were enumerated in {name} {level} in the 2024 census?"),
    ("households_total", "How many households were there in {name} {level} in the 2024 census?"),
    (
        "occupied_housing_units",
        "How many occupied housing units did the 2024 census count in {name} {level}?",
    ),
    (
        "population_aged_60_plus",
        "How many people aged 60 and over lived in {name} {level} in 2024?",
    ),
]
LEVEL_WORDS = {"district": "district", "ds": "DS division", "gn": "GN division"}
UNANSWERABLE = [
    ("What was the GDP of {name} district in 2024?", "No GDP by district is in the release."),
    (
        "How many people in {name} GN division own a car?",
        "Vehicle ownership is not in the release.",
    ),
    (
        "What was the population of {name} DS division in 1950?",
        "No 1950 DS-level figures exist in the release.",
    ),
    ("What is the average household income in {name} district?", "Income is not in the release."),
    (
        "How many people in {name} district voted in the 2025 local elections?",
        "Those results are not in the release.",
    ),
]


def _read(root: Path, rel: str) -> Any:
    return json.loads((root / "api" / "v1" / rel).read_text())


def build(
    release_dir: Path, out_dir: Path, size: int = 150, seed: int = 20261118
) -> dict[str, Any]:
    rng = random.Random(seed)
    latest = _read(release_dir, "releases/latest.json")
    release, citation = latest["release"], latest["citation"]
    geos = _read(release_dir, "geographies/admin.json")["geographies"]
    by_level: dict[str, list[dict[str, Any]]] = {}
    for g in geos:
        if g.get("name_en"):
            by_level.setdefault(g["level_name"], []).append(g)
    children: dict[str, list[str]] = {}
    for g in geos:
        if g.get("parent_id"):
            children.setdefault(g["parent_id"], []).append(g["geography_id"])
    indicators = {i["id"]: i for i in _read(release_dir, "indicators.json")["indicators"]}

    def value(gid: str, indicator: str) -> dict[str, Any] | None:
        path = release_dir / "api" / "v1" / "places" / f"{gid}.json"
        if not path.exists():
            return None
        for v in json.loads(path.read_text())["values"]:
            if v["indicator_id"] == indicator and v.get("value") is not None:
                return v
        return None

    items: list[dict[str, Any]] = []

    def add(category: str, question: str, expected: Any, unit: str | None, **extra: Any) -> None:
        items.append(
            {
                "id": f"q{len(items) + 1:03d}",
                "category": category,
                "question": question,
                "expected": expected,
                "unit": unit,
                "tolerance": 0 if isinstance(expected, int | float) else None,
                "release": release,
                "citation": citation,
                **extra,
            }
        )

    quota = {
        "lookup": int(size * 0.4),
        "comparison": int(size * 0.2),
        "aggregation": int(size * 0.15),
        "definition": int(size * 0.1),
    }
    quota["unanswerable"] = size - sum(quota.values())
    while sum(1 for i in items if i["category"] == "lookup") < quota["lookup"]:
        level = rng.choice(["district", "ds", "gn", "gn"])
        place = rng.choice(by_level[level])
        indicator, template = rng.choice(LOOKUP_INDICATORS)
        v = value(place["geography_id"], indicator)
        if v is None or indicator not in indicators:
            continue
        add(
            "lookup",
            template.format(name=place["name_en"], level=LEVEL_WORDS[level]),
            v["value"],
            v["unit"],
            geography_id=place["geography_id"],
            indicator_id=indicator,
            period=v["period"],
            source_locator=v["source_locator"],
        )
    while sum(1 for i in items if i["category"] == "comparison") < quota["comparison"]:
        level = rng.choice(["district", "ds"])
        a, b = rng.sample(by_level[level], 2)
        va, vb = (
            value(a["geography_id"], "population_total"),
            value(b["geography_id"], "population_total"),
        )
        if va is None or vb is None or va["value"] == vb["value"]:
            continue
        larger = a if va["value"] > vb["value"] else b
        add(
            "comparison",
            f"Which had more people in the 2024 census: {a['name_en']} {LEVEL_WORDS[level]} or "
            f"{b['name_en']} {LEVEL_WORDS[level]}?",
            larger["geography_id"],
            None,
            geography_ids=[a["geography_id"], b["geography_id"]],
            indicator_id="population_total",
            values={a["geography_id"]: va["value"], b["geography_id"]: vb["value"]},
        )
    while sum(1 for i in items if i["category"] == "aggregation") < quota["aggregation"]:
        parent = rng.choice(by_level["ds"])
        kids = children.get(parent["geography_id"], [])
        vp = value(parent["geography_id"], "population_total")
        kid_values = [value(k, "population_total") for k in kids]
        if vp is None or not kids or any(k is None for k in kid_values):
            continue
        total = sum(int(k["value"]) for k in kid_values if k)
        if total != int(vp["value"]):
            continue  # only where the release itself adds up, so the question has one answer
        add(
            "aggregation",
            f"What is the total 2024 census population of all GN divisions in "
            f"{parent['name_en']} DS division?",
            total,
            "persons",
            geography_id=parent["geography_id"],
            indicator_id="population_total",
            children=len(kids),
        )
    for indicator_id in rng.sample(sorted(indicators), quota["definition"]):
        meta = indicators[indicator_id]
        add(
            "definition",
            f"How does Sri Lanka Facts define the indicator '{meta['name']}'?",
            meta["definition"],
            meta["unit"],
            indicator_id=indicator_id,
            scoring="manual or keyword overlap",
        )
    while sum(1 for i in items if i["category"] == "unanswerable") < quota["unanswerable"]:
        template, why = rng.choice(UNANSWERABLE)
        level = "gn" if "GN" in template else "ds" if "DS" in template else "district"
        place = rng.choice(by_level[level])
        add(
            "unanswerable",
            template.format(name=place["name_en"]),
            "not available",
            None,
            geography_id=place["geography_id"],
            reason=why,
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"eval-{release}.jsonl"
    target.write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items))
    counts: dict[str, int] = {}
    for i in items:
        counts[i["category"]] = counts.get(i["category"], 0) + 1
    return {"release": release, "items": len(items), "by_category": counts, "path": str(target)}
