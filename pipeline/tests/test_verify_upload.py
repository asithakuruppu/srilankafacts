import hashlib
import json

from slf.verify_upload import verify_upload


class _Body:
    def __init__(self, data):
        self.data = data

    def read(self, n):
        out, self.data = self.data[:n], self.data[n:]
        return out


class FakeClient:
    def __init__(self, objects):
        self.objects = objects  # key -> bytes
        self.etags = {}

    def get_paginator(self, name):
        outer = self

        class P:
            def paginate(self, Bucket, Prefix):
                yield {
                    "Contents": [
                        {
                            "Key": k,
                            "Size": len(v),
                            "ETag": f'"{outer.etags.get(k, hashlib.md5(v).hexdigest())}"',
                        }
                        for k, v in outer.objects.items()
                        if k.startswith(Prefix)
                    ]
                }

        return P()

    def get_object(self, Bucket, Key):
        return {"Body": _Body(self.objects[Key])}


def _release(tmp_path):
    (tmp_path / "api/v1/releases").mkdir(parents=True)
    (tmp_path / "datapackage.json").write_text(
        json.dumps({"publishable": True, "access": "public"})
    )
    (tmp_path / "api/v1/releases/latest.json").write_text(json.dumps({"release": "v1"}))
    (tmp_path / "a.csv").write_text("hello")
    lines = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(tmp_path).as_posix()}"
        for p in tmp_path.rglob("*")
        if p.is_file()
    ]
    (tmp_path / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n")
    return tmp_path


def _mirror(root):
    return {
        f"releases/v1/{p.relative_to(root).as_posix()}": p.read_bytes()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_matching_bucket_ok(tmp_path):
    root = _release(tmp_path)
    res = verify_upload(root, FakeClient(_mirror(root)), "b")
    assert res.ok and res.hash_checked > 0 and res.etag_checked == res.local_files


def test_missing_extra_size_etag_and_hash(tmp_path):
    root = _release(tmp_path)
    objs = _mirror(root)
    del objs["releases/v1/datapackage.json"]
    objs["releases/v1/zzz.txt"] = b"x"
    objs["releases/v1/a.csv"] = b"hellO"  # same size, different content
    c = FakeClient(objs)
    c.etags["releases/v1/CHECKSUMS.sha256"] = "0" * 32
    res = verify_upload(root, c, "b")
    assert res.missing == ["datapackage.json"]
    assert res.extra == ["zzz.txt"]
    assert res.etag_mismatch == ["CHECKSUMS.sha256", "a.csv"]
    assert res.hash_mismatch == ["a.csv"]
    assert not res.ok


def test_size_mismatch_and_multipart_fallback(tmp_path):
    root = _release(tmp_path)
    objs = _mirror(root)
    objs["releases/v1/a.csv"] = b"hi"
    c = FakeClient(objs)
    c.etags["releases/v1/datapackage.json"] = "abc-3"
    res = verify_upload(root, c, "b")
    assert res.size_mismatch == ["a.csv"]
    assert res.multipart_size_only == 1 and res.etag_mismatch == []
