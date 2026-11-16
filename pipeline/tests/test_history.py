"""Tests for slf.history (G06): 2012 GN-file parsing, GN matching, change classification."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pandas as pd
import pytest

from slf import history


def test_parse_line_variants() -> None:
    assert history.parse_line("Sri Lanka 20,359,439 9,856,634 10,502,805") == (
        "Sri Lanka", None, 20359439, 9856634, 10502805,
    )  # fmt: skip
    assert history.parse_line("Pettah 1,924 1,854 70") == ("Pettah", None, 1924, 1854, 70)
    assert history.parse_line("Yati Hanguranketha 495B 799 367 432") == (
        "Yati Hanguranketha", "495B", 799, 367, 432,
    )  # fmt: skip
    # Number printed with a space before its suffix.
    assert history.parse_line("Evariwatta 175 A 4,527 2,200 2,327") == (
        "Evariwatta", "175A", 4527, 2200, 2327,
    )  # fmt: skip
    assert history.parse_line("Nedunkulam J/61 722 350 372") == (
        "Nedunkulam",
        "J/61",
        722,
        350,
        372,
    )
    assert history.parse_line("Wetakoluwewa E438D 1,406 700 706") == (
        "Wetakoluwewa", "E438D", 1406, 700, 706,
    )  # fmt: skip
    # A GN listed without figures.
    assert history.parse_line("Victoria 825") == ("Victoria", "825", None, None, None)
    # Male + female must equal the total, otherwise the line is not a data row.
    assert history.parse_line("Odd 100 60 50") is None
    assert history.parse_line("12") is None


def test_norm_gn_number() -> None:
    assert history.norm_gn_number("J-37") == history.norm_gn_number("J/37") == "J37"
    assert history.norm_gn_number("06") == "6"
    assert history.norm_gn_number("W/86 G") == "W86G"
    assert history.norm_gn_number(None) is None


def _pages(tmp_path: Path, text: str) -> Path:
    d = tmp_path / "gn2012"
    d.mkdir()
    (d / "page-001.txt").write_text(text, encoding="utf-8")
    return d


GN_FILE = """Census of Population and Housing 2012
Population by GN division and sex 2012
Sri Lanka 1,000 500 500
Colombo 1,000 500 500
Alpha 600 300 300
Aone 1A 400 200 200
Atwo 1B 200 100 100
Ablank 1C
Beta 400 200 200
Bone 2A 400 200 200
1
"""


def test_parse_gn_2012_rebuilds_hierarchy(tmp_path: Path) -> None:
    rows = history.parse_gn_2012(_pages(tmp_path, GN_FILE))
    assert rows.national["total"] == 1000
    assert list(rows.ds["name"]) == ["Alpha", "Beta"]
    assert list(rows.ds["ds_2012"]) == ["11-01", "11-02"]
    gn = rows.gn
    assert list(gn["name"]) == ["Aone", "Atwo", "Ablank", "Bone"]
    # The blank GN after Alpha's GNs add up still belongs to Alpha (DS row precedes its GNs).
    assert gn.loc[gn["name"] == "Ablank", "ds_2012"].item() == "11-01"
    assert rows.unparsed == []


def test_parse_gn_2012_raises_when_arithmetic_breaks(tmp_path: Path) -> None:
    bad = GN_FILE.replace("Atwo 1B 200 100 100", "Atwo 1B 100 50 50")
    with pytest.raises(ValueError):
        history.parse_gn_2012(_pages(tmp_path, bad))


def _gn24(rows: Sequence[tuple[str, str, str, str | None, int]]) -> pd.DataFrame:
    """(dcs_ds, ds_name, gn_name, gn_number, population) -> GN workbook-like frame."""
    out = []
    for n, (ds, ds_name, name, number, pop) in enumerate(rows, start=1):
        out.append(dict(dcs_gn=f"{ds}{n:03d}", dcs_ds=ds, ds_name=ds_name, district_code=11,
                        district_name="Colombo", gn_name=name, gn_number=number,
                        population_total=pop, line=n + 5))  # fmt: skip
    return pd.DataFrame(out)


def _gn12(rows: Sequence[tuple[str, str, str, str | None, int | None]]) -> pd.DataFrame:
    """(ds_2012, ds_name, gn_name, gn_number, population) -> parsed 2012 GN frame."""
    return pd.DataFrame(
        [dict(ds_2012=ds, ds_name=dsn, district_code=11, name=name, gn_number=no, total=pop,
              male=None, female=None, page=1, line=i)
         for i, (ds, dsn, name, no, pop) in enumerate(rows, start=1)]
    )  # fmt: skip


def test_match_gns_layers_and_duplicates() -> None:
    gn12 = _gn12([
        ("11-01", "Alpha", "Aone", "1A", 10),        # number and name
        ("11-01", "Alpha", "Atwo Old", "1B", 20),    # number only (renamed GN)
        ("11-01", "Alpha", "Athree", None, 30),      # name only
        ("11-02", "Beta", "Dup", "9", 40),           # listed under two DS (layer 4)
        ("11-03", "Gamma", "Dup", "9", 50),
        ("11-03", "Gamma", "Gone", "7", 60),         # unmatched
    ])  # fmt: skip
    gn24 = _gn24([
        ("1103", "Alpha", "Aone", "1-A", 11),
        ("1103", "Alpha", "Atwo New", "1B", 21),
        ("1103", "Alpha", "Athree", None, 31),
        ("1106", "Beta", "Dup", "9", 41),
        ("1109", "Gamma", "Dup", "9", 51),
    ])  # fmt: skip
    m = history.match_gns(gn12, gn24).set_index("name")
    assert m.loc["Aone", "match_layer"] == "number_and_name"
    assert m.loc["Atwo Old", "match_layer"] == "number"
    assert m.loc["Athree", "match_layer"] == "name"
    dup = m.loc["Dup"]
    assert set(dup["match_layer"]) == {"number_name_and_ds"}
    assert set(zip(dup["ds_2012"], dup["ds_2024"], strict=True)) == {
        ("11-02", "1106"), ("11-03", "1109"),
    }  # fmt: skip
    assert pd.isna(m.loc["Gone", "gn_2024"])


def _scenario() -> history.Result:
    # 11-01 Alpha unchanged; 11-02 Beta split into Beta + Delta; 11-03 Gamma renamed to
    # Gamma Pattu; 11-04 Eps loses one of eleven GNs to 11-05 Zeta (a transfer).
    gn12 = _gn12(
        [("11-01", "Alpha", f"A{i}", f"A{i}", 100) for i in range(3)]
        + [("11-02", "Beta", f"B{i}", f"B{i}", 100) for i in range(4)]
        + [("11-03", "Gamma", "G0", "G0", 50)]
        + [("11-04", "Eps", f"E{i}", f"E{i}", 10) for i in range(11)]
        + [("11-05", "Zeta", f"Z{i}", f"Z{i}", 10) for i in range(10)]
    )
    gn24 = _gn24(
        [("1101", "Alpha", f"A{i}", f"A{i}", 110) for i in range(3)]
        + [("1102", "Beta", f"B{i}", f"B{i}", 120) for i in range(3)]
        + [("1108", "Delta", "B3", "B3", 130)]
        + [("1103", "Gamma Pattu", "G0", "G0", 60)]
        + [("1104", "Eps", f"E{i}", f"E{i}", 10) for i in range(10)]
        + [("1105", "Zeta", f"Z{i}", f"Z{i}", 10) for i in range(10)]
        + [("1105", "Zeta", "E10", "E10", 10)]
    )
    ds12 = (
        gn12.groupby(["ds_2012", "ds_name"], as_index=False)
        .agg(total=("total", "sum"))
        .rename(columns={"ds_name": "name"})
    )
    spine = {"1101": "LK1101", "1102": "LK1102", "1108": "LK1108", "1103": "LK1103",
             "1104": "LK1104", "1105": "LK1105"}  # fmt: skip
    return history.classify(ds12, history.match_gns(gn12, gn24), gn24, spine)


def test_classify_change_types_and_identity() -> None:
    res = _scenario()
    u12 = res.units_2012.set_index("ds_2012")
    assert u12.loc["11-01", "change_type"] == "unchanged"
    assert u12.loc["11-02", "change_type"] == "split"
    assert u12.loc["11-03", "change_type"] == "renamed"
    assert u12.loc["11-04", "change_type"] == "boundary_adjusted"
    assert u12.loc["11-05", "change_type"] == "boundary_adjusted"
    # Only the split unit is retired with a vintage id; the others keep the spine id.
    assert u12.loc["11-02", "geography_id"] == "LK-ADM3-V2012-11-02"
    assert u12.loc["11-01", "geography_id"] == "LK1101"
    u24 = res.units_2024.set_index("dcs_ds")
    assert u24.loc["1102", "change_type"] == "split_remainder"
    assert u24.loc["1108", "change_type"] == "new"
    assert u24.loc["1103", "change_type"] == "renamed"


def test_classify_comparisons_and_relations() -> None:
    res = _scenario()
    c = res.comparison.set_index("dcs_ds")
    assert c.loc["1101", "comparison"] == "exact"
    assert c.loc["1101", "pop_2012"] == 300 and c.loc["1101", "pop_2024"] == 330
    assert c.loc["1103", "comparison"] == "exact"  # a rename alone keeps the comparison exact
    for j in ("1102", "1108", "1104", "1105"):
        assert c.loc[j, "comparison"] == "approximate"
    assert c.loc["1108", "pop_2012"] == 100  # rebuilt from the one GN that moved
    # Every 2012 person lands in exactly one 2024 unit.
    assert sum(c["pop_2012"].tolist()) == sum(res.units_2012["total"].tolist())
    rel = res.relations
    succ = rel[(rel["relation"] == "succeeded_by") & (rel["geography_id"] == "LK-ADM3-V2012-11-02")]
    assert set(succ["related_id"]) == {"LK1102", "LK1108"}
    assert sum(succ["weight"].tolist()) == pytest.approx(1.0)
    assert set(rel["relation"]) == {"succeeded_by", "preceded_by"}
    groups = res.groups
    assert set(groups["comparison"]) == {"exact"}
    beta = groups[groups["ds_2012"] == "11-02"].iloc[0]
    assert (beta["pop_2012"], beta["pop_2024"]) == (400, 490)


TABLE_3_3 = """Sri Lanka 14,846,274 18,797,257 20,359,439 21,781,800 1.2 1.0 0.7 0.5
Colombo 1,675,847 2,239,696 2,324,349 2,375,415 1.4 1.1 0.3 0.2
Mullaitivu 73,886 - 92,238 122,619 0.7 2.2
Trincomalee 250,771 - 379,541 442,745 - 1.3 - 1.2
"""


def test_parse_table_3_3_and_rate_formula() -> None:
    t = history.parse_table_3_3(TABLE_3_3).set_index("district")
    assert t.loc["Sri Lanka", "p2024"] == 21781800
    assert pd.isna(t.loc["Mullaitivu", "p2001"])
    assert t.loc["Trincomalee", "rate_2012_2024"] == 1.2
    # DCS's average annual growth rate is exponential: Mullaitivu 2012-2024 is 2.2.
    assert round(history.exp_rate(92238, 122619, history.YEARS), 1) == 2.2
    assert round(history.exp_rate(20359439, 21781800, history.YEARS), 1) == 0.5


def test_check_transcription_flags_values_not_in_text() -> None:
    t = pd.DataFrame(
        {"district": ["Sri Lanka", "A", "B"], "1871": ["10.0", "4.0", "6.0"]}, dtype=str
    )
    ok = history.check_transcription(t, "Sri Lanka 10.0 A 4.0 B 6.0")
    assert ok["missing_from_text_layer"] == {} and ok["column_sum_minus_total"] == {"1871": 0.0}
    bad = history.check_transcription(t, "Sri Lanka 10.0 A 4.0 B 6.1")
    assert bad["missing_from_text_layer"] == {"6.0": 1}


def test_district_series_labels() -> None:
    tr = pd.DataFrame(
        {"district": ["Sri Lanka", "Gampaha", "Jaffna"], "1971": ["1.0", "..", "0.5"],
         "2001": ["2.0", "1.0", "0.6"], "2012": ["3.0", "1.5", "0.7"]}, dtype=str,
    )  # fmt: skip
    s = history.district_series(tr, history.parse_table_3_3(TABLE_3_3))
    a = s[s["source"].str.startswith("DCS Statistical Abstract")].set_index(["district", "year"])
    assert a.loc[("Gampaha", 1971), "value_status"] == "not_available"
    assert a.loc[("Jaffna", 1971), "comparison_to_2024"] == "approximate"
    assert a.loc[("Jaffna", 2001), "value_status"] == "estimate"
    assert a.loc[("Jaffna", 2001), "comparison_to_2024"] == "approximate"
    assert a.loc[("Gampaha", 2001), "comparison_to_2024"] == "exact"
    assert "1978" in a.loc[("Gampaha", 2012), "note"]
