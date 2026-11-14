"""The topic-table re-trace must catch wrong values, wrong row counts and wrong place files."""

from __future__ import annotations

import json
from pathlib import Path

import openpyxl
import pandas as pd

from slf import audit_topics as at
from slf.audit import sha256

HEADER = ["Province Code", "Province Name", "District Code", "District Name", "DS_Division Code"]
HEADER += ["DS_Division Name", "GN_Division Code", "GN_Division Name", "GN_Division Number"]
HEADER += ["Number of Households", "Pipe"]
# province, district, DS, GN, households (J), piped water (K); data from Excel row 5
GN = [(1, 11, 3, 5, 100, 40), (1, 11, 3, 10, 200, 50), (1, 11, 6, 5, 50, 10), (2, 21, 1, 5, 10, 1)]


def _workbook(tmp_path: Path) -> tuple[Path, str]:
    raw = tmp_path / "raw"
    raw.mkdir()
    wb = openpyxl.Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Households"
    ws.append(["Census of Population and Housing 2024"])
    ws.append([])
    ws.append(HEADER)
    ws.append([])
    for p, d, ds, gn, hh, pipe in GN:
        # DCS writes numbers as text
        ws.append([str(p), "P", str(d), "D", str(ds), "S", str(gn), "G", " ", str(hh), str(pipe)])
    path = raw / "HH_GND_excel.xlsx"
    wb.save(path)
    return raw, sha256(path)


def _obs(sha: str, rows: list[tuple[str, str, float | None, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "claim_id": f"c:{geo}:{ind}",
                "indicator_id": ind,
                "geography_id": geo,
                "value": value,
                "value_status": "normal" if value is not None else "not_available",
                "snapshot_sha256": sha,
                "source_locator": loc,
                "release": "v0",
            }
            for ind, geo, value, loc in rows
        ]
    )


def _rows(sha: str, pipe_ds_1103: float = 90.0) -> list[tuple[str, str, float | None, str]]:
    f = "HH_GND_excel.xlsx, sheet 'Households'"
    return [
        ("households_water_pipe", "LK1103005", 40.0, f"{f}, row 5, column K ('Pipe')"),
        (
            "households_water_pipe_share",
            "LK1103005",
            40.0,
            f"{f}, row 5, column K ÷ column J; derived share",
        ),
        (
            "households_water_pipe",
            "LK1103",
            pipe_ds_1103,
            f"{f}, 2 GN rows summed to ds 1103; row range 5-6",
        ),
        (
            "households_water_pipe_share",
            "LK1103",
            30.0,
            f"{f}, 2 GN rows summed to ds 1103; row range 5-6; derived share",
        ),
        (
            "households_water_pipe",
            "LK1",
            100.0,
            f"{f}, 3 GN rows summed to province 1; row range 5-7",
        ),
        (
            "households_water_pipe",
            "LK",
            101.0,
            f"{f}, 4 GN rows summed to country LK; row range 5-8",
        ),
    ]


def _trace_all(raw: Path, obs: pd.DataFrame) -> list[tuple[float | None, str]]:
    obs = obs.assign(file="HH_GND_excel.xlsx")
    books = at.Workbooks(raw)
    columns = at.Columns.learn(obs)
    return [at.trace(r, books, columns, {11: 1, 21: 2}) for _, r in obs.iterrows()]


def test_trace_reads_cells_shares_and_gn_sums(tmp_path: Path):
    raw, sha = _workbook(tmp_path)
    traced = _trace_all(raw, _obs(sha, _rows(sha)))
    assert [t[0] for t in traced] == [40.0, 40.0, 90.0, 30.0, 100.0, 101.0]
    assert traced[2][1].startswith("sum of 2 raw GN rows (ds 1103), column K")


def test_trace_rejects_a_wrong_row_count(tmp_path: Path):
    raw, sha = _workbook(tmp_path)
    rows = _rows(sha)
    ind, geo, value, loc = rows[2]
    rows[2] = (ind, geo, value, loc.replace("2 GN rows", "3 GN rows"))
    expected, how = _trace_all(raw, _obs(sha, rows))[2]
    assert expected is None and "locator says 3" in how


def _release(tmp_path: Path, sha: str, rows, place_values, distribution="api") -> Path:
    rel = tmp_path / "release"
    (rel / "observations").mkdir(parents=True)
    _obs(sha, rows).to_parquet(rel / "observations" / f"{at.DATASET}.parquet")
    api = rel / "api" / "v1"
    (api / "places").mkdir(parents=True)
    index = {
        "indicators": [
            {"id": "households_water_pipe", "distribution": distribution},
            {"id": "households_water_pipe_share", "distribution": "api"},
        ]
    }
    (api / "indicators.json").write_text(json.dumps(index))
    for geo in {g for _, g, _, _ in rows}:
        values = [
            {"indicator_id": i, "value": v}
            for i, g, v, _ in rows
            if g == geo and (i, g) in place_values
        ]
        (api / "places" / f"{geo}.json").write_text(json.dumps({"values": values}))
    return rel


def test_run_passes_a_correct_release_and_catches_a_wrong_value(tmp_path: Path):
    raw, sha = _workbook(tmp_path)
    rows = _rows(sha)
    everything = {(i, g) for i, g, _, _ in rows}
    good = at.run(_release(tmp_path, sha, rows, everything), raw)
    assert good is not None
    assert bool((good.sample["source_match"] & good.sample["api_match"]).all())
    assert good.warnings == []

    bad_rows = _rows(sha, pipe_ds_1103=91.0)
    (tmp_path / "release").rename(tmp_path / "old")
    bad = at.run(_release(tmp_path, sha, bad_rows, everything), raw)
    assert bad is not None
    failed = bad.sample[~bad.sample["source_match"]]
    assert list(failed["geography_id"]) == ["LK1103"] and failed["traced"].tolist() == [90.0]


def test_run_checks_downloads_only_is_absent_from_place_files(tmp_path: Path):
    raw, sha = _workbook(tmp_path)
    rows = _rows(sha)
    everything = {(i, g) for i, g, _, _ in rows}
    res = at.run(_release(tmp_path, sha, rows, everything, distribution="downloads_only"), raw)
    assert res is not None
    counts = res.sample[res.sample["indicator_id"] == "households_water_pipe"]
    assert not bool(counts["api_match"].any())  # present in place files, but should not be


def test_lead_rows_offer_a_passing_nonzero_cell_per_step(tmp_path: Path):
    raw, sha = _workbook(tmp_path)
    rows = _rows(sha)
    res = at.run(_release(tmp_path, sha, rows, {(i, g) for i, g, _, _ in rows}), raw)
    assert res is not None
    sheet = at.lead_rows(res, first_check=21)
    assert sheet["check"].tolist() == [21]  # only step (a) exists in this release
    assert sheet["where_to_look"].tolist() == ["HH_GND_excel.xlsx, sheet 'Households', cell K5"]
    assert sheet["published_value"].tolist() == [40.0]
