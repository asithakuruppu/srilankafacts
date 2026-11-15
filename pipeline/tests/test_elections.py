"""Election results (Presidential Election 2024) and electoral geography (G05 electoral)."""

from __future__ import annotations

import json

import geopandas as gpd
import pytest
from shapely.geometry import box

from slf.datasets import election_results as er
from slf.datasets import electoral_geography as eg
from slf.datasets.election_parse import (
    CANDIDATES,
    Box,
    SheetPage,
    normalise_code,
    parse_sheet,
)
from slf.datasets.election_snapshot import pdf_links

# --- party codes and links -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("token", "code"),
    [("NPP", "NPP"), ("INDIO", "IND10"), ("IND1O", "IND10"), ("lND7", "IND7"), ("IND3", None)],
)
def test_normalise_code(token: str, code: str | None) -> None:
    assert normalise_code(token) == code


def test_pdf_links_skips_placeholders_and_duplicates() -> None:
    base = "https://elections.gov.lk/web/wp-content/uploads/2024/09/PRE_2024_Results/"
    html = "".join(
        f'<a href="{base}{n}">x</a>' for n in ("1_AA.pdf", "1_PV.pdf", "1_AA.pdf", "XXXVanni.pdf")
    )
    assert [n for _u, n in pdf_links(html)] == ["1_AA.pdf", "1_PV.pdf"]


# --- result sheets ---------------------------------------------------------------------------


def _votes(valid: int) -> dict[str, int]:
    """38 candidate counts summing to ``valid``: most votes to two candidates."""
    votes = {code: 3 + i for i, (_b, code, _n) in enumerate(CANDIDATES)}
    rest = valid - sum(votes.values())
    votes["NPP"] += rest * 6 // 10
    votes["SJB"] += rest - rest * 6 // 10
    return votes


def _sheet_pages(
    votes: dict[str, int],
    valid: int,
    rejected: int,
    electors: int,
    *,
    unread: tuple[str, ...] = (),
    misread: dict[str, int] | None = None,
    no_pct: tuple[str, ...] = (),
) -> list[SheetPage]:
    """One synthetic page: party codes at x=0.65, votes at 0.78, percentages at 0.88."""
    misread = misread or {}
    ocr: list[Box] = [
        Box("Polling Division : B - Colombo Central", 0.05, 0.02, 0.5, 0.01),
        Box("Electoral District: 1 - Colombo", 0.05, 0.035, 0.5, 0.01),
        Box("Votes Obtained", 0.72, 0.05, 0.1, 0.01),
        Box("Percentage", 0.85, 0.05, 0.08, 0.01),
    ]
    for i, (_b, code, _n) in enumerate(CANDIDATES):
        y = 0.07 + 0.018 * i
        ocr.append(Box(code, 0.65, y, 0.04, 0.01))
        if code not in unread:
            ocr.append(Box(f"{misread.get(code, votes[code]):,}", 0.77, y, 0.03, 0.01))
        if code not in no_pct:
            ocr.append(Box(f"{100 * votes[code] / valid:.2f} %", 0.87, y, 0.04, 0.01))
    polled = valid + rejected
    for j, (label, value) in enumerate(
        [
            ("Total Number of Valid Votes :", valid),
            ("Number of Rejected Votes :", rejected),
            ("Number of Votes Polled :", polled),
            ("Number of Registered Electors :", electors),
        ]
    ):
        y = 0.8 + 0.03 * j
        ocr.append(Box(label, 0.45, y, 0.25, 0.01))
        ocr.append(Box(f"{value:,}", 0.77, y, 0.04, 0.01))
    return [SheetPage(1, ocr, [], "", [])]


def test_parse_sheet_reads_a_clean_sheet() -> None:
    votes = _votes(50_000)
    s = parse_sheet("1_B.pdf", _sheet_pages(votes, 50_000, 1_000, 70_000))
    assert (s.kind, s.ed_number, s.pd_letter, s.pd_name) == ("pd", 1, "B", "Colombo Central")
    assert s.complete and not s.problems
    assert {c: r.value for c, r in s.candidates.items()} == votes
    assert s.totals["polled"].value == 51_000


def test_parse_sheet_derives_one_unread_value_from_total_and_percentage() -> None:
    votes = _votes(50_000)
    s = parse_sheet("1_B.pdf", _sheet_pages(votes, 50_000, 1_000, 70_000, unread=("IND5",)))
    assert s.candidates["IND5"].value == votes["IND5"]
    assert s.candidates["IND5"].how == "derived"
    assert s.derived == ["IND5"] and not s.problems


def test_parse_sheet_withholds_unconfirmed_values_when_sheet_does_not_add_up() -> None:
    votes = _votes(50_000)
    pages = _sheet_pages(
        votes,
        50_000,
        1_000,
        70_000,
        unread=("IND5", "IND6"),  # two unread small values: not uniquely derivable
        misread={"SLCP": 9},
        no_pct=("SLCP", "IND5", "IND6"),
    )
    # a second read agreeing with the misread value (as two OCR passes of one row can)
    pages[0].strip.append(Box("9", 0.77, 0.07 + 0.018 * 8, 0.03, 0.01))
    s = parse_sheet("1_B.pdf", pages)
    assert s.candidates["SLCP"].value is None
    assert s.candidates["SLCP"].how == "withheld"
    assert s.candidates["NPP"].value == votes["NPP"]  # confirmed by its printed percentage
    assert not s.complete


# --- observations ----------------------------------------------------------------------------


def _raw(geo_kind: str, letter: str | None, indicator: str, value: float | None, **bd) -> dict:
    return {
        "geo": eg.pd_id(1, letter or "") if geo_kind == "pd" else eg.ed_id(1),
        "indicator_id": indicator,
        "breakdown": ({} if geo_kind == "pd" else {"vote_type": "postal"}) | bd,
        "value": value,
        "how": "ocr",
        "locator": "x",
        "sha": "a" * 64,
        "file": f"1_{letter or 'PV'}.pdf",
        "kind": geo_kind,
        "ed": 1,
    }


def test_ed_total_is_pds_plus_postal_and_postal_stays_on_the_ed() -> None:
    rows = [
        _raw("pd", "A", "electors_registered", 100),
        _raw("pd", "B", "electors_registered", 200),
        _raw("postal", None, "electors_registered", 10),
        _raw("pd", "A", "votes_polled", 80),
        _raw("pd", "B", "votes_polled", None),
        _raw("postal", None, "votes_polled", 9),
    ]
    obs = [er.observation(r) for r in rows]
    agg = {(o["geography_id"], o["indicator_id"]): o for o in er.aggregate_rows(rows)}
    assert agg[("LK-ED-01", "electors_registered")]["value"] == 310
    assert agg[("LK", "electors_registered")]["value"] == 310
    assert agg[("LK-ED-01", "votes_polled")]["value_status"] == "not_available"
    postal = [o for o in obs if o["breakdown"] == {"vote_type": "postal"}]
    assert {o["geography_id"] for o in postal} == {"LK-ED-01"}
    assert not any(o["geography_id"].startswith("LK-PD") for o in postal)


def test_shares_are_recomputed_from_counts() -> None:
    rows = [
        _raw("pd", "A", "electors_registered", 200),
        _raw("pd", "A", "votes_polled", 150),
        _raw("pd", "A", "votes_valid", 100),
        _raw("pd", "A", "votes_candidate", 25, party="NPP", ballot_number="16"),
    ]
    obs = [er.observation(r) for r in rows]
    shares = {o["indicator_id"]: o["value"] for o in er.share_rows(obs)}
    assert shares == {"turnout": 75.0, "votes_candidate_share": 25.0}


# --- register and geography ------------------------------------------------------------------

REGISTER_PAGE = """A Colombo North 1 2 3 4 5 6 7 8 9 10
B Colombo Central 10 20 30 40 50 60 70 80 90 100
11 22 33 44 55 66 77 88 99 110
Electoral District : - 01 - Colombo
"""


def test_parse_register() -> None:
    reg = eg.parse_register({1: REGISTER_PAGE})
    assert not reg.problems
    assert [p.geography_id for p in reg.pds] == ["LK-PD-01A", "LK-PD-01B"]
    assert reg.pds[1].name == "Colombo Central" and reg.pds[1].electors[2024] == 90
    assert reg.ed_totals[1][2025] == 110


def test_parse_register_reports_a_total_that_does_not_match() -> None:
    reg = eg.parse_register({1: REGISTER_PAGE.replace("110\n", "111\n")})
    assert any("match no total line" in p for p in reg.problems)


def test_ed_grouping_covers_25_districts_once() -> None:
    districts = [d for ds in eg.ED_DISTRICTS.values() for d, _ in ds]
    assert len(eg.ED_DISTRICTS) == 22 and len(districts) == 25 == len(set(districts))
    rows = eg.ed_rows()
    assert all(r["relation"] == "composed_of" and r["weight"] == 1.0 for r in rows)


def test_weight_sums_iou_and_denominators() -> None:
    comp = eg.Composition({"U1": {"g1": 1.0, "g2": 0.5}, "U2": {"g2": 0.5}}, "manual", "test")
    assert eg.weight_sums(comp, ["g1", "g2", "g3"]) == {1.0: 2, 0.0: 1}
    gns = gpd.GeoSeries({"g1": box(80, 7, 80.01, 7.01), "g2": box(80.01, 7, 80.02, 7.01)}, crs=4326)
    iou = eg.iou_table({"U1": box(80, 7, 80.02, 7.01)}, gns, comp).set_index("unit")
    assert iou.at["U1", "iou"] == pytest.approx(1.0, abs=1e-3)
    import pandas as pd

    values = pd.DataFrame(
        {"indicator_id": ["population_total"] * 2, "geography_id": ["g1", "g2"], "value": [10, 40]}
    )
    den = eg.denominators(comp, values, ["population_total"]).set_index("geography_id")
    assert den.at["U1", "population_total"] == 30 and den.at["U2", "population_total"] == 20


def test_read_geojson_accepts_nuuuwan_ring_lists(tmp_path) -> None:
    from slf.snapshot import snapshot_bytes
    from slf.storage import LocalStorage

    storage = LocalStorage(tmp_path)
    ring = [[80, 7], [80.01, 7], [80.01, 7.01], [80, 7.01], [80, 7]]
    ref = snapshot_bytes(
        storage, source="t", dataset="d", filename="g.json", content=json.dumps([ring]).encode()
    )
    geom = eg.read_geojson(storage, ref)
    assert geom.area == pytest.approx(0.0001)
