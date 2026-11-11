"""Census 2024 GN-level population and occupied housing units (prompt D01).

Source: Department of Census and Statistics, Census of Population and Housing 2024.
Held files: the provisional GN population-by-sex-and-age workbook and the occupied-housing-units
workbook. Both use DCS codes (DDSSGGG for GN, DDSS for DS); joins to the spine go through the
G02 crosswalk. Nothing is matched by name alone.

Output rows follow data-model.md §5 and footprint-model.md. Counts are census counts; derived
ratios and shares are computed from the published counts, never adopted from another source.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import pandas as pd

from slf.dataset import Dataset, QAReport, Row
from slf.snapshot import SnapshotRef, snapshot_url
from slf.storage import Storage

POP_URL = "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/GN_population_excel"
HOUSING_URL = (
    "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/GN_housing_excel"
)
POP_FILE = "GN_population.xlsx"
HOUSING_FILE = "GN_housing.xlsx"
CENSUS_DATE = "2024-12-19"
PERIOD = "2024"
VINTAGE = "2024"

# Published totals used as validation anchors. Locators point to the Final Report snapshot
# CPH2024_Final_Eng.pdf (20261107T171418Z) unless stated otherwise.
EXPECTED_NATIONAL = {
    "population_total": 21_781_800,
    "population_male": 10_512_344,
    "population_female": 11_269_456,
    "population_age_0_14": 4_506_839,
    "population_age_15_59": 13_353_837,
    "population_age_60_64": 1_183_310,
    "population_age_65_plus": 2_737_814,
    "population_age_60_plus": 3_921_124,
    "occupied_housing_units": 6_030_541,
}
EXPECTED_DISTRICTS_POP = {
    11: 2_375_415,
    12: 2_436_142,
    13: 1_305_784,
    21: 1_461_895,
    22: 526_870,
    23: 725_280,
    31: 1_097_372,
    32: 837_889,
    33: 671_418,
    41: 594_751,
    42: 123_756,
    43: 172_312,
    44: 122_619,
    45: 136_710,
    51: 595_918,
    52: 744_551,
    53: 442_745,
    61: 1_768_156,
    62: 818_816,
    71: 960_080,
    72: 447_530,
    81: 872_307,
    82: 527_585,
    91: 1_145_423,
    92: 870_476,
}
EXPECTED_DISTRICTS_HOUSING = {
    11: 654_051,
    12: 683_025,
    13: 349_430,
    21: 389_826,
    22: 148_184,
    23: 192_915,
    31: 305_379,
    32: 230_034,
    33: 187_558,
    41: 156_797,
    42: 32_005,
    43: 47_825,
    44: 34_348,
    45: 36_484,
    51: 167_150,
    52: 202_861,
    53: 119_351,
    61: 506_909,
    62: 231_494,
    71: 271_408,
    72: 126_482,
    81: 239_417,
    82: 150_728,
    91: 324_853,
    92: 242_027,
}

COUNT_INDICATORS = (
    "population_total",
    "population_male",
    "population_female",
    "population_age_0_14",
    "population_age_15_59",
    "population_age_60_64",
    "population_age_65_plus",
    "occupied_housing_units",
)
DERIVED_INDICATORS = (
    "population_age_60_plus",
    "sex_ratio",
    "population_age_0_14_share",
    "population_age_60_plus_share",
    "persons_per_occupied_housing_unit",
    "population_density",
)
ALL_INDICATORS = COUNT_INDICATORS + DERIVED_INDICATORS

COUNT_UNITS = {
    "population_total": ("persons", "persons"),
    "population_male": ("persons", "persons"),
    "population_female": ("persons", "persons"),
    "population_age_0_14": ("persons", "persons"),
    "population_age_15_59": ("persons", "persons"),
    "population_age_60_64": ("persons", "persons"),
    "population_age_65_plus": ("persons", "persons"),
    "occupied_housing_units": ("housing_units", "housing_units_occupied"),
}
DERIVED_UNITS = {
    "population_age_60_plus": ("persons", "persons"),
    "sex_ratio": ("males per 100 females", "persons"),
    "population_age_0_14_share": ("percent", "persons"),
    "population_age_60_plus_share": ("percent", "persons"),
    "persons_per_occupied_housing_unit": ("persons per housing unit", "persons"),
    "population_density": ("persons per km2", "persons"),
}
COLUMNS = {
    "population_total": (9, "Total", POP_FILE),
    "population_male": (10, "Male", POP_FILE),
    "population_female": (11, "Female", POP_FILE),
    "population_age_0_14": (13, "0 - 14", POP_FILE),
    "population_age_15_59": (14, "15 - 59", POP_FILE),
    "population_age_60_64": (15, "60 - 64", POP_FILE),
    "population_age_65_plus": (16, "65 and above", POP_FILE),
    "occupied_housing_units": (9, "Occupied Housing Units", HOUSING_FILE),
}


def _latest(storage: Storage, filename: str) -> SnapshotRef:
    keys = sorted(
        k for k in storage.list("raw/dcs/census-2024-gnd-tables") if k.endswith("/" + filename)
    )
    if not keys:
        raise FileNotFoundError(
            f"no snapshot {filename}; run `slf snapshot census-2024-gnd-tables`"
        )
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})


def _workbook(storage: Storage, ref: SnapshotRef) -> openpyxl.Workbook:
    return openpyxl.load_workbook(io.BytesIO(storage.get(ref.key)), read_only=True, data_only=True)


def _clean(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _int_cell(value: object, *, line: int, field: str) -> int:
    """Read a numeric cell without silently accepting labels or formulas."""
    if isinstance(value, bool):
        raise ValueError(f"line {line}: {field} is not an integer: {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    raise ValueError(f"line {line}: {field} is not an integer: {value!r}")


def parse_population(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    wb = _workbook(storage, ref)
    ws = wb.worksheets[0]
    header = [
        _clean(c).replace("\n", " ")
        for c in next(ws.iter_rows(min_row=4, max_row=4, values_only=True))
    ]
    expected = [
        "Province Code",
        "Province Name",
        "District Code",
        "District Name",
        "DS_Division Code",
        "DS_Division Name",
        "GN_Division Code",
        "GN_Division Name",
        "GN_Division Number",
        "Sex",
    ]
    if header[:10] != expected:
        raise ValueError(f"unexpected population header: {header[:10]}")
    rows: list[dict[str, object]] = []
    for line, r in enumerate(ws.iter_rows(min_row=6, values_only=True), start=6):
        if r[6] is None:
            continue
        rows.append(
            {
                "line": line,
                "province_code": _int_cell(r[0], line=line, field="province code"),
                "province_name": _clean(r[1]),
                "district_code": _int_cell(r[2], line=line, field="district code"),
                "district_name": _clean(r[3]),
                "ds_code": _int_cell(r[4], line=line, field="DS code"),
                "ds_name": _clean(r[5]),
                "gn_code": _int_cell(r[6], line=line, field="GN code"),
                "gn_name": _clean(r[7]),
                "gn_number": _clean(r[8]) or None,
                "population_total": _int_cell(r[9], line=line, field="population total"),
                "population_male": _int_cell(r[10], line=line, field="population male"),
                "population_female": _int_cell(r[11], line=line, field="population female"),
                "age_total": _int_cell(r[12], line=line, field="age total"),
                "population_age_0_14": _int_cell(r[13], line=line, field="age 0-14"),
                "population_age_15_59": _int_cell(r[14], line=line, field="age 15-59"),
                "population_age_60_64": _int_cell(r[15], line=line, field="age 60-64"),
                "population_age_65_plus": _int_cell(r[16], line=line, field="age 65+"),
            }
        )
    wb.close()
    df = pd.DataFrame(rows)
    df["dcs_gn"] = df.apply(
        lambda x: f"{x.district_code:02d}{x.ds_code:02d}{x.gn_code:03d}", axis=1
    )
    df["dcs_ds"] = df.apply(lambda x: f"{x.district_code:02d}{x.ds_code:02d}", axis=1)
    return df


def parse_housing(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    wb = _workbook(storage, ref)
    ws = wb.worksheets[0]
    rows: list[dict[str, object]] = []
    for line, r in enumerate(ws.iter_rows(min_row=6, values_only=True), start=6):
        if r[6] is None:
            continue
        district = _int_cell(r[2], line=line, field="district code")
        ds = _int_cell(r[4], line=line, field="DS code")
        gn = _int_cell(r[6], line=line, field="GN code")
        rows.append(
            {
                "line": line,
                "dcs_gn": f"{district:02d}{ds:02d}{gn:03d}",
                "gn_name": _clean(r[7]),
                "occupied_housing_units": _int_cell(
                    r[9], line=line, field="occupied housing units"
                ),
            }
        )
    wb.close()
    return pd.DataFrame(rows)


def _crosswalk(catalog: Path) -> tuple[dict[str, str], dict[str, str]]:
    cw = pd.read_csv(catalog / "geographies" / "codes" / "dcs-census2024.csv", dtype=str)
    gn = cw[cw["external_code"].str.len() == 7].set_index("external_code")["geography_id"].to_dict()
    ds = cw[cw["external_code"].str.len() == 4].set_index("external_code")["geography_id"].to_dict()
    return gn, ds


def _areas(spine_dir: Path) -> dict[str, float]:
    versions = pd.read_parquet(spine_dir / "geography_versions.geoparquet")
    return dict(zip(versions["geography_id"], versions["area_km2"], strict=False))


def _derived(counts: dict[str, float], area_km2: float | None) -> dict[str, float | None]:
    total = counts["population_total"]
    male = counts["population_male"]
    female = counts["population_female"]
    units = counts["occupied_housing_units"]
    return {
        "population_age_60_plus": counts["population_age_60_64"] + counts["population_age_65_plus"],
        "sex_ratio": round(100.0 * male / female, 4) if female else None,
        "population_age_0_14_share": round(100.0 * counts["population_age_0_14"] / total, 4)
        if total
        else None,
        "population_age_60_plus_share": (
            round(
                100.0 * (counts["population_age_60_64"] + counts["population_age_65_plus"]) / total,
                4,
            )
            if total
            else None
        ),
        "persons_per_occupied_housing_unit": round(total / units, 4) if units else None,
        "population_density": round(total / area_km2, 4) if area_km2 else None,
    }


def _row(
    *,
    indicator: str,
    geography_id: str,
    value: float | None,
    source_locator: str,
    snapshot_sha256: str,
    note_ids: list[str] | None = None,
) -> Row:
    is_count = indicator in COUNT_INDICATORS
    unit, universe = COUNT_UNITS[indicator] if is_count else DERIVED_UNITS[indicator]
    return {
        "claim_id": f"dcs-census2024:{geography_id}:{indicator}:{PERIOD}",
        "indicator_id": indicator,
        "geography_id": geography_id,
        "geography_vintage": VINTAGE,
        "period": PERIOD,
        "time_start": CENSUS_DATE,
        "time_end": CENSUS_DATE,
        "time_support": "snapshot",
        "support_type": "area_total",
        "footprint_ref": geography_id,
        "information_footprint_ref": "gn-2024",
        "universe": universe,
        "collection_method": "enumeration",
        "sensitivity": "public",
        "revision_status": "provisional",
        "preferred": True,
        "preferred_reason": (
            "Only claim in this preview: DCS Census 2024 GN workbook."
            if is_count
            else "Derived from DCS Census 2024 GN counts; see the indicator definition."
        ),
        "breakdown": None,
        "value": value,
        "value_status": "normal" if value is not None else "not_available",
        "unit": unit,
        "data_nature": "census_count",
        "verification": "machine_extracted",
        "dataset_id": "census-2024-gnd-tables",
        "snapshot_sha256": snapshot_sha256,
        "source_locator": source_locator,
        "note_ids": note_ids or [],
        "release": None,
    }


@dataclass
class _Aggregate:
    """A DS, district, province or country total built from GN rows."""

    geography_id: str
    counts: dict[str, float] = field(default_factory=lambda: dict.fromkeys(COUNT_INDICATORS, 0.0))
    first_line: int = 0
    last_line: int = 0
    units: int = 0

    def add(self, counts: dict[str, float], line: int) -> None:
        for indicator in COUNT_INDICATORS:
            self.counts[indicator] += counts[indicator]
        self.first_line = line if not self.units else min(self.first_line, line)
        self.last_line = line if not self.units else max(self.last_line, line)
        self.units += 1


class Census2024Gnd(Dataset):
    dataset_id = "census-2024-gnd-tables"
    source_id = "dcs"

    def snapshot(self, storage: Storage) -> SnapshotRef:
        try:
            pop = _latest(storage, POP_FILE)
        except FileNotFoundError:
            pop = snapshot_url(
                storage,
                source="dcs",
                dataset=self.dataset_id,
                url=POP_URL,
                filename=POP_FILE,
                licence_note="rights unclear; internal use only until DCS replies",
            )
        try:
            _latest(storage, HOUSING_FILE)
        except FileNotFoundError:
            snapshot_url(
                storage,
                source="dcs",
                dataset=self.dataset_id,
                url=HOUSING_URL,
                filename=HOUSING_FILE,
                licence_note="rights unclear; internal use only until DCS replies",
            )
        return pop

    def extract(self, storage: Storage, ref: SnapshotRef) -> list[Row]:
        pop_ref = _latest(storage, POP_FILE)
        housing_ref = _latest(storage, HOUSING_FILE)
        pop = parse_population(storage, pop_ref)
        housing = parse_housing(storage, housing_ref)
        if set(pop["dcs_gn"]) != set(housing["dcs_gn"]):
            raise ValueError("population and housing workbooks do not cover the same GN units")
        housing_by_gn = {str(r["dcs_gn"]): r for r in housing.to_dict("records")}
        merged: list[Row] = []
        for record in pop.to_dict("records"):
            code = str(record["dcs_gn"])
            house = housing_by_gn.get(code)
            if house is None:
                raise ValueError(f"GN {code} has no occupied-housing value")
            merged.append(
                {
                    **record,
                    "occupied_housing_units": house["occupied_housing_units"],
                    "housing_line": house["line"],
                    "population_sha256": pop_ref.sha256,
                    "housing_sha256": housing_ref.sha256,
                }
            )
        return merged

    def harmonise(self, rows: list[Row], ref: SnapshotRef) -> list[Row]:
        catalog = Path(__file__).resolve().parents[3] / "catalog"
        gn_map, ds_map = _crosswalk(catalog)
        areas = _areas(
            Path(__file__).resolve().parents[3] / "pipeline" / "data" / "build" / "geography-spine"
        )
        pop_sha = str(rows[0]["population_sha256"])
        housing_sha = str(rows[0]["housing_sha256"])

        observations: list[Row] = []
        aggregates: dict[tuple[str, str], _Aggregate] = {}
        self.unmatched_gn: list[str] = []
        for rec in rows:
            counts: dict[str, float] = {k: float(rec[k]) for k in COUNT_INDICATORS}
            district = str(rec["district_code"])
            province = str(rec["province_code"])
            ds = str(rec["dcs_ds"])
            for level, key, geo in (
                ("ds", ds, ds_map.get(ds)),
                ("district", district, f"LK{int(district):02d}"),
                ("province", province, f"LK{int(province)}"),
                ("country", "LK", "LK"),
            ):
                if not geo:
                    continue
                aggregates.setdefault((level, key), _Aggregate(geo)).add(counts, int(rec["line"]))

            geo = gn_map.get(str(rec["dcs_gn"]))
            if not geo:
                # listed in QA; its values still enter DS/district totals above
                self.unmatched_gn.append(str(rec["dcs_gn"]))
                continue
            derived = _derived(counts, areas.get(geo))
            for indicator in COUNT_INDICATORS:
                col, label, filename = COLUMNS[indicator]
                is_housing = indicator == "occupied_housing_units"
                sha = housing_sha if is_housing else pop_sha
                sheet = "Housing Units" if is_housing else "Population"
                line = rec["housing_line"] if is_housing else rec["line"]
                locator = f"{filename}, sheet '{sheet}', row {line}, column {col} ('{label}')"
                observations.append(
                    _row(
                        indicator=indicator,
                        geography_id=geo,
                        value=counts[indicator],
                        source_locator=locator,
                        snapshot_sha256=sha,
                    )
                )
            for indicator, value in derived.items():
                observations.append(
                    _row(
                        indicator=indicator,
                        geography_id=geo,
                        value=value,
                        source_locator=(
                            f"{POP_FILE} row {rec['line']} and {HOUSING_FILE} row "
                            f"{rec['housing_line']}; derived {indicator}"
                        ),
                        snapshot_sha256=pop_sha,
                        note_ids=["derived-two-workbooks"]
                        if indicator == "persons_per_occupied_housing_unit"
                        else [],
                    )
                )

        # Aggregates: DS -> district -> province -> country. DS 5224 has no spine unit (D-022),
        # so it contributes to Ampara district but has no DS-level output. Unmatched GNs
        # contribute to their DS and above.
        for (level, code), aggregate in sorted(aggregates.items()):
            geo = aggregate.geography_id
            derived = _derived(aggregate.counts, areas.get(geo))
            locator = (
                f"{POP_FILE} sheet 'Population' and {HOUSING_FILE} sheet 'Housing Units', "
                f"{aggregate.units} GN rows summed to {level} {code}; row range "
                f"{aggregate.first_line}-{aggregate.last_line}"
            )
            for indicator in COUNT_INDICATORS:
                sha = housing_sha if indicator == "occupied_housing_units" else pop_sha
                observations.append(
                    _row(
                        indicator=indicator,
                        geography_id=geo,
                        value=aggregate.counts[indicator],
                        source_locator=locator,
                        snapshot_sha256=sha,
                    )
                )
            for indicator, value in derived.items():
                observations.append(
                    _row(
                        indicator=indicator,
                        geography_id=geo,
                        value=value,
                        source_locator=locator,
                        snapshot_sha256=pop_sha,
                        note_ids=["aggregate"],
                    )
                )
        return observations

    def validate(self, observations: list[Row]) -> QAReport:
        report = super().validate(observations)
        indicators_by_geo: dict[str, set[str]] = {}
        values: dict[tuple[str, str], float | None] = {}
        for row in observations:
            indicators_by_geo.setdefault(str(row["geography_id"]), set()).add(
                str(row["indicator_id"])
            )
            values[(str(row["geography_id"]), str(row["indicator_id"]))] = row["value"]
            value = row["value"]
            if value is not None and value < 0:
                report.errors.append(f"{row['claim_id']}: negative value {value}")

        expected_per_geo = len(ALL_INDICATORS)
        for geo, seen in sorted(indicators_by_geo.items()):
            if len(seen) != expected_per_geo:
                report.errors.append(f"{geo}: {len(seen)} indicators, expected {expected_per_geo}")

        for indicator, expected in EXPECTED_NATIONAL.items():
            got = values.get(("LK", indicator))
            if got is None or int(got) != expected:
                report.errors.append(f"national {indicator}: {got}, expected {expected}")

        # District ids follow the DCS numeric code: district 11 is LK11. Compare against the
        # Final Report tables without resolving names, which drift between sources.
        for code, expected in EXPECTED_DISTRICTS_POP.items():
            geo = f"LK{code:02d}"
            got = values.get((geo, "population_total"))
            if got is None or int(got) != expected:
                report.errors.append(
                    f"district {geo}: population {got}, expected {expected} "
                    "(Final Report Table 3.2)"
                )
        for code, expected in EXPECTED_DISTRICTS_HOUSING.items():
            geo = f"LK{code:02d}"
            got = values.get((geo, "occupied_housing_units"))
            if got is None or int(got) != expected:
                report.errors.append(
                    f"district {geo}: housing {got}, expected {expected} (Final Report Table 11.2)"
                )
        unmatched = getattr(self, "unmatched_gn", None)
        if unmatched is None:
            report.warnings.append(
                "Unmatched DCS GN units were not counted (validate ran without harmonise)."
            )
        elif unmatched:
            report.warnings.append(
                f"{len(unmatched)} DCS GN units are unmatched in the G02 crosswalk; they enter "
                "DS/district totals but have no GN-level rows. Codes: "
                + ", ".join(sorted(unmatched))
            )
        report.warnings.append(
            "DCS 5224 Kalmunai has no spine equivalent (D-022); its population enters Ampara "
            "district but no DS-level row is published."
        )
        report.warnings.append(
            "Persons per occupied housing unit uses two snapshots; snapshot_sha256 records the "
            "population workbook and the locator names both files."
        )
        return report

    def publish(self, observations: list[Row], report: QAReport, out_dir: str) -> list[str]:
        if not report.ok:
            raise RuntimeError(f"refusing to publish {self.dataset_id}: QA report has errors")
        out = Path(out_dir) / self.dataset_id
        out.mkdir(parents=True, exist_ok=True)
        frame = (
            pd.DataFrame(observations)
            .sort_values(["geography_id", "indicator_id"])
            .reset_index(drop=True)
        )
        parquet = out / "observations.parquet"
        csv = out / "observations.csv"
        qa = out / "qa.md"
        frame.to_parquet(parquet, index=False)
        frame.to_csv(csv, index=False)
        qa.write_text(report.to_markdown(), encoding="utf-8")
        return [str(parquet), str(csv), str(qa)]
