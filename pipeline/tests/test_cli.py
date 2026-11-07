from typer.testing import CliRunner

from slf.cli import app

runner = CliRunner()


def test_build_example(tmp_path, monkeypatch):
    monkeypatch.setenv("SLF_DATA_DIR", str(tmp_path / "data"))
    result = runner.invoke(app, ["build", "example", "--out-dir", str(tmp_path / "build")])
    assert result.exit_code == 0, result.output
    assert "6 observations, 0 errors, 1 warnings" in result.output


def test_unknown_dataset_fails_clearly(tmp_path, monkeypatch):
    monkeypatch.setenv("SLF_DATA_DIR", str(tmp_path / "data"))
    result = runner.invoke(app, ["snapshot", "nope"])
    assert result.exit_code == 2


def test_release_is_a_clear_stub():
    result = runner.invoke(app, ["release"])
    assert result.exit_code == 2


def test_catalog_validate(tmp_path):
    for name in ("sources", "datasets", "indicators", "geographies", "spaces"):
        (tmp_path / name).mkdir()
    (tmp_path / "sources" / "bad.yaml").write_text("a: [unclosed")
    result = runner.invoke(app, ["catalog", "validate", "--root", str(tmp_path)])
    assert result.exit_code == 1
