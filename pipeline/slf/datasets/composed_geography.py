"""GN-composed geographies (G05, SCHEME la and health): local authorities and MOH areas.

Neither scheme nests in the administrative hierarchy: a unit is a set of GN divisions. This
module turns a **unit list** and a **membership list** (GN code -> unit code, optional weight)
into the scheme's ids, codes, ``composed_of`` relations, checks and Census 2024 denominators,
the same way ``electoral_geography`` does for electoral districts.

Inputs are two plain tables, so any source can be used once its rights are recorded:

- units: ``unit_code,name[,kind]`` (kind: for local authorities ``MC``, ``UC`` or ``PS``);
- membership: ``gn_code,unit_code[,weight]`` (weight defaults to 1; a GN split across units
  has one row per unit, and its weights should sum to 1).

GN codes join to the spine through a crosswalk file in ``catalog/geographies/codes/`` (rule 5);
names are never used to join. Every row that does not resolve is written to a QA file (rule 6).

Rights gate (rule 4): codes and relations are written to ``catalog/`` only when the membership
dataset's rights allow publication (``open`` / ``permitted_with_conditions``, or ``unclear``
with an Accepted publication decision). Otherwise every output stays in the build folder with
``internal`` in its name, as for polling divisions (D-040).

As of 2026-11-17 no local authority or MOH list with recorded, usable rights is held. The only
held membership is nuuuwan's ``gig-data`` (``lg_id`` and ``moh_id`` per GN; no licence, no
stated origin), which is read for an internal run only.
"""

from __future__ import annotations

import io
import urllib.error
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import pandas as pd

from slf.catalog import CatalogReport, effective_rights, load_catalog, load_decisions
from slf.datasets.electoral_geography import (
    DENOMINATORS,
    GIG_DATASET,
    Composition,
    _census_gn,
    _dist,
    _with_adults,
    denominators,
    iou_table,
    read_geojson,
    read_tsv,
    snapshot_gig,
    weight_sums,
)
from slf.storage import Storage

LA_TYPE_INDICATORS = {
    "MC": "population_local_authority_municipal_council",
    "UC": "population_local_authority_urban_council",
    "PS": "population_local_authority_pradeshiya_sabha",
}


@dataclass(frozen=True)
class SchemeSpec:
    scheme: str
    level: str
    id_prefix: str
    unit_label: str
    gig_column: str
    gig_file: str
    gig_prefix: str


SCHEMES: dict[str, SchemeSpec] = {
    "la": SchemeSpec("la", "local_authority", "LK-LA-", "local authority", "lg_id", "lg", "LG-"),
    "health": SchemeSpec("health", "moh", "LK-MOH-", "MOH area", "moh_id", "moh", "MOH-"),
}


@dataclass(frozen=True)
class Unit:
    code: str
    name: str
    kind: str | None = None


@dataclass(frozen=True)
class Member:
    gn_code: str
    unit_code: str
    weight: float = 1.0


def unit_id(spec: SchemeSpec, code: str) -> str:
    return f"{spec.id_prefix}{code}"


def la_kind(name: str) -> str | None:
    """Local authority type from a name ending in MC, UC or PS; None when it has no such ending."""
    last = name.strip().rsplit(" ", 1)[-1].upper()
    return last if last in LA_TYPE_INDICATORS else None


def read_units(path: Path) -> list[Unit]:
    frame = pd.read_csv(path, dtype=str).fillna("")
    missing = {"unit_code", "name"} - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    return [
        Unit(str(r["unit_code"]).strip(), str(r["name"]).strip(), str(r.get("kind") or "") or None)
        for r in cast(list[dict[str, Any]], frame.to_dict("records"))
    ]


def read_membership(path: Path) -> list[Member]:
    frame = pd.read_csv(path, dtype=str).fillna("")
    missing = {"gn_code", "unit_code"} - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns {sorted(missing)}")
    return [
        Member(
            str(r["gn_code"]).strip(),
            str(r["unit_code"]).strip(),
            float(r["weight"]) if r.get("weight") else 1.0,
        )
        for r in cast(list[dict[str, Any]], frame.to_dict("records"))
    ]


def read_crosswalk(catalog: Path, code_system: str) -> dict[str, str] | None:
    """External GN code -> spine id from ``codes/<code_system>.csv``; None = p-codes."""
    if code_system == "pcode":
        return None
    frame = pd.read_csv(catalog / "geographies" / "codes" / f"{code_system}.csv", dtype=str)
    return dict(zip(frame["external_code"], frame["geography_id"], strict=False))


@dataclass
class Composed:
    spec: SchemeSpec
    units: dict[str, Unit]
    composition: Composition
    #: membership rows whose GN code is not in the crosswalk or not a spine GN
    unmatched_gn: list[Member] = field(default_factory=list)
    #: membership rows with an empty unit code (the source assigns the GN to no unit)
    unassigned: list[Member] = field(default_factory=list)
    #: membership rows naming a unit that is not in the unit list
    unknown_unit: list[Member] = field(default_factory=list)
    duplicates: list[Member] = field(default_factory=list)


def compose(
    spec: SchemeSpec,
    units: Iterable[Unit],
    members: Iterable[Member],
    crosswalk: Mapping[str, str] | None,
    spine_gns: set[str],
    *,
    method: str,
    source: str,
    empty_codes: Iterable[str] = ("", "None", "nan"),
) -> Composed:
    """Resolve a membership list to unit id -> {spine GN id: weight}; nothing dropped silently."""
    unit_map = {u.code: u for u in units}
    empty = set(empty_codes)
    out = Composed(spec, unit_map, Composition(defaultdict(dict), method, source))
    seen: set[tuple[str, str]] = set()
    for m in members:
        if m.unit_code in empty:
            out.unassigned.append(m)
            continue
        if m.unit_code not in unit_map:
            out.unknown_unit.append(m)
            continue
        gn = m.gn_code if crosswalk is None else crosswalk.get(m.gn_code)
        if gn is None or gn not in spine_gns:
            out.unmatched_gn.append(m)
            continue
        if (gn, m.unit_code) in seen:
            out.duplicates.append(m)
            continue
        seen.add((gn, m.unit_code))
        out.composition.members[unit_id(spec, m.unit_code)][gn] = m.weight
    return out


def split_gns(comp: Composition) -> dict[str, list[str]]:
    """GNs that belong to more than one unit, with the units."""
    owners: dict[str, list[str]] = defaultdict(list)
    for unit, gns in comp.members.items():
        for gn in gns:
            owners[gn].append(unit)
    return {gn: sorted(units) for gn, units in owners.items() if len(units) > 1}


def units_without_gn(composed: Composed) -> list[str]:
    return sorted(
        unit_id(composed.spec, code)
        for code in composed.units
        if not composed.composition.members.get(unit_id(composed.spec, code))
    )


def code_rows(composed: Composed, vintage: str, code_system: str) -> list[dict[str, object]]:
    return [
        {
            "geography_id": unit_id(composed.spec, u.code),
            "vintage": vintage,
            "code_system": code_system,
            "external_code": u.code,
            "external_name": u.name,
            "match_method": "exact_code",
            "confidence": 1.0,
            "notes": f"kind {u.kind}" if u.kind else None,
        }
        for u in sorted(composed.units.values(), key=lambda u: u.code)
    ]


def relation_rows(composed: Composed, vintage: str, method: str) -> list[dict[str, object]]:
    return [
        {
            "geography_id": unit,
            "related_id": gn,
            "relation": "composed_of",
            "vintage": vintage,
            "weight": weight,
            "method": method,
            "source": composed.composition.source,
            "valid_from": None,
            "valid_to": None,
            "notes": None,
        }
        for unit, gns in sorted(composed.composition.members.items())
        for gn, weight in sorted(gns.items())
    ]


def rights_allow_catalog(catalog: Path, dataset_id: str) -> tuple[bool, str]:
    """Whether a dataset's recorded rights let its composition be committed and published."""
    report = CatalogReport()
    cat = load_catalog(catalog, None, report)
    ds = cat.datasets.get(dataset_id)
    if ds is None:
        return False, f"dataset {dataset_id!r} is not in the catalogue"
    rights = effective_rights(cat, ds)
    if rights is None:
        return False, f"dataset {dataset_id!r} has no rights recorded"
    if rights.status in ("open", "permitted_with_conditions"):
        return True, f"rights {rights.status} ({rights.licence or 'no licence name'})"
    if rights.status == "unclear" and ds.publication is not None:
        decisions = load_decisions(catalog.parent / "docs" / "decisions" / "decision-log.md") or {}
        if decisions.get(ds.publication.decision) == "Accepted":
            return True, f"rights unclear; publication decision {ds.publication.decision} Accepted"
    return False, f"rights {rights.status}; internal run only, nothing committed"


def publication_text(catalog: Path, dataset_id: str) -> tuple[str | None, str | None]:
    """The attribution and notice of a dataset's publication block, if it has one."""
    cat = load_catalog(catalog, None, CatalogReport())
    ds = cat.datasets.get(dataset_id)
    if ds is None or ds.publication is None:
        return None, None
    return ds.publication.attribution, ds.publication.notice


def la_type_check(composed: Composed, census: pd.DataFrame) -> pd.DataFrame:
    """Per local authority: census population of its GNs by DCS local-authority type.

    DCS's GN table says how many people in each GN live under a municipal council, an urban
    council or a pradeshiya sabha. A unit whose name says MC should hold mostly MC population.
    This is an official, independent check of a membership list (G05 step 4).
    """
    wanted = list(LA_TYPE_INDICATORS.values())
    values = census[census["indicator_id"].isin(wanted)].pivot_table(
        index="geography_id", columns="indicator_id", values="value", aggfunc="first"
    )
    rows = []
    for code, unit in sorted(composed.units.items()):
        members = composed.composition.members.get(unit_id(composed.spec, code), {})
        ids = [g for g in members if g in values.index]
        sums = {
            kind: float(sum(members[g] * float(values.at[g, ind]) for g in ids))
            if ind in values.columns
            else 0.0
            for kind, ind in LA_TYPE_INDICATORS.items()
        }
        total = sum(sums.values())
        kind = unit.kind or la_kind(unit.name)
        rows.append(
            {
                "geography_id": unit_id(composed.spec, code),
                "kind": kind,
                **{f"population_{k.lower()}": v for k, v in sums.items()},
                "share_in_own_kind": round(sums[kind] / total, 4) if kind and total else None,
            }
        )
    return pd.DataFrame(rows)


@dataclass
class ComposedBuild:
    outputs: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    qa: str = ""
    committed: bool = False
    summary: dict[str, Any] = field(default_factory=dict)


def spine_gn_ids(spine_dir: Path) -> set[str]:
    geos = pd.read_parquet(spine_dir / "geographies.parquet", columns=["geography_id", "level"])
    return {str(g) for g in geos.loc[geos["level"] == 4, "geography_id"]}


def build(
    composed: Composed,
    *,
    vintage: str,
    code_system: str,
    relation_method: str,
    spine_dir: Path,
    census_dirs: list[Path],
    catalog: Path,
    out_dir: Path,
    publishable: bool,
    rights_note: str,
    unit_geoms: Mapping[str, object] | None = None,
    published_totals: Mapping[str, float] | None = None,
    published_label: str = "published population",
) -> ComposedBuild:
    """Run G05's checks and denominators for one GN-composed scheme and write the QA report."""
    spec = composed.spec
    res = ComposedBuild()
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = "" if publishable else "_internal"
    all_gns = spine_gn_ids(spine_dir)
    comp = composed.composition

    ws = weight_sums(comp, all_gns)
    splits = split_gns(comp)
    empty_units = units_without_gn(composed)
    census = _census_gn(census_dirs, all_gns)
    den = _with_adults(denominators(comp, census, DENOMINATORS))
    names = {unit_id(spec, c): u.name for c, u in composed.units.items()}
    if not den.empty:
        den.insert(1, "name", [names.get(str(g)) for g in den["geography_id"]])
    if published_totals is not None and not den.empty:
        den["published_total"] = [published_totals.get(str(g)) for g in den["geography_id"]]
        den["difference"] = den["population_total"] - den["published_total"]

    frames: dict[str, pd.DataFrame] = {
        f"{spec.scheme}_denominators{tag}.csv": den,
        f"{spec.scheme}_unmatched_gn{tag}.csv": pd.DataFrame(
            [m.__dict__ for m in composed.unmatched_gn], columns=["gn_code", "unit_code", "weight"]
        ),
        f"{spec.scheme}_unassigned_gn{tag}.csv": pd.DataFrame(
            [m.__dict__ for m in composed.unassigned], columns=["gn_code", "unit_code", "weight"]
        ),
        f"{spec.scheme}_unknown_unit{tag}.csv": pd.DataFrame(
            [m.__dict__ for m in composed.unknown_unit], columns=["gn_code", "unit_code", "weight"]
        ),
        f"{spec.scheme}_split_gn{tag}.csv": pd.DataFrame(
            [{"gn": gn, "units": ";".join(units)} for gn, units in sorted(splits.items())],
            columns=["gn", "units"],
        ),
    }
    covered = {gn for gns in comp.members.values() for gn in gns}
    frames[f"{spec.scheme}_spine_gn_without_unit{tag}.csv"] = pd.DataFrame(
        {"gn": sorted(all_gns - covered)}
    )

    iou: pd.DataFrame | None = None
    if unit_geoms:
        versions = gpd.read_parquet(spine_dir / "geography_versions.geoparquet")
        gn_geoms = versions[versions["level"] == 4].set_index("geography_id")["geometry"]
        iou = iou_table(unit_geoms, gpd.GeoSeries(gn_geoms, crs=versions.crs), comp)
        frames[f"{spec.scheme}_iou{tag}.csv"] = iou

    kinds: pd.DataFrame | None = None
    if spec.scheme == "la":
        kinds = la_type_check(composed, census)
        frames[f"{spec.scheme}_census_type_check{tag}.csv"] = kinds

    if publishable:
        codes = catalog / "geographies" / "codes" / f"{spec.scheme}-{vintage}.csv"
        rels = catalog / "geographies" / "relations" / f"{spec.scheme}_{vintage}.csv"
        pd.DataFrame(code_rows(composed, vintage, code_system)).to_csv(codes, index=False)
        pd.DataFrame(relation_rows(composed, vintage, relation_method)).to_csv(rels, index=False)
        res.outputs += [codes, rels]
        res.committed = True
    else:
        frames[f"{spec.scheme}_relations{tag}.csv"] = pd.DataFrame(
            relation_rows(composed, vintage, relation_method)
        )

    for name, frame in frames.items():
        path = out_dir / name
        frame.to_csv(path, index=False)
        res.outputs.append(path)

    res.summary = {
        "scheme": spec.scheme,
        "vintage": vintage,
        "units_listed": len(composed.units),
        "units_with_gn": sum(bool(m) for m in comp.members.values()),
        "units_without_gn": len(empty_units),
        "spine_gns": len(all_gns),
        "gns_covered": len(covered),
        "weight_sums": {str(k): v for k, v in sorted(ws.items())},
        "split_gns": len(splits),
        "unmatched_gn_rows": len(composed.unmatched_gn),
        "unassigned_gn_rows": len(composed.unassigned),
        "unknown_unit_rows": len(composed.unknown_unit),
        "duplicate_rows": len(composed.duplicates),
        "population_sum": float(den["population_total"].to_numpy().sum()) if not den.empty else 0.0,
        "publishable": publishable,
    }
    res.qa = _qa(
        composed, res.summary, rights_note, den, iou, kinds, empty_units, census, covered,
        published_totals is not None, published_label,
    )  # fmt: skip
    qa = out_dir / "qa.md"
    qa.write_text(res.qa, encoding="utf-8")
    res.outputs.append(qa)
    return res


def _qa(composed, s, rights_note, den, iou, kinds, empty_units, census, covered,
        has_published, published_label) -> str:  # fmt: skip
    spec = composed.spec
    pop = census[census["indicator_id"] == "population_total"]
    spine_pop = float(pop["value"].sum())
    uncovered_pop = float(pop.loc[~pop["geography_id"].isin(sorted(covered)), "value"].sum())
    status = (
        "publishable (codes and relations written to catalog/)"
        if s["publishable"]
        else "INTERNAL ONLY (nothing committed; unit-level files stay in the build folder)"
    )
    lines = [
        f"# QA: {spec.unit_label} composition (G05, scheme `{spec.scheme}`, "
        f"vintage {s['vintage']})",
        "",
        f"Status: **{status}**. Rights: {rights_note}. Composition method: "
        f"{composed.composition.method}; source dataset: `{composed.composition.source}`.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "|---|---|",
        f"| Units in the unit list | {s['units_listed']} |",
        f"| Units with at least one matched GN | {s['units_with_gn']} |",
        f"| Units with no GN | {s['units_without_gn']} |",
        f"| Spine GNs (COD-AB v03) | {s['spine_gns']} |",
        f"| Spine GNs covered by a unit | {s['gns_covered']} |",
        f"| Membership rows whose GN code did not match the spine | {s['unmatched_gn_rows']} |",
        f"| Membership rows with no unit (GN left unassigned) | {s['unassigned_gn_rows']} |",
        f"| Membership rows naming a unit not in the unit list | {s['unknown_unit_rows']} |",
        f"| Repeated (GN, unit) rows ignored | {s['duplicate_rows']} |",
        f"| GNs split across more than one unit | {s['split_gns']} |",
        "",
        "## Weight sums per spine GN",
        "",
        f"{s['weight_sums']} (expected 1.0 for every GN; 0.0 means the GN is in no unit).",
        "",
        "## Census 2024 denominators",
        "",
        f"Population summed over units: {int(s['population_sum']):,}. Population of all spine GNs "
        f"with a census value: {int(spine_pop):,}. Population in GNs that are in no unit: "
        f"{int(uncovered_pop):,}. GNs the DCS crosswalk does not match to the spine are in "
        "neither figure (see the census QA).",
        "",
        f"- Unit population: {_dist(den['population_total']) if not den.empty else 'n/a'}",
        f"- GNs per unit: {_dist(den['gn_members']) if not den.empty else 'n/a'}",
    ]
    if empty_units:
        shown = ", ".join(empty_units[:20]) if s["publishable"] else f"{len(empty_units)} units"
        lines += ["", f"Units with no GN: {shown}."]
    if has_published and not den.empty:
        d = den.dropna(subset=["published_total"]).copy()
        d["abs"] = d["difference"].abs()
        lines += [
            "",
            f"## Against {published_label}",
            "",
            f"Units compared: {len(d)}. Absolute difference: {_dist(d['abs'])}. "
            f"Relative difference (% of published): "
            f"{_dist((100 * d['difference'] / d['published_total']).round(2))}.",
        ]
        if s["publishable"]:
            lines += ["", "| unit | census sum | published | difference |", "|---|---|---|---|"]
            for r in d.sort_values("abs", ascending=False).head(10).to_dict("records"):
                lines.append(
                    f"| {r['geography_id']} | {int(r['population_total']):,} | "
                    f"{int(r['published_total']):,} | {int(r['difference']):,} |"
                )
    if iou is not None:
        lines += [
            "",
            "## IoU: unit shape vs union of its member GNs (EPSG:5235)",
            "",
            f"- {_dist(iou['iou'])}",
            f"- Units with IoU < 0.9: {int((iou['iou'] < 0.9).sum())}; < 0.8: "
            f"{int((iou['iou'] < 0.8).sum())}; no shape or no GN: {int(iou['iou'].isna().sum())}",
        ]
    if kinds is not None:
        k = kinds.dropna(subset=["share_in_own_kind"])
        by_kind = Counter(str(v) for v in kinds["kind"].fillna("unknown"))
        lines += [
            "",
            "## Against DCS's local-authority type per GN (official, independent)",
            "",
            "DCS's Census 2024 GN table gives each GN's population by local authority type "
            "(municipal council, urban council, pradeshiya sabha). For each unit, the share of "
            "its members' population that DCS puts under the unit's own type:",
            "",
            f"- Units by type in the unit list: {dict(sorted(by_kind.items()))}",
            f"- Share in own type: {_dist(k['share_in_own_kind'])}",
            f"- Units below 0.9: {int((k['share_in_own_kind'] < 0.9).sum())}; below 0.5: "
            f"{int((k['share_in_own_kind'] < 0.5).sum())}",
        ]
    return "\n".join(lines) + "\n"


# --- internal run on nuuuwan gig-data (no licence: never committed, never released) ----------


#: shape files the last gig_inputs call could not fetch (reported in the CLI output and QA)
missing_shapes: list[str] = []


def gig_inputs(
    storage: Storage, spec: SchemeSpec, *, with_geometry: bool
) -> tuple[list[Unit], list[Member], dict[str, object], dict[str, float]]:
    """Units, membership, shapes and nuuuwan's own unit populations from gig-data (internal)."""
    refs = snapshot_gig(storage, ["ents/gnd.tsv", f"ents/{spec.gig_file}.tsv"])
    gnd = read_tsv(storage, refs["ents/gnd.tsv"])
    ents = read_tsv(storage, refs[f"ents/{spec.gig_file}.tsv"])
    strip = len(spec.gig_prefix)
    units = [
        Unit(str(i)[strip:], str(n), la_kind(str(n)) if spec.scheme == "la" else None)
        for i, n in zip(ents["id"], ents["name"], strict=True)
    ]
    members = [
        Member(str(g), "" if str(u) in ("None", "nan", "") else str(u)[strip:])
        for g, u in zip(gnd["id"], gnd[spec.gig_column], strict=True)
    ]
    totals = {
        unit_id(spec, str(i)[strip:]): float(p)
        for i, p in zip(ents["id"], ents["population"], strict=True)
        if str(p) not in ("None", "nan", "")
    }
    geoms: dict[str, object] = {}
    missing_shapes.clear()
    if with_geometry:
        paths = [f"geo/{spec.gig_file}/{i}.json" for i in ents["id"]]
        for i, path in zip(ents["id"], paths, strict=True):
            try:
                ref = snapshot_gig(storage, [path])[path]
            except urllib.error.HTTPError as exc:
                # A missing upstream shape is reported (IoU "no shape"), never invented.
                missing_shapes.append(f"{path}: HTTP {exc.code}")
                continue
            geoms[unit_id(spec, str(i)[strip:])] = read_geojson(storage, ref)
    return units, members, geoms, totals


def units_csv(units: Iterable[Unit]) -> str:
    buffer = io.StringIO()
    pd.DataFrame([u.__dict__ for u in units]).rename(columns={"code": "unit_code"}).to_csv(
        buffer, index=False
    )
    return buffer.getvalue()


GIG_SOURCE_DATASET = GIG_DATASET
# Catalogue entry for the lg_id / moh_id memberships alone (D-057); the rights gate reads it.
GIG_LG_MOH_DATASET = "nuuuwan-gig-data-lg-moh"
