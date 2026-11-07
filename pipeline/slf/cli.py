"""Command-line interface: `slf --help`."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from slf.catalog import export_json_schemas, validate_catalog
from slf.datasets import REGISTRY
from slf.storage import from_env

app = typer.Typer(help="Sri Lanka Facts data pipeline.", no_args_is_help=True)
catalog_app = typer.Typer(help="Catalogue commands.", no_args_is_help=True)
app.add_typer(catalog_app, name="catalog")

DEFAULT_BUILD_DIR = "./data/build"


def _dataset(dataset_id: str):
    if dataset_id not in REGISTRY:
        known = ", ".join(sorted(REGISTRY)) or "(none)"
        typer.echo(f"unknown dataset {dataset_id!r}; known: {known}", err=True)
        raise typer.Exit(code=2)
    return REGISTRY[dataset_id]()


def _ids(dataset_id: str | None) -> list[str]:
    return [dataset_id] if dataset_id else sorted(REGISTRY)


@app.command()
def snapshot(dataset_id: str) -> None:
    """Fetch a dataset's source and store it immutably under raw/."""
    ref = _dataset(dataset_id).snapshot(from_env())
    state = "reused existing" if ref.reused else "stored new"
    typer.echo(f"{state} snapshot {ref.key} sha256={ref.sha256}")


@app.command()
def build(
    dataset_id: Annotated[str | None, typer.Argument()] = None,
    out_dir: Annotated[str, typer.Option(help="Local build folder.")] = DEFAULT_BUILD_DIR,
) -> None:
    """Run snapshot → extract → harmonise → validate → publish (to a local build folder)."""
    storage = from_env()
    failed = False
    for ds_id in _ids(dataset_id):
        ds = _dataset(ds_id)
        ref = ds.snapshot(storage)
        observations = ds.harmonise(ds.extract(storage, ref), ref)
        report = ds.validate(observations)
        typer.echo(
            f"{ds_id}: {report.checked} observations, "
            f"{len(report.errors)} errors, {len(report.warnings)} warnings"
        )
        if not report.ok:
            failed = True
            typer.echo(report.to_markdown(), err=True)
            continue
        for path in ds.publish(observations, report, out_dir):
            typer.echo(f"  wrote {path}")
    if failed:
        raise typer.Exit(code=1)


@app.command()
def validate(dataset_id: Annotated[str | None, typer.Argument()] = None) -> None:
    """Validate datasets without publishing."""
    storage = from_env()
    failed = False
    for ds_id in _ids(dataset_id):
        ds = _dataset(ds_id)
        ref = ds.snapshot(storage)
        report = ds.validate(ds.harmonise(ds.extract(storage, ref), ref))
        typer.echo(report.to_markdown())
        failed = failed or not report.ok
    if failed:
        raise typer.Exit(code=1)


@app.command()
def release() -> None:
    """Build a versioned release (not implemented yet; arrives with prompt D04)."""
    typer.echo("slf release is not implemented yet (prompt D04).", err=True)
    raise typer.Exit(code=2)


@catalog_app.command("validate")
def catalog_validate(
    root: Annotated[Path, typer.Option(help="Path to the catalog folder.")] = Path("../catalog"),
    overrides: Annotated[
        Path | None, typer.Option(help="Path to the overrides folder (default: next to catalog).")
    ] = None,
) -> None:
    """Check every catalogue file against the schemas and the links between them."""
    report = validate_catalog(
        root, overrides if overrides is not None else root.parent / "overrides"
    )
    for e in report.errors:
        typer.echo(f"ERROR {e}", err=True)
    counts = ", ".join(f"{v} {k}" for k, v in report.counts.items())
    if counts:
        typer.echo(f"checked: {counts}")
    if report.not_publishable:
        typer.echo(f"not publishable: {len(report.not_publishable)} findings")
        for n in report.not_publishable:
            typer.echo(f"  - {n}")
    if not report.ok:
        typer.echo(f"catalogue FAILED: {len(report.errors)} errors", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"catalogue OK ({root})")


@catalog_app.command("schemas")
def catalog_schemas(
    out_dir: Annotated[Path, typer.Option(help="Where to write JSON Schema files.")] = Path(
        "../catalog/schemas"
    ),
) -> None:
    """Export the catalogue schemas as JSON Schema files (for editors and reviewers)."""
    for path in export_json_schemas(out_dir):
        typer.echo(f"wrote {path}")
