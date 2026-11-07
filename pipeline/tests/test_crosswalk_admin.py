"""Code crosswalk (G02): matching rules on toy data, and checks on the committed CSVs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd
import pytest

from slf.datasets import crosswalk_admin as cw

CATALOG = Path(__file__).resolve().parents[2] / "catalog" / "geographies"


def spine() -> pd.DataFrame:
    rows = [
        ("LK2309", 3, "Nildandahinna", "LK23"),
        ("LK2324", 3, "Walapane", "LK23"),
        ("LK2221", 3, "Ambanganga", "LK22"),
        ("LK2324010", 4, "Deliwala North", "LK2324"),
        ("LK2324020", 4, "High Forest", "LK2324"),
        ("LK2324030", 4, "High Forest", "LK2324"),
        ("LK2309005", 4, "Nildandahinna Town", "LK2309"),
        ("LK5221", 3, "Kalmunai", "LK52"),
    ]
    return pd.DataFrame(rows, columns=["geography_id", "level", "name_en", "parent_id"])


def units(rows: list[tuple[int, str, str, str]]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["level", "code", "name", "parent_code"])
    df["system"] = "toy"
    df["parent_name"] = None
    df["extra"] = None
    df["candidate_pcode"] = "LK" + df["code"]
    return df


def test_normalisation_folds_known_variants() -> None:
    assert cw.norm_loose("Poojapitiya") == cw.norm_loose("Pujapitiya")
    assert cw.similarity("Galle Four Gravets", "Galle 4 Gravets") >= 0.97
    assert cw.similarity("Koralai Pattu North (Vaharai)", "Koralai Pattu North") >= 0.97
    assert cw.tokens_contained("Laggala-Pallegama", "Laggala")
    assert cw.similarity(None, "x") == 0.0 and cw.similarity(float("nan"), "x") == 0.0


def test_drifted_ds_code_matched_by_name_and_gn_follows() -> None:
    u = units(
        [
            (3, "2309", "Walapane", "23"),  # DCS 2309 = Walapane, but LK2309 = Nildandahinna
            (3, "2221", "Ambanganga Korale", "22"),  # code agrees, suffix differs
            (4, "2309010", "Deliwela North", "2309"),  # GN number agrees under remapped DS
        ]
    )
    res = cw.match_system(u, spine(), code_equivalence=True)
    got = dict(zip(res.matches["code"], res.matches["geography_id"], strict=True))
    assert got["2309"] == "LK2324"
    assert got["2221"] == "LK2221"
    assert got["2309010"] == "LK2324010"
    assert res.review.empty


def test_same_name_siblings_go_to_review_not_guessed() -> None:
    u = units([(3, "2324", "Walapane", "23"), (4, "2324099", "High Forest", "2324")])
    res = cw.match_system(u, spine(), code_equivalence=True)
    queued = res.review[res.review["code"] == "2324099"]
    assert queued["reason"].item() == "several same-name units in parent"
    assert "2324099" not in set(res.matches["code"])


def test_two_units_claiming_one_spine_unit_keep_the_stronger() -> None:
    u = units([(3, "5224", "Kalmunai", "52"), (3, "5221", "Kalmunai North Sub", "52")])
    res = cw.match_system(u, spine(), code_equivalence=True)
    assert dict(zip(res.matches["code"], res.matches["geography_id"], strict=True)) == {
        "5224": "LK5221"
    }
    assert (
        "already matched to 5224" in res.review.loc[res.review["code"] == "5221", "reason"].item()
    )


def test_without_code_equivalence_codes_are_ignored() -> None:
    u = units([(3, "2309", "Unknown Place", "23")])
    res = cw.match_system(u, spine(), code_equivalence=False)
    assert res.matches.empty and len(res.review) == 1


def test_inherit_refuses_non_identical_ids() -> None:
    base_units = units([(3, "2324", "Walapane", "23")])
    base = cw.match_system(base_units, spine(), code_equivalence=True)
    other = units([(3, "LK-9999", "X", "23")])
    with pytest.raises(ValueError, match="not a 1:1 relabelling"):
        cw.inherit_matches(other, base_units, base, spine(), to_base={"LK-9999": "9999"})


# --- Committed outputs ------------------------------------------------------------------------


def _codes(system: str) -> pd.DataFrame:
    return pd.read_csv(CATALOG / "codes" / f"{system}.csv", dtype=str)


def test_dcs_codes_map_to_unique_pcodes() -> None:
    dcs = _codes("dcs-census2024")
    assert not dcs["external_code"].duplicated().any(), "a DCS code maps to two places"
    assert not dcs["geography_id"].duplicated().any(), "two DCS codes map to one place"


def test_every_dcs_unit_is_matched_or_queued() -> None:
    dcs = _codes("dcs-census2024")
    review = pd.read_csv(CATALOG / "manual-review.csv", dtype=str)
    queued = review[review["system"] == "dcs_census2024"]
    assert not set(dcs["external_code"]) & set(queued["code"])
    # DCS Census 2024 GN workbook: 340 DS and 14,008 GN units
    assert len(dcs) + len(queued) == 340 + 14008


def test_known_cases_in_committed_crosswalk() -> None:
    dcs = dict(
        zip(*(_codes("dcs-census2024")[c] for c in ("external_code", "geography_id")), strict=True)
    )
    assert dcs["2309"] == "LK2324"  # Walapane (code drift, audit §11)
    assert dcs["2310"] == "LK2309"  # Nildandahinna
    assert dcs["5221"] == "LK-ADM3-P0001"  # Kalmunai North Sub, provisional (D-022)
    assert "5224" not in dcs  # Kalmunai: LK5221 covers 5221 + 5224, so not equivalent
    review = pd.read_csv(CATALOG / "manual-review.csv", dtype=str)
    k = review[(review["system"] == "dcs_census2024") & (review["code"] == "5224")]
    assert "not equivalent" in k["reason"].item().lower()


def test_ldl_is_identical_to_spine_codes() -> None:
    ldl = _codes("ldl")
    assert bool((ldl["external_code"] == ldl["geography_id"]).all())
    assert Counter(ldl["geography_id"].str.len()) == {6: 339, 9: 14043}


def test_manual_decision_overrides_automatic_match() -> None:
    u = units([(3, "2309", "Walapane", "23")])
    res = cw.match_system(u, spine(), code_equivalence=True)
    manual = pd.DataFrame(
        [{"system": "toy", "level": "3", "code": "2309", "decision": "review", "geography_id": None,
          "evidence": "not equivalent", "decided_by": "lead", "date": "2026-11-08"}]
    )  # fmt: skip
    out = cw.apply_manual(res, "toy", manual, spine())
    assert out.matches.empty
    assert "automatic match was LK2324" in out.review["reason"].item()
    assert "LK2324" in set(out.no_counterpart["geography_id"])
