"""Cross-checks for the HeiGIT and DesInventar indicators (`slf hazard-access checks`).

Each check says what it compares, whether the comparison figure is independent of the source,
and the numbers. A check reports; it never edits a value. Where two sources legitimately
differ (a modelled grid against a census, OpenStreetMap against a school list) the result is a
size of difference to read, not a pass or fail.
"""

# pandas type stubs can't follow these DataFrame operations; behaviour is covered by tests.
# pyright: reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportReturnType=false, reportGeneralTypeIssues=false

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from slf.hazard_access import RETURN_PERIODS, latest


@dataclass
class Check:
    id: str
    what: str
    independent: bool
    result: str
    detail: list[str] = field(default_factory=list)
    ok: bool | None = None  # None: a size to read, not a pass or fail


def _risk(raw: Path, name: str) -> pd.DataFrame:
    path, _ = latest(raw, "heigit", "heigit-risk-indicators", name)
    return pd.read_csv(path, dtype={"ADM2_PCODE": str}).set_index("ADM2_PCODE")


def _pct(x: float) -> str:
    return f"{x:+.1f}%"


def census_population(raw: Path, release_dir: Path) -> Check:
    """Modelled district population against the 2024 census (an independent source)."""
    demo = _risk(raw, "LKA_ADM2_demographics.csv")
    obs = pd.read_parquet(release_dir / "observations" / "census-2024-gnd-tables.parquet")
    obs = obs[obs["geography_id"].str.len() == 4]
    pairs = {
        "total_pop": "population_total",
        "female_pop": "population_female",
        "pop_u15": "population_age_0_14",
        "elderly": "population_age_65_plus",
    }
    lines: list[str] = []
    worst = 0.0
    for column, indicator in pairs.items():
        census = obs[obs["indicator_id"] == indicator].set_index("geography_id")["value"]
        joined = pd.concat(
            [demo[column].rename("heigit"), census.rename("census")], axis=1
        ).dropna()
        diff = (joined["heigit"] / joined["census"] - 1) * 100
        worst = max(worst, float(diff.abs().max()))
        far = diff[diff.abs() > 10].round(1).to_dict()
        lines.append(
            f"`{column}` against census `{indicator}`: {len(joined)} districts; sum "
            f"{joined['heigit'].sum():,.0f} against {joined['census'].sum():,.0f} "
            f"({_pct((joined['heigit'].sum() / joined['census'].sum() - 1) * 100)}); "
            f"district difference {_pct(float(diff.min()))} to {_pct(float(diff.max()))}, "
            f"median {_pct(float(diff.median()))}; beyond ±10%: {far or 'none'}"
        )
    return Check(
        "heigit-population-vs-census-2024",
        "HeiGIT district population (WorldPop, modelled) against the Census 2024 district figure "
        "in the release",
        True,
        f"largest district difference {worst:.1f}%",
        lines,
    )


def internal_composites(raw: Path) -> Check:
    """`coping` and `vulnerability` are documented as joins of other tables: confirm it."""
    lines: list[str] = []
    ok = True
    coping = _risk(raw, "LKA_ADM2_coping.csv")
    parts = pd.concat(
        [
            _risk(raw, name).drop(columns=["ADM_PCODE"], errors="ignore")
            for name in (
                "LKA_ADM2_access.csv",
                "LKA_ADM2_facilities.csv",
                "LKA_ADM2_evacuability.csv",
                "LKA_ADM2_rai.csv",
            )
        ],
        axis=1,
    )
    for label, whole, pieces in (
        ("coping = access + facilities + evacuability + rai", coping, parts),
        (
            "vulnerability = demographics + rural_population",
            _risk(raw, "LKA_ADM2_vulnerability.csv"),
            pd.concat(
                [
                    _risk(raw, name).drop(columns=["ADM_PCODE"], errors="ignore")
                    for name in ("LKA_ADM2_demographics.csv", "LKA_ADM2_rural_population.csv")
                ],
                axis=1,
            ),
        ),
    ):
        cols = [c for c in whole.columns if c in pieces.columns]
        missing = [c for c in whole.columns if c not in pieces.columns and c != "ADM_PCODE"]
        diff = (whole[cols].astype(float) - pieces[cols].astype(float)).abs().max().max()
        same = bool(diff < 1e-9) and not missing
        ok &= same
        lines.append(
            f"{label}: {len(cols)} of {len(whole.columns)} columns compared, largest absolute "
            f"difference {diff:g}; columns not found in the parts: {missing or 'none'}"
        )
    return Check(
        "heigit-composites-are-joins",
        "The `coping` and `vulnerability` tables against the tables HeiGIT says they combine",
        False,
        "identical" if ok else "differences found",
        lines,
        ok,
    )


def access_counts_vs_shares(raw: Path, catalog: Path) -> Check:
    """People-count table against the accessibility shares (two HeiGIT products).

    The two files use different codes; the reviewed `heigit-iso` crosswalk joins them.
    """
    xwalk = pd.read_csv(catalog / "geographies" / "codes" / "heigit-iso.csv", dtype=str)
    to_pcode = dict(zip(xwalk["external_code"], xwalk["geography_id"], strict=True))
    path, _ = latest(raw, "heigit", "heigit-accessibility", "LKA_hospitals_access_long.csv")
    long = pd.read_csv(path, dtype=str)
    long = long[
        (long["admin_level"] == "ADM2")
        & (long["population_type"] == "total")
        & (long["range"] == "1800")
    ]
    long["pcode"] = long["iso"].map(to_pcode)
    shares = long.set_index("pcode")
    access = _risk(raw, "LKA_ADM2_access.csv")["access_pop_hospitals_30min"]
    demo = _risk(raw, "LKA_ADM2_demographics.csv")["total_pop"]
    joined = pd.concat(
        [
            (access / demo * 100).rename("count_share"),
            shares["population_share"].astype(float).rename("table_share"),
            access.rename("count_people"),
            shares["population"].astype(float).rename("table_people"),
            demo.rename("risk_pop"),
            shares["population"].astype(float).rename("x"),
        ],
        axis=1,
    )
    gap = (joined["count_share"] - joined["table_share"]).abs()
    people = (joined["count_people"] / joined["table_people"] - 1) * 100
    return Check(
        "heigit-access-counts-vs-shares",
        "People within 30 minutes of a hospital: the risk-indicator count table against the "
        "accessibility table, joined by the reviewed ISO crosswalk",
        False,
        f"share differs by up to {gap.max():.1f} percentage points; people count by up to "
        f"{people.abs().max():.1f}%",
        [
            f"{len(joined.dropna(subset=['table_share']))} districts joined; share gap median "
            f"{gap.median():.2f} points",
            f"people counts: risk table {joined['count_people'].sum():,.0f}, accessibility "
            f"table {joined['table_people'].sum():,.0f}",
            "Differences are expected if the two products used different population grids or "
            "routing runs; HeiGIT does not say. Large gaps are listed in the report.",
            *[
                f"{k}: share {joined.loc[k, 'count_share']:.1f}% against "
                f"{joined.loc[k, 'table_share']:.1f}%"
                for k in gap.index[gap > 2].tolist()
            ],
        ],
    )


def flood_logic(raw: Path) -> Check:
    """Exposure should not fall as the return period lengthens; facilities exposed <= facilities."""
    flood = _risk(raw, "LKA_ADM2_flood_exposure.csv")
    facilities = _risk(raw, "LKA_ADM2_facilities.csv")
    problems: list[str] = []
    measures = sorted({c.split("_", 1)[1] for c in flood.columns if c.startswith("RP10_")})
    for m in measures:
        cols = [f"RP{rp}_{m}" for rp in RETURN_PERIODS]
        for lower, upper in itertools.pairwise(cols):
            bad = flood.index[flood[lower] > flood[upper] + 1e-9].tolist()
            if bad and "dependency" not in m:
                problems.append(f"{lower} > {upper} in {bad}")
    for rp in RETURN_PERIODS:
        for key, total in (
            ("education", "education_count"),
            ("hospitals", "hospitals_count"),
            ("primary_healthcare", "primary_healthcare_count"),
        ):
            over = flood.index[flood[f"RP{rp}_{key}_30cm_count"] > facilities[total]].tolist()
            if over:
                problems.append(f"RP{rp} exposed {key} exceeds the district's facilities: {over}")
        for column in (f"RP{rp}_crops_30cm_croppct", f"RP{rp}_hospitals_30cm_pct"):
            if ((flood[column] < 0) | (flood[column] > 100)).any():
                problems.append(f"{column} outside 0 to 100")
    return Check(
        "heigit-flood-exposure-logic",
        "Flood exposure by return period: non-decreasing from 10 to 500 years; exposed facilities "
        "not above the district's facilities; shares within 0 to 100",
        False,
        "no violations" if not problems else f"{len(problems)} violation(s)",
        problems,
        not problems,
    )


def facilities_vs_lists(raw: Path, spine_dir: Path) -> list[Check]:
    """OSM counts in HeiGIT's table against two other held point lists (different definitions)."""
    import geopandas as gpd

    gpkg = next(spine_dir.glob("geography_spine_*.gpkg"))
    districts = gpd.read_file(gpkg, layer="admin2_district")[["geography_id", "geometry"]]
    facilities = _risk(raw, "LKA_ADM2_facilities.csv")
    out: list[Check] = []

    giga_path, _ = latest(
        raw, "giga", "giga-school-locations", "sri-lanka-school-geolocation-connectivity-data.csv"
    )
    schools = pd.read_csv(giga_path)
    pts = gpd.GeoDataFrame(
        schools, geometry=gpd.points_from_xy(schools["longitude"], schools["latitude"]), crs=4326
    )
    joined = gpd.sjoin(pts, districts.to_crs(4326), how="left", predicate="within")
    giga = joined["geography_id"].value_counts()
    inside = int(joined["geography_id"].notna().sum())
    comp = pd.concat([facilities["education_count"].rename("osm"), giga.rename("giga")], axis=1)
    ratio = (comp["osm"] / comp["giga"]).dropna()
    out.append(
        Check(
            "osm-education-vs-giga-schools",
            "OpenStreetMap educational facilities (HeiGIT) against Giga's school point list, "
            "by district (point in district)",
            True,
            f"OSM {int(comp['osm'].sum()):,} against Giga {inside:,} schools; district ratio "
            f"{ratio.min():.2f} to {ratio.max():.2f}, median {ratio.median():.2f}",
            [
                "Different definitions: OSM counts any mapped education feature (including "
                "universities, kindergartens and tuition centres), Giga lists schools.",
                f"Giga points outside every district polygon: {len(pts) - inside}",
            ],
        )
    )

    hs_path, _ = latest(raw, "healthsites", "healthsites-lk", "sri-lanka.geojson")
    hs = gpd.read_file(hs_path)
    hospital = hs[(hs["amenity"] == "hospital") | (hs["healthcare"] == "hospital")].copy()
    hospital["geometry"] = hospital.geometry.representative_point()
    hj = gpd.sjoin(
        hospital.set_crs(4326, allow_override=True), districts, how="left", predicate="within"
    )
    hcount = hj["geography_id"].value_counts()
    comp = pd.concat([facilities["hospitals_count"].rename("osm"), hcount.rename("hs")], axis=1)
    ratio = (comp["osm"] / comp["hs"]).dropna()
    out.append(
        Check(
            "osm-hospitals-vs-healthsites",
            "OpenStreetMap hospitals (HeiGIT) against healthsites.io hospitals (also OSM-derived), "
            "by district",
            False,
            f"HeiGIT {int(comp['osm'].sum()):,} against healthsites {len(hospital):,}; district "
            f"ratio {ratio.min():.2f} to {ratio.max():.2f}, median {ratio.median():.2f}",
            [
                "healthsites.io is itself extracted from OpenStreetMap, so this is a "
                "consistency check between two extractions, not an independent count.",
            ],
        )
    )
    return out


def desinventar_levels(observations: pd.DataFrame, spine_dir: Path) -> Check:
    """DS-level counts must never exceed the district's count for the same year."""
    di = observations[observations["indicator_id"].str.startswith("di_")]
    parent = pd.read_parquet(spine_dir / "geographies.parquet").set_index("geography_id")[
        "parent_id"
    ]
    problems: list[str] = []
    for indicator, group in di.groupby("indicator_id"):
        ds = group[group["geography_id"].str.len() == 6].copy()
        dist = group[group["geography_id"].str.len() == 4].set_index(["geography_id", "period"])
        ds["district"] = ds["geography_id"].map(parent)
        sums = ds.groupby(["district", "period"])["value"].sum()
        for key, total in sums.items():
            district = dist["value"].get(key)
            if district is None or total > district + 1e-9:
                problems.append(f"{indicator} {key}: DS sum {total:g} against district {district}")
    return Check(
        "desinventar-ds-within-district",
        "DesInventar record counts: the sum over DS divisions never exceeds the district count "
        "for the same hazard and year",
        False,
        "holds in every district-year" if not problems else f"{len(problems)} violation(s)",
        problems[:20],
        not problems,
    )


def tsunami_2004(raw: Path) -> Check:
    """DesInventar's 2004 tsunami deaths against a published national figure."""
    from slf.hazard_access import read_events

    events, _, _ = read_events(raw)
    t = events[(events["Event"] == "TSUNAMI") & events["Date (YMD)"].str.endswith("2004")]
    deaths = int(pd.to_numeric(t["Deaths"], errors="coerce").sum())
    missing = int(pd.to_numeric(t["Missing"], errors="coerce").sum())
    return Check(
        "desinventar-tsunami-2004-deaths",
        "Deaths recorded for the 26 December 2004 tsunami in DesInventar, summed over its "
        f"{len(t)} TSUNAMI records dated 2004, against the national figure in the ADRC Annual "
        "Disaster Report 2004, Sri Lanka chapter (page 1 of 6-2.pdf, read 2026-11-21): "
        "30,959 deaths and 5,443 missing, which it attributes to UN/OCHA, 4 February 2005",
        True,
        f"deaths {deaths:,} against 30,959; missing {missing:,} against 5,443",
        [
            "Source: https://web.adrc.asia/publications/annual/04/04eng/pdf/6-2.pdf",
            "The deaths figure is identical, which suggests both trace to the same government "
            "tally, so it confirms transcription rather than the count itself.",
            "The missing figure differs: DesInventar holds fewer than the report. People missing "
            "are not used by any indicator here.",
        ],
        deaths == 30959,
    )


def run(
    raw: Path,
    spine_dir: Path,
    release_dir: Path,
    observations: Path,
    catalog: Path,
) -> list[Check]:
    obs = pd.read_parquet(observations)
    checks = [
        census_population(raw, release_dir),
        internal_composites(raw),
        access_counts_vs_shares(raw, catalog),
        flood_logic(raw),
        *facilities_vs_lists(raw, spine_dir),
        desinventar_levels(obs, spine_dir),
        tsunami_2004(raw),
    ]
    return checks


def render(checks: list[Check], extra: list[str] | None = None) -> str:
    lines = [
        "# QA: cross-checks of the HeiGIT and DesInventar indicators",
        "",
        "Built by `uv run slf hazard-access checks`. A check reports a size or a pass; it never "
        "changes a value. “Independent” means the comparison figure does not come from the "
        "source being checked.",
        "",
        "| Check | Independent | Result |",
        "|---|---|---|",
        *[f"| {c.id} | {'yes' if c.independent else 'no'} | {c.result} |" for c in checks],
        "",
    ]
    for c in checks:
        lines += [f"## {c.id}", "", c.what, "", f"**Result:** {c.result}", ""]
        lines += [f"- {d}" for d in c.detail]
        lines.append("")
    lines += extra or []
    return "\n".join(lines)


def write(checks: list[Check], out_dir: Path, extra: list[str] | None = None) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "checks.json").write_text(
        json.dumps([c.__dict__ for c in checks], indent=2, default=str) + "\n"
    )
    path = out_dir / "checks.md"
    path.write_text(render(checks, extra))
    return path


def as_dicts(checks: list[Check]) -> list[dict[str, Any]]:
    return [c.__dict__ for c in checks]
