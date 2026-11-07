import pytest

from slf.storage import ImmutableKeyError, LocalStorage


def test_put_get_and_list(tmp_path):
    s = LocalStorage(tmp_path)
    s.put("raw/src/ds/a.txt", b"hello")
    assert s.exists("raw/src/ds/a.txt")
    assert s.get("raw/src/ds/a.txt") == b"hello"
    assert s.list("raw/src") == ["raw/src/ds/a.txt"]


def test_refuses_overwrite(tmp_path):
    s = LocalStorage(tmp_path)
    s.put("raw/src/ds/a.txt", b"first")
    with pytest.raises(ImmutableKeyError):
        s.put("raw/src/ds/a.txt", b"second")
    assert s.get("raw/src/ds/a.txt") == b"first"


@pytest.mark.parametrize("key", ["", "/", "raw/../etc/passwd"])
def test_rejects_bad_keys(tmp_path, key):
    with pytest.raises(ValueError):
        LocalStorage(tmp_path).put(key, b"x")
