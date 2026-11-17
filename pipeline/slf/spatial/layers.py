"""The raster layers behind the landscape indicators: what is read, and what it becomes.

One place holds the facts the build, the catalogue and the method note all need: which dataset
each indicator comes from, its unit, its time footprint and its information floor.
"""

from __future__ import annotations

from dataclasses import dataclass

HA = 10_000.0  # m² per hectare

# ESA WorldCover v200 class values -> our class slugs
WORLDCOVER_CLASSES: dict[int, tuple[str, str]] = {
    10: ("tree", "Tree cover"),
    20: ("shrubland", "Shrubland"),
    30: ("grassland", "Grassland"),
    40: ("cropland", "Cropland"),
    50: ("built_up", "Built-up"),
    60: ("bare", "Bare or sparse vegetation"),
    80: ("water", "Permanent water bodies"),
    90: ("wetland", "Herbaceous wetland"),
    95: ("mangrove", "Mangroves"),
}

# GHS-SMOD (degree of urbanisation, level 2) class values -> groups
SMOD_GROUPS: dict[int, str] = {
    30: "urban_centre",
    23: "urban_cluster",
    22: "urban_cluster",
    21: "urban_cluster",
    13: "rural",
    12: "rural",
    11: "rural",
    10: "water",
}

GHSL_EPOCHS = tuple(range(1975, 2021, 5))
LOSS_YEARS = tuple(range(2001, 2025))


@dataclass(frozen=True)
class IndicatorSpec:
    id: str
    name: str
    dataset: str
    measure_type: str  # count | share | mean | ratio
    unit: str
    decimals: int
    definition: str
    topic: tuple[str, ...] = ("landscape",)
    numerator: str | None = None
    denominator: str | None = None
    aggregation: str = "sum"
    universe: str = "land_area_measured"
    higher_is: str = "neutral"
    distribution: str = "api"


def _area(id_: str, name: str, dataset: str, definition: str, **kw) -> IndicatorSpec:
    return IndicatorSpec(id_, name, dataset, "count", "hectares", 1, definition, **kw)


def _share(id_: str, name: str, dataset: str, num: str, den: str, definition: str, **kw):
    return IndicatorSpec(
        id_,
        name,
        dataset,
        "share",
        "percent",
        2,
        definition,
        numerator=num,
        denominator=den,
        aggregation="recompute_from_components",
        **kw,
    )


def indicator_specs() -> list[IndicatorSpec]:
    s: list[IndicatorSpec] = []
    dem = "copernicus-dem-glo30"
    s += [
        _area(
            "terrain_measured_area",
            "Area with elevation data",
            dem,
            "Ground area of the place covered by Copernicus DEM GLO-30 pixels whose centre falls "
            "inside its boundary. The denominator for terrain shares.",
        ),
        IndicatorSpec(
            "elevation_mean",
            "Mean elevation",
            dem,
            "mean",
            "metres",
            1,
            "Area-weighted mean height above the EGM2008 geoid of the 30 m surface-model pixels "
            "inside the place. A surface model includes buildings and tree canopy.",
            aggregation="none",
        ),
        IndicatorSpec(
            "elevation_min",
            "Lowest elevation",
            dem,
            "mean",
            "metres",
            1,
            "Lowest 30 m surface-model pixel inside the place.",
            aggregation="none",
        ),
        IndicatorSpec(
            "elevation_max",
            "Highest elevation",
            dem,
            "mean",
            "metres",
            1,
            "Highest 30 m surface-model pixel inside the place.",
            aggregation="none",
        ),
        IndicatorSpec(
            "slope_mean",
            "Mean slope",
            dem,
            "mean",
            "degrees",
            2,
            "Area-weighted mean slope of the 30 m surface model, from central differences "
            "between neighbouring pixels.",
            aggregation="none",
        ),
        _area(
            "steep_land_area",
            "Steep land (slope over 15°)",
            dem,
            "Ground area where the 30 m surface-model slope exceeds 15 degrees.",
        ),
        _share(
            "steep_land_share",
            "Steep land share (slope over 15°)",
            dem,
            "steep_land_area",
            "terrain_measured_area",
            "Share of the place's measured area where the 30 m surface-model slope exceeds "
            "15 degrees.",
        ),
    ]
    wc = "esa-worldcover-2021"
    s.append(
        _area(
            "land_cover_mapped_area",
            "Area with land-cover data",
            wc,
            "Ground area of the place covered by classified ESA WorldCover 2021 pixels. The "
            "denominator for land-cover shares.",
        )
    )
    for slug, label in WORLDCOVER_CLASSES.values():
        s.append(
            _area(
                f"land_cover_{slug}_area",
                f"Land cover: {label.lower()}",
                wc,
                f"Ground area classified as '{label}' in ESA WorldCover 2021 (10 m pixels, "
                "Sentinel-1 and Sentinel-2). A satellite classification, not a land-use survey.",
            )
        )
        s.append(
            _share(
                f"land_cover_{slug}_share",
                f"Land cover share: {label.lower()}",
                wc,
                f"land_cover_{slug}_area",
                "land_cover_mapped_area",
                f"Share of the place's mapped area classified as '{label}' in ESA WorldCover 2021.",
            )
        )
    gfc = "hansen-global-forest-change"
    s += [
        _area(
            "forest_measured_area",
            "Area with tree-cover data",
            gfc,
            "Ground area of the place covered by Global Forest Change pixels. The denominator "
            "for the tree-cover share.",
        ),
        _area(
            "tree_cover_2000_area",
            "Tree cover in 2000 (canopy 30% or more)",
            gfc,
            "Ground area of 30 m pixels with tree canopy cover of 30% or more in the year 2000 "
            "(vegetation taller than 5 m). Includes plantations such as rubber, coconut and "
            "shade trees; it is not a map of natural forest.",
            topic=("landscape", "change"),
        ),
        _share(
            "tree_cover_2000_share",
            "Tree cover share in 2000",
            gfc,
            "tree_cover_2000_area",
            "forest_measured_area",
            "Share of the place with tree canopy cover of 30% or more in 2000.",
            topic=("landscape", "change"),
        ),
        _area(
            "tree_cover_loss_area",
            "Tree cover loss in the year",
            gfc,
            "Ground area inside the year-2000 tree cover (canopy 30% or more) where a "
            "stand-replacement disturbance was detected in the year. Loss is not the same as "
            "deforestation: it includes plantation harvest and replanting, fire and storm "
            "damage. Regrowth is not subtracted.",
            topic=("landscape", "change"),
            universe="tree_cover_2000",
        ),
        _area(
            "tree_cover_loss_total_area",
            "Tree cover loss, 2001 to 2024",
            gfc,
            "Sum of yearly tree cover loss from 2001 to 2024 inside the year-2000 tree cover. "
            "Each pixel is counted once, in its first year of loss.",
            topic=("landscape", "change"),
            universe="tree_cover_2000",
        ),
        IndicatorSpec(
            "tree_cover_loss_total_share",
            "Share of year-2000 tree cover lost by 2024",
            gfc,
            "share",
            "percent",
            2,
            "Tree cover loss from 2001 to 2024 as a share of the year-2000 tree cover. Regrowth "
            "is not subtracted, so this is not net change.",
            topic=("landscape", "change"),
            numerator="tree_cover_loss_total_area",
            denominator="tree_cover_2000_area",
            aggregation="recompute_from_components",
            universe="tree_cover_2000",
        ),
    ]
    gsw = "jrc-global-surface-water"
    s += [
        _area(
            "surface_water_measured_area",
            "Area with surface-water data",
            gsw,
            "Ground area of the place with valid Global Surface Water observations. The "
            "denominator for surface-water shares.",
        ),
        _area(
            "surface_water_permanent_area",
            "Surface water present most of the time",
            gsw,
            "Ground area of 30 m pixels where Landsat detected open water in 75% or more of "
            "valid observations, 1984 to 2021.",
        ),
        _share(
            "surface_water_permanent_share",
            "Share under water most of the time",
            gsw,
            "surface_water_permanent_area",
            "surface_water_measured_area",
            "Share of the place where open water was detected in 75% or more of valid Landsat "
            "observations, 1984 to 2021.",
        ),
        _area(
            "surface_water_ever_area",
            "Surface water ever detected",
            gsw,
            "Ground area of 30 m pixels where Landsat detected open water at least once, 1984 "
            "to 2021. Includes seasonal tanks, paddy flooding and flood events.",
        ),
        _share(
            "surface_water_ever_share",
            "Share where water was ever detected",
            gsw,
            "surface_water_ever_area",
            "surface_water_measured_area",
            "Share of the place where open water was detected at least once by Landsat, 1984 to "
            "2021.",
        ),
    ]
    built = "ghsl-built-up"
    s += [
        _area(
            "built_up_measured_area",
            "Area with built-up surface data",
            built,
            "Ground area of the place covered by GHS-BUILT-S cells. The denominator for the "
            "built-up surface share.",
            topic=("landscape", "change"),
        ),
        _area(
            "built_up_surface_area",
            "Built-up surface",
            built,
            "Building footprint surface estimated by the Global Human Settlement Layer "
            "(GHS-BUILT-S R2023A) from Landsat and Sentinel-2 imagery, for the epoch. 100 m "
            "cells shared between places by area.",
            topic=("landscape", "change"),
        ),
        _share(
            "built_up_surface_share",
            "Built-up surface share",
            built,
            "built_up_surface_area",
            "built_up_measured_area",
            "Share of the place's area covered by building footprints, as estimated by "
            "GHS-BUILT-S R2023A for the epoch.",
            topic=("landscape", "change"),
        ),
    ]
    smod = "ghsl-settlement-model"
    s += [
        _area(
            "settlement_measured_area",
            "Area with settlement-type data",
            smod,
            "Ground area of the place covered by GHS-SMOD cells. The denominator for "
            "settlement-type shares.",
            topic=("landscape", "settlement"),
        ),
        _area(
            "settlement_urban_centre_area",
            "Area in an urban centre",
            smod,
            "Ground area in 1 km cells classed as 'urban centre' by the Degree of Urbanisation "
            "method (GHS-SMOD R2023A, 2020): contiguous cells of at least 1,500 inhabitants per "
            "km² with at least 50,000 inhabitants in total. This is a density rule, not Sri "
            "Lanka's administrative urban definition.",
            topic=("landscape", "settlement"),
        ),
        _share(
            "settlement_urban_centre_share",
            "Share in an urban centre",
            smod,
            "settlement_urban_centre_area",
            "settlement_measured_area",
            "Share of the place's area in 'urban centre' cells of GHS-SMOD 2020.",
            topic=("landscape", "settlement"),
        ),
        _area(
            "settlement_urban_area",
            "Area in an urban centre or urban cluster",
            smod,
            "Ground area in 1 km cells classed as urban centre, dense urban cluster, semi-dense "
            "urban cluster or suburban by the Degree of Urbanisation method (GHS-SMOD R2023A, "
            "2020). A density rule on a modelled population grid, not the administrative urban "
            "definition.",
            topic=("landscape", "settlement"),
        ),
        _share(
            "settlement_urban_share",
            "Share in an urban centre or urban cluster",
            smod,
            "settlement_urban_area",
            "settlement_measured_area",
            "Share of the place's area in urban centre or urban cluster cells of GHS-SMOD 2020.",
            topic=("landscape", "settlement"),
        ),
    ]
    return s


OVERTURE_CATEGORIES: dict[str, str] = {
    "services_and_business": "services and business",
    "shopping": "shopping",
    "lodging": "lodging",
    "education": "education",
    "food_and_drink": "food and drink",
    "travel_and_transportation": "travel and transportation",
    "cultural_and_historic": "cultural and historic",
    "lifestyle_services": "lifestyle services",
    "community_and_government": "community and government",
    "sports_and_recreation": "sports and recreation",
    "health_care": "health care",
    "arts_and_entertainment": "arts and entertainment",
    "geographic_entities": "geographic entities",
}
OVERTURE_MIN_CONFIDENCE = 0.5
HEALTH_AMENITIES = ("hospital", "clinic", "doctors")


def _count(id_: str, name: str, dataset: str, unit: str, definition: str, **kw) -> IndicatorSpec:
    return IndicatorSpec(
        id_,
        name,
        dataset,
        "count",
        unit,
        0,
        definition,
        topic=("features",),
        universe="mapped_features",
        **kw,
    )


def point_specs() -> list[IndicatorSpec]:
    giga, health, places, wd = (
        "giga-school-locations",
        "healthsites-lk",
        "overture-places",
        "wikidata-places-lk",
    )
    s = [
        _count(
            "schools_located",
            "Schools (located)",
            giga,
            "schools",
            "Schools whose published coordinates fall inside the place, from the Giga school "
            "location list (source named by Giga: Sri Lanka Ministry of Education). A count of "
            "listed locations, not an official school census count for the place.",
        ),
        _count(
            "schools_connected",
            "Schools recorded as connected to the internet",
            giga,
            "schools",
            "Located schools whose Giga record says connectivity is available ('Yes'), from "
            "government data and Giga's real-time mapping.",
        ),
        IndicatorSpec(
            "schools_connected_share",
            "Share of located schools recorded as connected",
            giga,
            "share",
            "percent",
            1,
            "Schools recorded as connected as a share of located schools.",
            topic=("features",),
            numerator="schools_connected",
            denominator="schools_located",
            aggregation="recompute_from_components",
            universe="mapped_features",
        ),
        IndicatorSpec(
            "nearest_school_distance",
            "Straight-line distance to the nearest located school",
            giga,
            "mean",
            "kilometres",
            2,
            "Straight-line distance from the GN division's label point to the nearest school in "
            "the Giga list, computed in EPSG:5235. Not a travel distance or travel time.",
            topic=("features", "access"),
            aggregation="none",
            universe="mapped_features",
        ),
        _count(
            "health_facilities_mapped",
            "Health facilities mapped in OpenStreetMap",
            health,
            "facilities",
            "Hospitals, clinics and doctors' practices mapped in OpenStreetMap (healthsites.io "
            "extract) that fall inside the place. A count of what volunteers have mapped; "
            "completeness is not measured, so a low count is not evidence of few facilities.",
        ),
        IndicatorSpec(
            "nearest_health_facility_distance",
            "Straight-line distance to the nearest mapped health facility",
            health,
            "mean",
            "kilometres",
            2,
            "Straight-line distance from the GN division's label point to the nearest hospital, "
            "clinic or doctors' practice mapped in OpenStreetMap, computed in EPSG:5235. Not a "
            "travel distance; unmapped facilities are not seen.",
            topic=("features", "access"),
            aggregation="none",
            universe="mapped_features",
        ),
        _count(
            "places_listed",
            "Places listed in Overture Maps",
            places,
            "places",
            "Businesses, institutions and points of interest in Overture Maps Places with "
            f"confidence of {OVERTURE_MIN_CONFIDENCE} or more that fall inside the place. Most "
            "records come from Meta; the list reflects online presence, not a business register.",
        ),
        _count(
            "wikidata_items",
            "Wikidata items with coordinates",
            wd,
            "items",
            "Wikidata items located in Sri Lanka whose coordinates fall inside the place "
            "(settlements, landmarks, natural features, institutions).",
        ),
    ]
    ob = "overture-buildings"
    s += [
        _count(
            "buildings_mapped",
            "Building footprints mapped",
            ob,
            "buildings",
            "Building footprints in Overture Maps (OpenStreetMap, Microsoft and Google footprints, "
            "merged by Overture) whose inside point falls in the place. Machine-detected "
            "footprints include sheds, outbuildings and some false detections, and miss some "
            "buildings under tree cover; this is not a count of houses or households.",
        ),
        IndicatorSpec(
            "building_footprint_area",
            "Building footprint area",
            ob,
            "count",
            "hectares",
            2,
            "Total ground area of the mapped building footprints in the place, computed in "
            "EPSG:5235.",
            topic=("features",),
            universe="mapped_features",
        ),
        IndicatorSpec(
            "building_footprint_mean",
            "Mean building footprint",
            ob,
            "ratio",
            "square metres",
            1,
            "Building footprint area divided by the number of mapped footprints.",
            topic=("features",),
            numerator="building_footprint_area",
            denominator="buildings_mapped",
            aggregation="recompute_from_components",
            universe="mapped_features",
        ),
    ]
    for slug, label in OVERTURE_CATEGORIES.items():
        s.append(
            _count(
                f"places_listed_{slug}",
                f"Places listed: {label}",
                places,
                "places",
                f"Overture Maps places in the top-level category '{slug}' with confidence of "
                f"{OVERTURE_MIN_CONFIDENCE} or more that fall inside the place.",
            )
        )
    return s


SPECS: dict[str, IndicatorSpec] = {spec.id: spec for spec in [*indicator_specs(), *point_specs()]}


def indicator_yaml(spec: IndicatorSpec) -> str:
    """The catalogue entry for an indicator, written from the same spec the build uses."""

    def q(text: str | None) -> str:
        return "null" if text is None else text

    wrapped: list[str] = []
    line = " "
    for word in spec.definition.split():
        if len(line) + len(word) + 1 > 98:
            wrapped.append(line.rstrip())
            line = " "
        line += " " + word
    wrapped.append(line.rstrip())
    return "\n".join(
        [
            f"id: {spec.id}",
            f'name: "{spec.name}"',
            f'short_name: "{spec.name}"',
            f"topic: [{', '.join(spec.topic)}]",
            f"measure_type: {spec.measure_type}",
            f"unit: {spec.unit}",
            f"universe: {spec.universe}",
            f"numerator: {q(spec.numerator)}",
            f"denominator: {q(spec.denominator)}",
            f"aggregation: {spec.aggregation}",
            f"higher_is: {spec.higher_is}",
            f"distribution: {spec.distribution}",
            f"decimals: {spec.decimals}",
            "sensitivity: public",
            "definition: >",
            *wrapped,
            f'source_definition_ref: "{spec.dataset} (catalog/datasets/{spec.dataset}.yaml)"',
            "methodology_notes: docs/methods/landscape.md",
            "",
        ]
    )
