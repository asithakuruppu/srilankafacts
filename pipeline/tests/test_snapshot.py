import hashlib
import json
from datetime import UTC, datetime

from slf.snapshot import snapshot_bytes
from slf.storage import LocalStorage


def test_snapshot_writes_content_and_meta(tmp_path):
    s = LocalStorage(tmp_path)
    ref = snapshot_bytes(
        s,
        source="src",
        dataset="ds",
        filename="f.csv",
        content=b"a,b\n1,2\n",
        url="https://example.org/f.csv",
        now=datetime(2026, 11, 7, 12, 0, tzinfo=UTC),
    )
    assert ref.key == "raw/src/ds/20261107T120000Z/f.csv"
    assert ref.sha256 == hashlib.sha256(b"a,b\n1,2\n").hexdigest()
    meta = json.loads(s.get(ref.key + ".meta.json"))
    assert meta["url"] == "https://example.org/f.csv"
    assert meta["sha256"] == ref.sha256
    assert not ref.reused


def test_identical_content_is_not_stored_twice(tmp_path):
    s = LocalStorage(tmp_path)
    first = snapshot_bytes(s, source="src", dataset="ds", filename="f", content=b"same")
    second = snapshot_bytes(s, source="src", dataset="ds", filename="f", content=b"same")
    assert second.reused and second.key == first.key
    assert len(s.list("raw/src/ds")) == 2  # one file + one .meta.json
