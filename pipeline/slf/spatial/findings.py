"""Cross-dataset findings: what the new layers show when joined to the census by place.

Everything here is arithmetic on values already in the ledger (landscape observations and Census
2024 observations) plus one zonal sum of the WorldPop grid. Results go to ``findings.json`` for
the research note; they are analysis, not published indicators.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from slf.spatial import build as landscape
from slf.spatial import zonal


class GridSum:
    """Sum of a count raster per zone, sharing each cell between zones by sub-cell."""

    def __init__(self, n_zones: int, upsample: int, nodata: float) -> None:
        self.total = np.zeros(n_zones + 1)
        self.share = 1.0 / (upsample * upsample)
        self.nodata = nodata

    def __call__(self, labels: np.ndarray, arrays: list[np.ndarray], areas: np.ndarray) -> None:
        values = arrays[0]
        good = (labels > 0) & (values != self.nodata) & np.isfinite(values)
        self.total += np.bincount(
            labels[good],
            weights=values[good].astype(np.float64) * self.share,
            minlength=self.total.size,
        )


def _pick(obs: pd.DataFrame, indicator: str, period: str | None = None) -> pd.Series:
    rows: Any = obs[obs.indicator_id == indicator]
    if period is not None:
        rows = rows[rows.period == period]
    return rows.drop_duplicates("geography_id").set_index("geography_id").value


def _top(
    table: pd.DataFrame, by: str, names: dict[str, str], n: int = 10, ascending: bool = False
) -> list[dict[str, Any]]:
    out = table.sort_values(by, ascending=ascending).head(n).round(3).reset_index()
    out.insert(1, "name_en", out.geography_id.map(names))
    return out.to_dict("records")


def run(
    roots: list[Path], spine_dir: Path, landscape_dir: Path, census_gn: Path, census_topics: Path
) -> dict[str, Any]:
    geos = pd.read_parquet(spine_dir / "geographies.parquet")
    names = geos.set_index("geography_id").name_en.to_dict()
    level = geos.set_index("geography_id").level
    obs = pd.read_parquet(landscape_dir / "observations.parquet")
    census = pd.read_parquet(census_gn, columns=["indicator_id", "geography_id", "period", "value"])
    topics = pd.read_parquet(
        census_topics, columns=["indicator_id", "geography_id", "period", "value"]
    )
    pop: Any = _pick(census, "population_total")
    gn_ids = level[level == 4].index
    ds_ids = level[level == 3].index
    district_ids = level[level == 2].index
    out: dict[str, Any] = {}

    # 1. WorldPop 2025 (modelled) against Census 2024 (counted), by GN
    zones = landscape.load_zones(spine_dir)
    files = [
        f
        for f in landscape.held_files(roots, "worldpop", "worldpop-population-100m")
        if f.path.suffix == ".tif"
    ]
    if files:
        reducer = GridSum(len(zones), upsample=4, nodata=-99999.0)
        with landscape.open_raster(files[0]) as dataset:
            zonal.walk([dataset], zones, reducer, upsample=4)
        modelled = pd.Series(reducer.total[1:], index=zones.ids)
        both: Any = pd.DataFrame(
            {"census_2024": pop.reindex(zones.ids), "worldpop_2025": modelled}
        ).dropna()
        both = both[both.census_2024 > 0]
        ratio = both.worldpop_2025 / both.census_2024
        by_ds = both.groupby(both.index.str[:6]).sum()
        ds_ratio = by_ds.worldpop_2025 / by_ds.census_2024
        out["worldpop_vs_census"] = {
            "file": files[0].path.name,
            "sha256": files[0].sha256,
            "gn_compared": len(both),
            "census_2024_total_in_compared_gn": float(both.census_2024.sum()),
            "worldpop_2025_total_in_compared_gn": round(float(both.worldpop_2025.sum())),
            "worldpop_total_all_gn_polygons": round(float(modelled.sum())),
            "gn_correlation_log": round(
                float(
                    np.corrcoef(
                        np.log10(both.census_2024), np.log10(both.worldpop_2025.clip(lower=1))
                    )[0, 1]
                ),
                4,
            ),
            "gn_median_absolute_percent_difference": round(
                float((ratio - 1).abs().median() * 100), 1
            ),
            "gn_within_10_percent_share": round(float(((ratio - 1).abs() <= 0.10).mean() * 100), 1),
            "gn_within_25_percent_share": round(float(((ratio - 1).abs() <= 0.25).mean() * 100), 1),
            "gn_off_by_more_than_half_share": round(
                float(((ratio < 0.5) | (ratio > 1.5)).mean() * 100), 1
            ),
            "ds_median_absolute_percent_difference": round(
                float((ds_ratio - 1).abs().median() * 100), 1
            ),
            "ds_largest_overestimates": [
                {
                    "geography_id": g,
                    "name_en": names.get(g),
                    "worldpop_over_census": round(float(v), 2),
                }
                for g, v in ds_ratio.sort_values(ascending=False).head(6).items()
            ],
            "ds_largest_underestimates": [
                {
                    "geography_id": g,
                    "name_en": names.get(g),
                    "worldpop_over_census": round(float(v), 2),
                }
                for g, v in ds_ratio.sort_values().head(6).items()
            ],
        }

    # 2. Official urban sector against satellite-era settlement type
    urban_share = _pick(obs, "settlement_urban_share", "2020")
    centre_share = _pick(obs, "settlement_urban_centre_share", "2020")
    gn: Any = pd.DataFrame(
        {
            "pop": pop.reindex(gn_ids),
            "urban": urban_share.reindex(gn_ids),
            "centre": centre_share.reindex(gn_ids),
        }
    ).dropna()
    official_urban: Any = _pick(topics, "population_sector_urban")
    official_total = (
        official_urban
        + _pick(topics, "population_sector_rural")
        + _pick(topics, "population_sector_estate_rural")
    )
    districts: Any = pd.DataFrame(
        {
            "official_urban_share": (100 * official_urban / official_total).reindex(district_ids),
            "area_in_urban_cells_share": urban_share.reindex(district_ids),
        }
    )
    gn["district"] = gn.index.str[:4]
    weighted = gn.assign(u=gn["pop"] * gn.urban / 100).groupby("district")[["u", "pop"]].sum()
    districts["population_in_urban_cells_share_approx"] = 100 * weighted.u / weighted["pop"]
    districts["gap_points"] = (
        districts.population_in_urban_cells_share_approx - districts.official_urban_share
    )
    districts.index.name = "geography_id"
    out["urban_definitions"] = {
        "official_urban_population_share_LK": round(
            float(100 * official_urban.get("LK") / official_total.get("LK")), 2
        ),
        "census_population_weighted_by_gn_area_in_urban_centre_or_cluster_cells_share": round(
            float((gn["pop"] * gn.urban / 100).sum() / gn["pop"].sum() * 100), 1
        ),
        "census_population_weighted_by_gn_area_in_urban_centre_cells_share": round(
            float((gn["pop"] * gn.centre / 100).sum() / gn["pop"].sum() * 100), 1
        ),
        "census_population_in_gn_mostly_in_urban_cells_share": round(
            float(gn.loc[gn.urban > 50, "pop"].sum() / gn["pop"].sum() * 100), 1
        ),
        "method_note": "GN population spread evenly over the GN's area; an approximation, not a count",
        "districts": _top(districts, "gap_points", names, n=25),
    }

    # 3. Built-up growth 1975 -> 2020
    b75, b20 = (
        _pick(obs, "built_up_surface_area", "1975"),
        _pick(obs, "built_up_surface_area", "2020"),
    )
    s75, s20 = (
        _pick(obs, "built_up_surface_share", "1975"),
        _pick(obs, "built_up_surface_share", "2020"),
    )
    growth: Any = pd.DataFrame(
        {"built_1975_ha": b75, "built_2020_ha": b20, "share_1975": s75, "share_2020": s20}
    )
    growth["times"] = growth.built_2020_ha / growth.built_1975_ha
    growth["added_ha"] = growth.built_2020_ha - growth.built_1975_ha
    growth.index.name = "geography_id"
    out["built_up_growth"] = {
        "LK": growth.loc["LK"].round(3).to_dict(),
        "districts_by_multiple": _top(growth.reindex(district_ids), "times", names, n=25),
        "ds_most_added_ha": _top(growth.reindex(ds_ids), "added_ha", names),
        "ds_highest_share_2020": _top(growth.reindex(ds_ids), "share_2020", names),
    }

    # 4. Tree cover loss
    loss: Any = pd.DataFrame(
        {
            "cover_2000_ha": _pick(obs, "tree_cover_2000_area", "2000"),
            "loss_ha": _pick(obs, "tree_cover_loss_total_area", "2024"),
            "loss_share": _pick(obs, "tree_cover_loss_total_share", "2024"),
        }
    )
    loss.index.name = "geography_id"
    yearly = obs[(obs.indicator_id == "tree_cover_loss_area") & obs.geography_id.isin(district_ids)]
    peak = yearly.loc[yearly.groupby("geography_id").value.idxmax()].set_index("geography_id")
    loss["peak_year"] = peak.period
    out["tree_cover_loss"] = {
        "districts": _top(loss.reindex(district_ids), "loss_share", names, n=25),
        "ds_highest_share": _top(
            loss.reindex(ds_ids)[lambda d: d.cover_2000_ha >= 1000], "loss_share", names
        ),
        "ds_most_ha": _top(loss.reindex(ds_ids), "loss_ha", names),
    }

    # 5. Distance to schools and mapped health facilities, weighted by census population
    school = _pick(obs, "nearest_school_distance").reindex(gn_ids)
    clinic = _pick(obs, "nearest_health_facility_distance").reindex(gn_ids)
    people = pop.reindex(gn_ids)
    ok = people.notna() & school.notna()

    def beyond(distance: pd.Series, km: float) -> float:
        return round(float(people[ok & (distance > km)].sum() / people[ok].sum() * 100), 2)

    far = (
        pd.DataFrame({"km": school, "population_2024": people})
        .dropna()
        .sort_values("km", ascending=False)
    )
    far.index.name = "geography_id"
    out["distance_to_school"] = {
        "basis": "straight line from the GN label point; census 2024 population of the GN",
        "population_share_in_gn_beyond_2km": beyond(school, 2),
        "population_share_in_gn_beyond_5km": beyond(school, 5),
        "gn_beyond_5km": int((school > 5).sum()),
        "farthest_gn": _top(far, "km", names, n=10),
        "health_population_share_in_gn_beyond_5km_of_mapped_facility": beyond(clinic, 5),
        "health_population_share_in_gn_beyond_10km_of_mapped_facility": beyond(clinic, 10),
    }

    # 6. Listed places per 1,000 residents
    listed: Any = _pick(obs, "places_listed")
    dens: Any = pd.DataFrame(
        {"places": listed.reindex(ds_ids), "population_2024": pop.reindex(ds_ids)}
    ).dropna()
    dens["per_1000"] = 1000 * dens.places / dens.population_2024
    dens.index.name = "geography_id"
    lodging = _pick(obs, "places_listed_lodging").reindex(dens.index)
    dens["lodging_share"] = 100 * lodging / dens.places
    out["places_listed"] = {
        "LK_per_1000": round(float(1000 * listed.get("LK") / pop.get("LK")), 2),
        "ds_highest_per_1000": _top(dens, "per_1000", names),
        "ds_lowest_per_1000": _top(dens, "per_1000", names, ascending=True),
        "ds_highest_lodging_share": _top(dens[dens.places >= 100], "lodging_share", names),
    }
    # 7. Mapped building footprints against census-occupied housing units
    footprints: Any = _pick(obs, "buildings_mapped")
    if len(footprints):
        units: Any = _pick(census, "occupied_housing_units")
        gnb: Any = pd.DataFrame(
            {"buildings": footprints.reindex(gn_ids), "housing_units": units.reindex(gn_ids)}
        ).dropna()
        gnb = gnb[gnb.housing_units > 0]
        per_unit = gnb.buildings / gnb.housing_units
        dist: Any = pd.DataFrame(
            {
                "buildings": footprints.reindex(district_ids),
                "housing_units": units.reindex(district_ids),
            }
        )
        dist["buildings_per_housing_unit"] = dist.buildings / dist.housing_units
        dist.index.name = "geography_id"
        out["buildings_vs_housing_units"] = {
            "gn_compared": len(gnb),
            "buildings_in_compared_gn": int(gnb.buildings.sum()),
            "occupied_housing_units_in_compared_gn": int(gnb.housing_units.sum()),
            "buildings_per_occupied_housing_unit": round(
                float(gnb.buildings.sum() / gnb.housing_units.sum()), 3
            ),
            "gn_percentiles_1_5_25_50_75_95_99": [
                round(float(v), 2) for v in np.percentile(per_unit, [1, 5, 25, 50, 75, 95, 99])
            ],
            "gn_share_with_fewer_buildings_than_housing_units": round(
                float((per_unit < 1).mean() * 100), 1
            ),
            "districts": _top(dist, "buildings_per_housing_unit", names, n=25, ascending=True),
        }
    (landscape_dir / "findings.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    return out
