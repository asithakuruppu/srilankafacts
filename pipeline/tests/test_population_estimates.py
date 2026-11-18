"""National 1891-1946 estimates: row ids, the repeated year and the census cross-check."""

import json

import pandas as pd

from slf import population_estimates as pe


def _setup(tmp_path):
    folder = tmp_path / "raw" / pe.SOURCE / pe.DATASET / "20261118T000000Z"
    folder.mkdir(parents=True)
    data = folder / pe.FILENAME
    data.write_text(
        "Country\tYear\tEstimatedPopulationAllDistrictsIncluding1946Data\t"
        "EstimatedPopulationNonplantationDistrictsIncluding1946Data\tSource\n"
        '"Sri Lanka"\t1917\t1000\t800\t"x"\n'
        '"Sri Lanka"\t1918\t1100\t880\t"x"\n'
        '"Sri Lanka"\t1918\t1000\t800\t"x"\n'
        '"Sri Lanka"\t1919\t1010\t808\t"x"\n'
    )
    data.with_name(data.name + ".meta.json").write_text(json.dumps({"sha256": "ab", "url": "u"}))
    catalog = tmp_path / "catalog"
    (catalog / "references").mkdir(parents=True)
    pd.DataFrame({"district": ["Sri Lanka"], "1917": ["1.0"], "1919": [".."]}).to_csv(
        catalog / "references/dcs-abstract2024-table2.1-transcription.csv", index=False
    )
    return tmp_path / "raw", catalog


def test_repeated_year_keeps_both_rows_with_distinct_ids(tmp_path):
    raw, catalog = _setup(tmp_path)
    result = pe.build(raw, catalog, tmp_path / "out")
    frame = pd.read_parquet(tmp_path / "out" / "observations.parquet")
    assert result["rows"] == 8 and not frame.claim_id.duplicated().any()
    twice = frame[(frame.period == "1918") & (frame.indicator_id.str.endswith("all_districts"))]
    assert sorted(twice.value) == [1000.0, 1100.0]
    assert twice.source_locator.str.contains("appears twice").all()
    assert (frame.geography_id == "LK").all() and (frame.data_nature == "reconstruction").all()


def test_crosscheck_skips_missing_census_years_and_repeats(tmp_path):
    raw, catalog = _setup(tmp_path)
    pe.build(raw, catalog, tmp_path / "out")
    check = pd.read_csv(tmp_path / "out" / "crosscheck_dcs_table_2_1.csv")
    assert check.year.tolist() == [1917] and check.difference_percent.tolist() == [0.0]
