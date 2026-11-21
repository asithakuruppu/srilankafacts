"""HeiGIT and DesInventar crosswalks and indicators (synthetic inputs, nothing from the drive)."""

import json
from pathlib import Path

import pandas as pd

from slf import hazard_access as h

SPINE = [
    ("LK", 0, "Sri Lanka", "None"),
    ("LK4", 1, "Northern", "LK"),
    ("LK8", 1, "Uva", "LK"),
    ("LK41", 2, "Jaffna", "LK4"),
    ("LK42", 2, "Mannar", "LK4"),
    ("LK45", 2, "Kilinochchi", "LK4"),
    ("LK81", 2, "Badulla", "LK8"),
    ("LK82", 2, "Monaragala", "LK8"),
]


def spine(tmp: Path) -> Path:
    d = tmp / "spine"
    d.mkdir()
    pd.DataFrame(SPINE, columns=["geography_id", "level", "name_en", "parent_id"]).to_parquet(
        d / "geographies.parquet"
    )
    return d


def put(raw: Path, source: str, dataset: str, name: str, text: str) -> None:
    folder = raw / source / dataset / "20261117T000000Z"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(text, encoding="utf-8")
    (folder / f"{name}.meta.json").write_text(json.dumps({"sha256": "ab" * 32, "url": "u"}))


def test_norm_drops_generic_words() -> None:
    assert h.norm("Ampara District") == h.norm("AMPARA") == "ampara"
    assert h.norm("Uva Province") == "uva"


def test_event_year_rejects_impossible_dates() -> None:
    assert h.event_year("02/06/2008") == 2008
    assert h.event_year("2006/1/0") is None
    assert h.event_year("31/02/2005") == 2005  # day/month ranges only; the year is what we use
    assert h.event_year("/0/0") is None


def test_heigit_iso_not_used_as_pcode(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    rows = [
        "name,iso,id,country,admin_level,category,range_type,range,population_type,population,"
        "population_share,population_interval,population_interval_share",
    ]
    for name, iso, level in [
        ("Northern Province", "LK-4", "ADM1"),
        ("Uva Province", "LK-8", "ADM1"),
        ("Jaffna District", "LK-41", "ADM2"),
        ("Kilinochchi District", "LK-42", "ADM2"),
        ("Mannar District", "LK-43", "ADM2"),
        ("Badulla District", "LK-81", "ADM2"),
        ("Monaragala District", "LK-82", "ADM2"),
        ("Atlantis District", "LK-99", "ADM2"),
    ]:
        rows.append(f"{name},{iso},x,LKA,{level},hospitals,TIME,1800,total,10,50.5,10,50.5")
    put(raw, "heigit", "heigit-accessibility", "LKA_hospitals_access_long.csv", "\n".join(rows))
    cw = h.crosswalk_heigit(raw, spine(tmp_path))
    mapped = cw.by_code()
    assert mapped["LK-42"] == "LK45" and mapped["LK-43"] == "LK42"  # differs from the ISO number
    assert mapped["LK-82"] == "LK82" and mapped["LKA"] == "LK"
    assert any("Atlantis" in u for u in cw.unmatched)  # never forced
    assert "DISAGREES" in next(r["notes"] for r in cw.rows if r["external_code"] == "LK-42")
    assert all(r["match_method"] in {"name_and_parent", "exact_code"} for r in cw.rows)


def test_alias_requires_free_parent_slot(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    spine_dir = spine(tmp_path)
    import geopandas as gpd

    work = tmp_path / "work"
    work.mkdir()
    for stem, data in {
        "provi": {"PROVINCE_N": ["Uva"], "pro_code": ["lka008"]},
        "ditric": {
            "PROVINCE_N": ["Uva", "Uva"],
            "DISTRICT_N": ["Badulla", "Moneragala"],
            "pro_code": ["lka008", "lka008"],
            "dis_code": ["lka008001", "lka008002"],
        },
        "dsdivi": {"DSD_N": ["x"]},
    }.items():
        gpd.GeoDataFrame(
            data,
            geometry=gpd.points_from_xy(
                [0] * len(next(iter(data.values()))), [0] * len(next(iter(data.values())))
            ),
        ).to_file(work / f"{stem}.shp")
    import zipfile

    folder = raw / "undrr-desinventar" / "desinventar-sri-lanka" / "20261117T000000Z"
    folder.mkdir(parents=True)
    with zipfile.ZipFile(folder / "srilanka.zip", "w") as z:
        for f in work.iterdir():
            z.write(f, f.name)
    (folder / "srilanka.zip.meta.json").write_text(json.dumps({"sha256": "ab" * 32}))
    cw = h.crosswalk_desinventar(raw, spine_dir, tmp_path / "out")
    by = cw.by_code()
    assert by["lka008001"] == "LK81" and by["lka008002"] == "LK82"
    method = {r["external_code"]: r["match_method"] for r in cw.rows}
    assert method["lka008002"] == "manual" and method["lka008001"] == "name_and_parent"
    assert cw.unmatched == []


def test_events_counted_by_district_year(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    head = "Serial\tEvent\tCode Region\tCode District\tCode Commune\tLocation\tDate (YMD)"
    lines = [
        head,
        "A\tFLOOD\tlka008\tlka008001\t\t\t02/06/2008",
        "B\tFLOOD\tlka008\tlka008001\t\t\t03/06/2008",
        "C\tEPIDEMIC\tlka008\tlka008001\t\t\t03/06/2008",
        "D\tFLOOD\tlka008\tlka008001\t\t\t2/29",  # bad date
        "E\tFLOOD\tlka008\t\t\t\t02/06/2008",  # no district
        "F\tFLOOD\tlka008\tlka009009\t\t\t02/06/2008",  # code not in the crosswalk
        "G\tDROUGHT\tlka009\tlka008001\t\t\t02/06/2008",  # province contradicts district
    ]
    put(
        raw,
        "undrr-desinventar",
        "desinventar-sri-lanka",
        "di_report-srilanka.xls",
        "\n".join(lines),
    )
    rows, qa, _ = h.ingest_desinventar(raw, {"lka008001": "LK81"})
    flood = [r for r in rows if r["indicator_id"] == "di_flood_records"]
    assert [(r["geography_id"], r["period"], r["value"]) for r in flood] == [("LK81", "2008", 2.0)]
    assert flood[0]["support_type"] == "area_total" and flood[0]["time_support"] == "interval_total"
    assert not [r for r in rows if r["indicator_id"] == "di_drought_records"]
    assert [r["value"] for r in rows if r["indicator_id"] == "di_disaster_records"] == [2.0]
    assert qa.no_district == 1 and qa.bad_date == 1 and qa.province_mismatch == 2
    assert qa.unmatched_code == {"lka009009": 1}
    assert qa.total == 7 and qa.used == 3  # A, B, C counted; D, E, F, G reported


def test_access_ingest_only_total_cumulative(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    cols = (
        "name,iso,id,country,admin_level,category,range_type,range,population_type,population,"
        "population_share,population_interval,population_interval_share"
    )
    text = "\n".join(
        [
            cols,
            "Jaffna District,LK-41,x,LKA,ADM2,hospitals,TIME,1800,total,10,80.5,10,1.0",
            "Jaffna District,LK-41,x,LKA,ADM2,hospitals,TIME,1800,elderly,10,70.0,10,1.0",
            "Jaffna District,LK-41,x,LKA,ADM2,hospitals,TIME,600,total,10,60.0,10,60.0",
            "Nowhere,LK-99,x,LKA,ADM2,hospitals,TIME,1800,total,10,1.0,10,1.0",
        ]
    )
    for name in (
        "LKA_hospitals_access_long.csv",
        "LKA_primary_healthcare_access_long.csv",
        "LKA_education_access_long.csv",
    ):
        put(
            raw,
            "heigit",
            "heigit-accessibility",
            name,
            text if name.startswith("LKA_hosp") else cols,
        )
    unmatched: list[str] = []
    rows = h.ingest_heigit_access(raw, {"LK-41": "LK41"}, unmatched)
    assert [(r["indicator_id"], r["value"]) for r in rows] == [("access_hospital_30min", 80.5)]
    assert unmatched == ["heigit access: LK-99 Nowhere"]
    assert rows[0]["support_type"] == "area_mean" and rows[0]["verification"] == "machine_extracted"


def test_ds_mapping_refuses_renames_and_splits(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog" / "geographies"
    (catalog / "codes").mkdir(parents=True)
    (catalog / "relations").mkdir()
    pd.DataFrame(
        {
            "external_code": ["8101", "8102", "8103", "8104"],
            "geography_id": ["LK8101", "LK8102", "LK8103", "LK8104"],
        }
    ).to_csv(catalog / "codes" / "dcs-census2024.csv", index=False)
    pd.DataFrame(
        {"relation": ["succeeded_by"], "related_id": ["LK8104"]},
    ).to_csv(catalog / "relations" / "succession_ds_2012-2024.csv", index=False)
    spine_ds = [
        h.Place("LK8101", "Badulla", "LK81"),
        h.Place("LK8102", "Ella", "LK81"),
        h.Place("LK8103", "Seethawaka", "LK81"),
        h.Place("LK8104", "Haputale", "LK81"),
        h.Place("LK8105", "Passara", "LK81"),
    ]
    ds = pd.DataFrame(
        {
            "DISTRICT_N": ["Badulla"] * 6,
            "dis_code": ["lka008001"] * 6,
            "ds_code": [f"lka008001{n:03d}" for n in range(1, 7)],
            "DSD_N": ["Badulla", "Ella(Town)", "Hanwella", "Haputale", "Passara", "Nowhere"],
            # 5 has no DCS code, so it is matched by name; 6 matches nothing
            "DSDCODE4": [8101, 8102, 8103, 8104, None, None],
        }
    )
    cw = h.Crosswalk("desinventar")
    h._map_ds(cw, spine_ds, ds, {"lka008001": "LK81"}, tmp_path / "catalog")
    got = {r["external_code"]: (r["geography_id"], r["match_method"]) for r in cw.rows}
    assert got == {
        "lka008001001": ("LK8101", "exact_code"),
        "lka008001002": ("LK8102", "exact_code"),  # name found inside the brackets? no: via code
        "lka008001005": ("LK8105", "name_and_parent"),
    }
    assert any("Hanwella" in r and "renamed" in r for r in cw.review)  # code agrees, name does not
    assert any("Haputale" in r and "split" in r for r in cw.review)  # lands on a split unit
    assert any("Nowhere" in u for u in cw.unmatched)  # never forced
