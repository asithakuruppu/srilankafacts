import json

import pytest

from slf.upload import NotPublishableError, upload_release


class FakeClient:
    def __init__(self):
        self.calls = []

    def upload_file(self, path, bucket, key, ExtraArgs=None):
        self.calls.append((bucket, key, (ExtraArgs or {})["ContentType"]))


def _release(tmp_path, publishable=True, access="public"):
    (tmp_path / "api/v1/releases").mkdir(parents=True)
    (tmp_path / "datapackage.json").write_text(
        json.dumps({"publishable": publishable, "access": access})
    )
    (tmp_path / "api/v1/releases/latest.json").write_text(json.dumps({"release": "v1"}))
    (tmp_path / "a.csv").write_text("x")
    return tmp_path


def test_uploads_with_prefix_and_type(tmp_path):
    c = FakeClient()
    res = upload_release(_release(tmp_path), c, "b", exists=lambda k: False)
    assert ("b", "releases/v1/a.csv", "text/csv") in c.calls
    assert len(res.uploaded) == 3


def test_never_overwrites(tmp_path):
    c = FakeClient()
    res = upload_release(_release(tmp_path), c, "b", exists=lambda k: k.endswith("a.csv"))
    assert res.skipped_existing == ["releases/v1/a.csv"]
    assert all(not k.endswith("a.csv") for _, k, _ in c.calls)


def test_dry_run_sends_nothing(tmp_path):
    c = FakeClient()
    res = upload_release(_release(tmp_path), c, "b", dry_run=True, exists=lambda k: False)
    assert c.calls == [] and res.uploaded


@pytest.mark.parametrize("kw", [{"publishable": False}, {"access": "private_preview"}])
def test_refuses_private(tmp_path, kw):
    with pytest.raises(NotPublishableError):
        upload_release(_release(tmp_path, **kw), FakeClient(), "b")


class ListingClient(FakeClient):
    class _Pager:
        def paginate(self, Bucket, Prefix):
            yield {"Contents": [{"Key": "releases/v1/a.csv"}]}

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return self._Pager()


def test_uses_one_listing_not_per_file_checks(tmp_path):
    c = ListingClient()
    res = upload_release(_release(tmp_path), c, "b")
    assert res.skipped_existing == ["releases/v1/a.csv"]
    assert len(c.calls) == 2
