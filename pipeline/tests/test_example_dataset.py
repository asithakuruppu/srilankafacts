import json

import pytest

from slf.dataset import check_observations
from slf.datasets.example_dataset import ExampleDataset
from slf.storage import LocalStorage


def run(tmp_path):
    ds = ExampleDataset()
    storage = LocalStorage(tmp_path / "data")
    ref = ds.snapshot(storage)
    obs = ds.harmonise(ds.extract(storage, ref), ref)
    return ds, obs, ds.validate(obs)


def test_five_stages_end_to_end(tmp_path):
    ds, obs, report = run(tmp_path)
    assert len(obs) == 6  # 3 units x 2 indicators
    assert report.ok, report.errors
    paths = ds.publish(obs, report, str(tmp_path / "build"))
    published = json.loads((tmp_path / "build" / "example" / "observations.json").read_text())
    assert len(published) == 6 and len(paths) == 2


def test_missing_value_is_kept_and_reported(tmp_path):
    _, obs, report = run(tmp_path)
    missing = [o for o in obs if o["value_status"] == "not_available"]
    assert len(missing) == 1 and missing[0]["value"] is None
    assert any("not available" in w for w in report.warnings)


def test_every_observation_has_where_when_what(tmp_path):
    _, obs, _ = run(tmp_path)
    for o in obs:
        assert o["footprint_ref"] and o["support_type"] == "area_total"
        assert o["time_start"] and o["time_support"] == "snapshot"
        assert o["indicator_id"] and o["snapshot_sha256"] and o["source_locator"]


def test_two_preferred_claims_for_same_box_fail():
    base = {
        "indicator_id": "x",
        "footprint_ref": "TEST-001",
        "geography_vintage": "test",
        "support_type": "area_total",
        "period": "2024",
        "time_start": "2024-01-01",
        "time_end": "2024-01-01",
        "time_support": "snapshot",
        "value": 1,
        "value_status": "normal",
        "data_nature": "census_count",
        "verification": "machine_extracted",
        "dataset_id": "t",
        "snapshot_sha256": "abc",
        "source_locator": "here",
        "preferred": True,
        "preferred_reason": "official",
    }
    rows = [{**base, "claim_id": "a"}, {**base, "claim_id": "b"}]
    report = check_observations("t", rows)
    assert any("preferred claims" in e for e in report.errors)


def test_publish_refuses_failed_report(tmp_path):
    ds, obs, report = run(tmp_path)
    report.errors.append("forced failure")
    with pytest.raises(RuntimeError):
        ds.publish(obs, report, str(tmp_path / "build"))
