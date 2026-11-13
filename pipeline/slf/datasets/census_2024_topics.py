"""Census 2024 topic tables, step (a): households and amenities by GN (D-032).

Source: Department of Census and Statistics, Census of Population and Housing 2024, "Household
Information by Grama Niladhari Division (Provisional)" (``HH_GND_excel``). One row per GN with the
number of households and four groups of household counts: main source of drinking water, main
cooking fuel, main source of lighting and toilet facilities. Every group sums to the number of
households in every row; extraction fails if one does not.

GN codes join to the spine through the G02 crosswalk, as in ``census_2024_gnd``. DS, district,
province and country values are sums of GN rows (unmatched GNs included). District and national
sums are checked against DCS's own district tables A5 (water), A6 (cooking), A7 (lighting) and A8
(toilets), category by category.

Other topics in the dataset (age, sector, local authority, DS materials, ethnicity and religion)
are later steps under D-032 and D-033; they are not read here.
"""

from __future__ import annotations

import io
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl
import pandas as pd

from slf.dataset import Dataset, QAReport, Row
from slf.datasets.census_2024_gnd import _crosswalk, _int_cell
from slf.snapshot import SnapshotRef, snapshot_url
from slf.storage import Storage

DATASET_ID = "census-2024-topic-tables"
BASE_URL = "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024"
HH_FILE = "HH_GND_excel.xlsx"
HH_URL = f"{BASE_URL}/HH_GND_excel"
CHECK_TABLES = {
    "water": ("HousingA_A5.xlsx", f"{BASE_URL}/HousingA/A5"),
    "cooking": ("HousingA_A6.xlsx", f"{BASE_URL}/HousingA/A6"),
    "lighting": ("HousingA_A7.xlsx", f"{BASE_URL}/HousingA/A7"),
    "toilet": ("HousingA_A8.xlsx", f"{BASE_URL}/HousingA/A8"),
}
LICENCE_NOTE = "rights unclear; non-commercial publication under D-030 as extended by D-032"
CENSUS_DATE = "2024-12-19"
PERIOD = "2024"
VINTAGE = "2024"

HOUSEHOLDS = "households_total"
HOUSEHOLDS_COLUMN = 9
FIRST_DATA_LINE = 7
GROUP_TITLES = {
    "water": "Main Source/way of drinking water",
    "cooking": "Main Source of Energy/Fuel Used for Cooking",
    "lighting": "Main source of Lighting",
    "toilet": "Toilet facilities",
}


@dataclass(frozen=True)
class Category:
    column: int  # 0-based column in HH_GND_excel.xlsx
    group: str
    slug: str
    name: str  # our English label
    source_label: str  # the column heading exactly as DCS prints it (typos kept)

    @property
    def count_id(self) -> str:
        return f"households_{self.group}_{self.slug}"

    @property
    def share_id(self) -> str:
        return f"{self.count_id}_share"


# Column order is the same in HH_GND_excel.xlsx and in the A5-A8 district tables.
CATEGORIES: tuple[Category, ...] = (
    Category(10, "water", "protected_well", "Protected well", "Protected well"),
    Category(11, "water", "semi_protected_well", "Semi-protected well", "Semi protected well"),
    Category(12, "water", "unprotected_well", "Unprotected well", "Unprotected well"),
    Category(13, "water", "tube_well", "Tube well", "Tube well"),
    Category(14, "water", "spring", "Spring or fountain", "Spring/\nFountain"),
    Category(
        15,
        "water",
        "pipe_nwsdb",
        "Pipe-borne water from the National Water Supply and Drainage Board",
        "Pipe borne water - National water supply & drainage board",
    ),
    Category(
        16,
        "water",
        "pipe_local_authority",
        "Pipe-borne water from a local authority",
        "Pipe borne water - Local Authority",
    ),
    Category(
        17,
        "water",
        "pipe_community",
        "Pipe-borne water from a community-based organisation",
        "Pipe borne water - Community base organiziation",
    ),
    Category(
        18,
        "water",
        "pipe_private",
        "Pipe-borne water from a private water supply project",
        "Pipe borne water - Private water supply project",
    ),
    Category(19, "water", "tank_river_stream", "Tank, river or stream", "Tank/ River/Streams"),
    Category(20, "water", "rain_water", "Rain water", "Rain water"),
    Category(21, "water", "bottled_water", "Bottled water", "Bottled water"),
    Category(
        22, "water", "filter_ro_plant", "Filtered water (R.O. plant)", "Filter water (R.O. Plant)"
    ),
    Category(23, "water", "bowser", "Bowser", "Bowser"),
    Category(24, "water", "other", "Other source of drinking water", "Other (specify)"),
    Category(25, "cooking", "firewood", "Firewood", "Fire wood"),
    Category(26, "cooking", "kerosene", "Kerosene", "Kerosene"),
    Category(27, "cooking", "gas", "Gas", "Gas"),
    Category(28, "cooking", "electricity", "Electricity", "Electricity"),
    Category(29, "cooking", "sawdust_paddy_husk", "Sawdust or paddy husk", "Saw dust/Paddy husk"),
    Category(30, "cooking", "biogas", "Biogas", "Bio gas"),
    Category(31, "cooking", "other", "Other cooking fuel", "Other (Specify bellow )"),
    Category(32, "cooking", "not_relevant", "Not relevant", "Not relavent"),
    Category(
        33,
        "lighting",
        "electricity_grid",
        "Electricity from the national grid or a rural hydro power project",
        "Electricity - from National grid/rural hydro power project",
    ),
    Category(34, "lighting", "kerosene_lamp", "Kerosene lamp", "Kerosene lamp"),
    Category(
        35,
        "lighting",
        "solar_grid_connected",
        "Solar power (grid connected)",
        "Solar power (grid connected)",
    ),
    Category(
        36,
        "lighting",
        "solar_stand_alone",
        "Solar power (stand-alone)",
        "Solar power (stand alone)",
    ),
    Category(37, "lighting", "biogas", "Biogas", "Bio gas"),
    Category(38, "lighting", "generator", "Generator", "Generator"),
    Category(39, "lighting", "other", "Other source of lighting", "Other (Specify bellow )"),
    Category(
        40,
        "toilet",
        "within_unit_exclusive",
        "Toilet within the housing unit, for the household only",
        "Within the housing unit - Exclusively for the household",
    ),
    Category(
        41,
        "toilet",
        "within_unit_shared",
        "Toilet within the housing unit, shared with another household",
        "Within the housing unit - Sharing with another household",
    ),
    Category(
        42,
        "toilet",
        "within_premises_exclusive",
        "Toilet within the premises, for the household only",
        "Within Premises - Exclusively for the household",
    ),
    Category(
        43,
        "toilet",
        "within_premises_shared",
        "Toilet within the premises, shared with another household",
        "Within Premises - Sharing with another household",
    ),
    Category(
        44,
        "toilet",
        "shared_other_unit",
        "No toilet of its own; shares with another housing unit or units",
        "No toilet but sharing with another housing unit/units",
    ),
    Category(45, "toilet", "common_public", "Common or public toilet", "Common/ Public toilet"),
    Category(
        46,
        "toilet",
        "not_using",
        "Not using a toilet",
        "Not using a toilet (use jungle, beach and open ground)",
    ),
)
GROUPS: tuple[str, ...] = ("water", "cooking", "lighting", "toilet")
COUNT_INDICATORS: tuple[str, ...] = (HOUSEHOLDS, *(c.count_id for c in CATEGORIES))
SHARE_INDICATORS: tuple[str, ...] = tuple(c.share_id for c in CATEGORIES)
ALL_INDICATORS: tuple[str, ...] = COUNT_INDICATORS + SHARE_INDICATORS
LAST_COLUMN = max(c.column for c in CATEGORIES)


def _latest(storage: Storage, filename: str) -> SnapshotRef:
    keys = sorted(k for k in storage.list(f"raw/dcs/{DATASET_ID}") if k.endswith("/" + filename))
    if not keys:
        raise FileNotFoundError(f"no snapshot {filename}; run `slf snapshot {DATASET_ID}`")
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})


def _rows(storage: Storage, ref: SnapshotRef) -> list[tuple[object, ...]]:
    wb = openpyxl.load_workbook(io.BytesIO(storage.get(ref.key)), read_only=True, data_only=True)
    rows: list[tuple[object, ...]] = [
        tuple(r) for r in wb.worksheets[0].iter_rows(values_only=True)
    ]
    wb.close()
    return rows


def _heading(value: object) -> str:
    return re.sub(r"\s+", " ", str(value)).strip() if value is not None else ""


def check_hh_header(rows: list[tuple[object, ...]]) -> None:
    """Fail unless the group titles and category headings are where this module expects them."""
    titles = rows[3]
    labels = rows[5]
    if _heading(titles[HOUSEHOLDS_COLUMN]) != "Number of Households":
        raise ValueError(f"unexpected households heading: {titles[HOUSEHOLDS_COLUMN]!r}")
    for group, title in GROUP_TITLES.items():
        first = min(c.column for c in CATEGORIES if c.group == group)
        if _heading(titles[first]) != title:
            raise ValueError(f"unexpected {group} heading in column {first}: {titles[first]!r}")
    for category in CATEGORIES:
        if _heading(labels[category.column]) != _heading(category.source_label):
            raise ValueError(
                f"column {category.column}: heading {labels[category.column]!r}, expected "
                f"{category.source_label!r}"
            )


def parse_households(rows: list[tuple[object, ...]]) -> pd.DataFrame:
    """One record per GN, with every group checked against the households count."""
    check_hh_header(rows)
    records: list[dict[str, object]] = []
    for line, r in enumerate(rows[FIRST_DATA_LINE - 1 :], start=FIRST_DATA_LINE):
        if len(r) <= LAST_COLUMN or r[6] is None:
            continue
        district = _int_cell(r[2], line=line, field="district code")
        ds = _int_cell(r[4], line=line, field="DS code")
        gn = _int_cell(r[6], line=line, field="GN code")
        record: dict[str, object] = {
            "line": line,
            "province_code": _int_cell(r[0], line=line, field="province code"),
            "district_code": district,
            "district_name": str(r[3]).strip(),
            "dcs_ds": f"{district:02d}{ds:02d}",
            "dcs_gn": f"{district:02d}{ds:02d}{gn:03d}",
            HOUSEHOLDS: _int_cell(r[HOUSEHOLDS_COLUMN], line=line, field="households"),
        }
        for category in CATEGORIES:
            record[category.count_id] = _int_cell(
                r[category.column], line=line, field=category.count_id
            )
        for group in GROUPS:
            total = sum(int(record[c.count_id]) for c in CATEGORIES if c.group == group)  # type: ignore[arg-type]
            if total != record[HOUSEHOLDS]:
                raise ValueError(
                    f"line {line}: {group} categories sum to {total}, households is "
                    f"{record[HOUSEHOLDS]}"
                )
        records.append(record)
    frame = pd.DataFrame(records)
    if frame["dcs_gn"].duplicated().any():
        raise ValueError("duplicate GN codes in the households workbook")
    return frame


def _district_key(value: object) -> str:
    """The English district name at the end of a trilingual A-series label, normalised."""
    words = re.findall(r"[A-Za-z]+", str(value))
    name = " ".join(words).lower()
    aliases = {"rathnapura": "ratnapura", "nuwaraeliya": "nuwara eliya", "monaragala": "moneragala"}
    return aliases.get(name, name)


def parse_district_table(rows: list[tuple[object, ...]], group: str) -> dict[str, list[int]]:
    """District (and 'sri lanka') -> [households, category counts...] from an A5-A8 table.

    Count rows carry a label in column A; the percentage row under each has none.
    """
    width = 1 + sum(1 for c in CATEGORIES if c.group == group)
    out: dict[str, list[int]] = {}
    for line, r in enumerate(rows, start=1):
        if not r or r[0] is None or not isinstance(r[1], int | float) or isinstance(r[1], bool):
            continue
        key = _district_key(r[0])
        values = [
            _int_cell(v, line=line, field=f"{group} column {j}")
            for j, v in enumerate(r[1 : 1 + width], start=1)
        ]
        if key in out:
            raise ValueError(f"{group} table: {key} appears twice")
        out[key] = values
    return out


def _share(count: float, total: float) -> float | None:
    return round(100.0 * count / total, 4) if total else None


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
        "universe": "households",
        "collection_method": "enumeration",
        "sensitivity": "public",
        "revision_status": "provisional",
        "preferred": True,
        "preferred_reason": (
            "Only claim in this preview: DCS Census 2024 household information by GN."
            if is_count
            else "Derived from DCS Census 2024 household counts; see the indicator definition."
        ),
        "breakdown": None,
        "value": value,
        "value_status": "normal" if value is not None else "not_available",
        "unit": "households" if is_count else "percent",
        "data_nature": "census_count",
        "verification": "machine_extracted",
        "dataset_id": DATASET_ID,
        "snapshot_sha256": snapshot_sha256,
        "source_locator": source_locator,
        "note_ids": note_ids or [],
        "release": None,
    }


def _column_letter(index: int) -> str:
    return openpyxl.utils.get_column_letter(index + 1)  # type: ignore[attr-defined]


@dataclass
class _Aggregate:
    geography_id: str
    level: str
    code: str
    counts: dict[str, float] = field(default_factory=lambda: dict.fromkeys(COUNT_INDICATORS, 0.0))
    first_line: int = 0
    last_line: int = 0
    units: int = 0

    def add(self, record: Row) -> None:
        for indicator in COUNT_INDICATORS:
            self.counts[indicator] += float(record[indicator])
        line = int(record["line"])
        self.first_line = line if not self.units else min(self.first_line, line)
        self.last_line = line if not self.units else max(self.last_line, line)
        self.units += 1


class Census2024TopicTables(Dataset):
    dataset_id = DATASET_ID
    source_id = "dcs"

    def snapshot(self, storage: Storage) -> SnapshotRef:
        wanted = [(HH_FILE, HH_URL), *CHECK_TABLES.values()]
        refs: list[SnapshotRef] = []
        for filename, url in wanted:
            try:
                refs.append(_latest(storage, filename))
            except FileNotFoundError:
                refs.append(
                    snapshot_url(
                        storage,
                        source="dcs",
                        dataset=self.dataset_id,
                        url=url,
                        filename=filename,
                        licence_note=LICENCE_NOTE,
                    )
                )
        return refs[0]

    def extract(self, storage: Storage, ref: SnapshotRef) -> list[Row]:
        hh_ref = _latest(storage, HH_FILE)
        frame = parse_households(_rows(storage, hh_ref))
        self.hh_sha256 = hh_ref.sha256
        self.check_tables: dict[str, dict[str, list[int]]] = {}
        self.check_refs: dict[str, SnapshotRef] = {}
        for group, (filename, _url) in CHECK_TABLES.items():
            check_ref = _latest(storage, filename)
            self.check_refs[group] = check_ref
            self.check_tables[group] = parse_district_table(_rows(storage, check_ref), group)
        self.district_names = {
            int(code): str(name)
            for code, name in frame[["district_code", "district_name"]].drop_duplicates().values
        }
        return frame.to_dict("records")

    def harmonise(self, rows: list[Row], ref: SnapshotRef) -> list[Row]:
        catalog = Path(__file__).resolve().parents[3] / "catalog"
        gn_map, ds_map = _crosswalk(catalog)
        sha = str(getattr(self, "hh_sha256", ref.sha256))
        observations: list[Row] = []
        aggregates: dict[tuple[str, str], _Aggregate] = {}
        self.unmatched_gn: list[str] = []

        for rec in rows:
            ds = str(rec["dcs_ds"])
            district = int(rec["district_code"])
            province = int(rec["province_code"])
            for level, key, geo in (
                ("ds", ds, ds_map.get(ds)),
                ("district", f"{district:02d}", f"LK{district:02d}"),
                ("province", str(province), f"LK{province}"),
                ("country", "LK", "LK"),
            ):
                if geo:
                    aggregates.setdefault((level, key), _Aggregate(geo, level, key)).add(rec)

            geo = gn_map.get(str(rec["dcs_gn"]))
            if not geo:
                self.unmatched_gn.append(str(rec["dcs_gn"]))
                continue
            line = rec["line"]
            observations.append(
                _row(
                    indicator=HOUSEHOLDS,
                    geography_id=geo,
                    value=float(rec[HOUSEHOLDS]),
                    source_locator=(
                        f"{HH_FILE}, sheet 'Households', row {line}, column "
                        f"{_column_letter(HOUSEHOLDS_COLUMN)} ('Number of Households')"
                    ),
                    snapshot_sha256=sha,
                )
            )
            total = float(rec[HOUSEHOLDS])
            for category in CATEGORIES:
                cell = f"row {line}, column {_column_letter(category.column)}"
                label = _heading(category.source_label)
                count = float(rec[category.count_id])
                observations.append(
                    _row(
                        indicator=category.count_id,
                        geography_id=geo,
                        value=count,
                        source_locator=f"{HH_FILE}, sheet 'Households', {cell} ('{label}')",
                        snapshot_sha256=sha,
                    )
                )
                observations.append(
                    _row(
                        indicator=category.share_id,
                        geography_id=geo,
                        value=_share(count, total),
                        source_locator=(
                            f"{HH_FILE}, sheet 'Households', {cell} ÷ column "
                            f"{_column_letter(HOUSEHOLDS_COLUMN)}; derived share"
                        ),
                        snapshot_sha256=sha,
                    )
                )

        # DS 5224 has no spine unit (D-022): it enters Ampara district but has no DS output.
        for (_level, _code), agg in sorted(aggregates.items()):
            locator = (
                f"{HH_FILE}, sheet 'Households', {agg.units} GN rows summed to {agg.level} "
                f"{agg.code}; row range {agg.first_line}-{agg.last_line}"
            )
            for indicator in COUNT_INDICATORS:
                observations.append(
                    _row(
                        indicator=indicator,
                        geography_id=agg.geography_id,
                        value=agg.counts[indicator],
                        source_locator=locator,
                        snapshot_sha256=sha,
                        note_ids=["aggregate"],
                    )
                )
            for category in CATEGORIES:
                observations.append(
                    _row(
                        indicator=category.share_id,
                        geography_id=agg.geography_id,
                        value=_share(agg.counts[category.count_id], agg.counts[HOUSEHOLDS]),
                        source_locator=locator + "; derived share",
                        snapshot_sha256=sha,
                        note_ids=["aggregate"],
                    )
                )
        return observations

    def validate(self, observations: list[Row]) -> QAReport:
        report = super().validate(observations)
        values: dict[tuple[str, str], float | None] = {}
        indicators_by_geo: dict[str, set[str]] = {}
        for row in observations:
            geo = str(row["geography_id"])
            indicator = str(row["indicator_id"])
            indicators_by_geo.setdefault(geo, set()).add(indicator)
            values[(geo, indicator)] = row["value"]
            value = row["value"]
            if value is not None and value < 0:
                report.errors.append(f"{row['claim_id']}: negative value {value}")
            if indicator in SHARE_INDICATORS and value is not None and value > 100:
                report.errors.append(f"{row['claim_id']}: share above 100: {value}")
        for geo, seen in sorted(indicators_by_geo.items()):
            if len(seen) != len(ALL_INDICATORS):
                report.errors.append(
                    f"{geo}: {len(seen)} indicators, expected {len(ALL_INDICATORS)}"
                )

        tables = getattr(self, "check_tables", None)
        names = getattr(self, "district_names", None)
        if tables is None or names is None:
            report.warnings.append("District tables A5-A8 were not compared (validate ran alone).")
        else:
            report.errors.extend(compare_with_district_tables(values, tables, names))

        unmatched = getattr(self, "unmatched_gn", None)
        if unmatched:
            report.warnings.append(
                f"{len(unmatched)} DCS GN units are unmatched in the G02 crosswalk; they enter "
                "DS/district totals but have no GN-level rows. Codes: "
                + ", ".join(sorted(unmatched))
            )
        report.warnings.append(
            "DCS 5224 Kalmunai has no spine equivalent (D-022); its households enter Ampara "
            "district but no DS-level row is published."
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


def compare_with_district_tables(
    values: Mapping[tuple[str, str], float | None],
    tables: dict[str, dict[str, list[int]]],
    district_names: dict[int, str],
) -> list[str]:
    """Every district and the national row of A5-A8 must equal the summed GN values."""
    errors: list[str] = []
    places = {"sri lanka": "LK"} | {
        _district_key(name): f"LK{code:02d}" for code, name in district_names.items()
    }
    for group, table in tables.items():
        indicators = [HOUSEHOLDS, *(c.count_id for c in CATEGORIES if c.group == group)]
        missing = sorted(set(places) - set(table))
        extra = sorted(set(table) - set(places))
        if missing or extra:
            errors.append(f"{group} table: rows not matched; missing {missing}, extra {extra}")
        for key, published in sorted(table.items()):
            geo = places.get(key)
            if geo is None:
                continue
            for indicator, expected in zip(indicators, published, strict=True):
                got = values.get((geo, indicator))
                if got is None or int(got) != expected:
                    errors.append(
                        f"{geo} {indicator}: GN sum {got}, DCS {group} district table {expected}"
                    )
    return errors
