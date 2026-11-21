# ruff: noqa: E501
"""CROPIX (Department of Agriculture) geography lists: code crosswalk and GN memberships (D-062).

Reads the snapshotted public endpoints under ``raw/department-of-agriculture/cropix-geographies/``
and writes a **local, private** build: each CROPIX GN division matched to the spine through the
DCS Census 2024 codes in ``catalog/geographies/codes/dcs-census2024.csv`` (rule 5: a code join
through the crosswalk, never by name), with the agriculture geographies CROPIX assigns to it
(agro-ecological zone, AI region, ASC and ARPA areas, Mahaweli system/block/unit).

CROPIX GN codes are ``P-D-SS-GGG`` (province, district index, DS, GN); the DCS code is
``P`` + ``D`` + ``SS`` + ``GGG`` (for example ``1-1-03-115`` -> ``1103115``, Pettah). Names are
compared only as a check. Nothing here enters a release: rights are unclear (D-062), and endpoints
about individual farmers are never fetched.
"""

from __future__ import annotations

import csv
import difflib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SOURCE = "department-of-agriculture"
DATASET = "cropix-geographies"
_CODE = re.compile(r"(\d)-(\d{1,2})-(\d{2})-(\d{3})")


def dcs_code(cropix_code: str) -> str | None:
    """CROPIX GN code -> DCS 7-digit GN code, or None if the code is not in the P-D-SS-GGG form."""
    m = _CODE.fullmatch(cropix_code.strip())
    if not m:
        return None
    p, d, ds, gn = m.groups()
    return f"{p}{int(d)}{ds}{gn}"


def _norm(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def name_agreement(a: str, b: str) -> str:
    """'same' (ignoring case, spaces, punctuation), 'close' (spelling, ratio >= 0.8) or 'different'."""
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return "same"
    return "close" if difflib.SequenceMatcher(None, na, nb).ratio() >= 0.8 else "different"


def load_pages(raw_root: Path, stem: str) -> tuple[list[dict[str, Any]], list[str]]:
    """All items of one endpoint (latest snapshot of each page) and the snapshot files used."""
    base = raw_root / SOURCE / DATASET
    latest: dict[str, Path] = {}
    for path in sorted(base.glob(f"*/{stem}__p*.json")):
        if path.name.endswith(".meta.json"):
            continue
        latest[path.name] = path  # later retrieval folders sort last
    items: list[dict[str, Any]] = []
    for path in latest.values():
        items += json.loads(path.read_text())["payloadDto"]
    return items, [str(p.relative_to(raw_root)) for p in latest.values()]


def _get(d: dict[str, Any] | None, *keys: str) -> Any:
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


@dataclass
class Crosswalk:
    rows: list[dict[str, Any]] = field(default_factory=list)
    unmatched: list[dict[str, Any]] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    counts: Counter[str] = field(default_factory=Counter)


def build(raw_root: Path, catalog_root: Path) -> Crosswalk:
    gns, files = load_pages(raw_root, "admin-divisions__gn-divisions")
    codes = catalog_root / "geographies" / "codes" / "dcs-census2024.csv"
    with codes.open(newline="", encoding="utf-8") as f:
        dcs = {
            r["external_code"]: (r["geography_id"], r["external_name"])
            for r in csv.DictReader(f)
            if len(r["external_code"]) == 7
        }
    out = Crosswalk(files=files)
    seen: set[str] = set()
    for g in gns:
        code = str(g.get("code", ""))
        if code in seen:
            out.counts["duplicate CROPIX code"] += 1
            continue
        seen.add(code)
        dc = dcs_code(code)
        hit = dcs.get(dc) if dc else None
        record = {
            "cropix_id": g.get("id"),
            "cropix_code": code,
            "cropix_name": str(g.get("name", "")).strip(),
            "gn_division_type": g.get("gnDivisionType"),
            "ae_zone": _get(g, "agroEcologicalZoneDTO", "aeZoneId"),
            "ai_region_id": _get(g, "aiRegionsDTO", "regionId"),
            "ai_region_name": _get(g, "aiRegionsDTO", "description"),
            "arpa_id": _get(g, "arpaDTO", "arpaId"),
            "arpa_name": _get(g, "arpaDTO", "name"),
            "asc_id": _get(g, "arpaDTO", "ascDto", "ascId"),
            "asc_name": _get(g, "arpaDTO", "ascDto", "name"),
            "mahaweli_system": _get(g, "mahaweliSystemDTO", "systemId"),
            "mahaweli_block": _get(g, "mahaweliBlockDTO", "description"),
            "mahaweli_unit": _get(g, "mahaweliUnitDTO", "unitId"),
            "mahaweli_unit_name": _get(g, "mahaweliUnitDTO", "description"),
        }
        if dc is None:
            out.counts["code not in P-D-SS-GGG form"] += 1
            out.unmatched.append({**record, "reason": "code not in P-D-SS-GGG form"})
            continue
        if hit is None:
            out.counts["no DCS 2024 GN with this code"] += 1
            out.unmatched.append({**record, "reason": f"no DCS 2024 GN code {dc}"})
            continue
        agreement = name_agreement(record["cropix_name"], hit[1])
        out.counts[f"matched, names {agreement}"] += 1
        out.rows.append(
            {
                **record,
                "dcs_code": dc,
                "geography_id": hit[0],
                "dcs_name": hit[1],
                "name_agreement": agreement,
            }
        )
    out.counts["CROPIX GN records"] = len(gns)
    return out


def qa_markdown(cw: Crosswalk) -> str:
    c = cw.counts
    matched = len(cw.rows)
    total = c["CROPIX GN records"]
    zones = Counter(r["ae_zone"] for r in cw.rows if r["ae_zone"])
    with_asc = sum(1 for r in cw.rows if r["asc_id"])
    with_mahaweli = sum(
        1 for r in cw.rows if r["mahaweli_system"] or r["mahaweli_block"] or r["mahaweli_unit"]
    )
    spine_ids = {r["geography_id"] for r in cw.rows}
    lines = [
        "# QA report: CROPIX GN divisions against the spine (`cropix-geographies`, local only, D-062)",
        "",
        f"- CROPIX GN records: {total}; matched to a spine GN through DCS 2024 codes: {matched} "
        f"({matched / total:.1%})"
        if total
        else "- no CROPIX GN records",
        f"- Distinct spine GN reached: {len(spine_ids)}",
        *[f"- {k}: {v}" for k, v in sorted(c.items()) if k != "CROPIX GN records"],
        f"- Matched GN with an agro-ecological zone: {sum(zones.values())} in {len(zones)} zones",
        f"- Matched GN with an ASC/ARPA area: {with_asc}; with a Mahaweli system, block or unit: {with_mahaweli}",
        "",
        "Names are a check, not the join: 'close' is a spelling difference (similarity >= 0.8); "
        "'different' needs a look (renamed GN, or a code that points elsewhere).",
        "",
        "## Names that differ (first 30)",
        "",
        "| CROPIX code | CROPIX name | DCS 2024 name | spine id |",
        "|---|---|---|---|",
        *[
            f"| {r['cropix_code']} | {r['cropix_name']} | {r['dcs_name']} | {r['geography_id']} |"
            for r in [r for r in cw.rows if r["name_agreement"] == "different"][:30]
        ],
        "",
        "## Unmatched CROPIX GN (first 30 of " + str(len(cw.unmatched)) + ")",
        "",
        "| CROPIX code | name | reason |",
        "|---|---|---|",
        *[
            f"| {u['cropix_code']} | {u['cropix_name']} | {u['reason']} |"
            for u in cw.unmatched[:30]
        ],
        "",
        "## Snapshots",
        "",
        *[f"- `{f}`" for f in cw.files],
    ]
    return "\n".join(lines) + "\n"


def write(cw: Crosswalk, out_dir: Path) -> Path:
    import pyarrow as pa
    import pyarrow.parquet as pq

    out_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(cw.rows), out_dir / "gn_memberships.parquet")
    if cw.unmatched:
        with (out_dir / "unmatched.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(cw.unmatched[0]))
            w.writeheader()
            w.writerows(cw.unmatched)
    path = out_dir / "qa.md"
    path.write_text(qa_markdown(cw), encoding="utf-8")
    return path
