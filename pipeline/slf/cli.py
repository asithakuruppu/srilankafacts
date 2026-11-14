"""Command-line interface: `slf --help`."""

from __future__ import annotations

import os
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
def release(
    version: Annotated[str, typer.Option(help="Release version, for example v2026.11.1.")],
    dataset_ids: Annotated[
        list[str] | None,
        typer.Option("--dataset", help="Dataset id to include; repeat for several. Default: all."),
    ] = None,
    notes: Annotated[str, typer.Option(help="Release notes (short text).")] = "",
    preview: Annotated[
        bool,
        typer.Option(
            help="Build a private preview even when rights are unclear. Never publishable."
        ),
    ] = False,
    previous: Annotated[
        Path | None, typer.Option(help="Previous observations.parquet for a diff changelog.")
    ] = None,
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    out_dir: Annotated[Path, typer.Option(help="Release output folder.")] = Path(
        "./data/build/releases"
    ),
    profile_dir: Annotated[
        Path | None,
        typer.Option(help="Profile build folder (`slf profile build`) to package under D-031."),
    ] = None,
    corrections_log: Annotated[
        Path | None, typer.Option(help="Corrections log to publish as api/v1/corrections.json.")
    ] = Path("../docs/corrections/log.yaml"),
) -> None:
    """Build a versioned, immutable release from validated datasets."""
    from slf.release import build_release

    data_dir = Path(os.environ.get("SLF_DATA_DIR", "data"))
    result = build_release(
        version=version,
        dataset_ids=dataset_ids or sorted(REGISTRY),
        catalog_root=catalog,
        data_dir=data_dir,
        spine_dir=spine_dir,
        out_dir=out_dir,
        notes=notes,
        preview=preview,
        previous=previous,
        profile_dir=profile_dir,
        corrections_path=corrections_log,
    )
    for warning in result.warnings:
        typer.echo(f"WARNING {warning}", err=True)
    for error in result.errors:
        typer.echo(f"ERROR {error}", err=True)
    if result.errors:
        raise typer.Exit(code=1)
    state = "private preview (not publishable)" if result.preview else "public release"
    typer.echo(f"{state}: {result.path} ({len(result.files)} files)")
    for rel in result.files:
        if rel.endswith(("CHECKSUMS.sha256", "datapackage.json", "CHANGELOG.md")):
            typer.echo(f"  {rel}")


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


spine_app = typer.Typer(help="Geography spine commands (G01).", no_args_is_help=True)
app.add_typer(spine_app, name="spine")


@spine_app.command("build")
def spine_build(
    out_dir: Annotated[Path, typer.Option(help="Where to write the build.")] = Path(
        "./data/build/geography-spine"
    ),
    refresh: Annotated[bool, typer.Option(help="Download a fresh snapshot.")] = False,
    relations_csv: Annotated[
        Path | None, typer.Option(help="Also write parent edges to this catalogue CSV.")
    ] = None,
    catalog: Annotated[Path, typer.Option(help="Catalogue folder (provisional units).")] = Path(
        "../catalog"
    ),
) -> None:
    """Build the admin geography spine (levels 0-4) from COD-AB, with a QA report."""
    from slf.datasets import cod_ab_admin

    storage = from_env()
    root = Path(os.environ.get("SLF_DATA_DIR", "data"))
    result = cod_ab_admin.build_spine(storage, root, out_dir, refresh=refresh, catalog_root=catalog)
    for p in result.outputs:
        typer.echo(f"wrote {p}")
    if relations_csv is not None:
        import pandas as pd

        rel = pd.read_parquet(out_dir / "geography_relations.parquet")
        rel = rel[
            rel["method"] == "attribute"
        ]  # COD-AB edges only; provisional edges live in the catalogue
        relations_csv.parent.mkdir(parents=True, exist_ok=True)
        relations_csv.write_text(cod_ab_admin.relations_csv(pd.DataFrame(rel)), encoding="utf-8")
        typer.echo(f"wrote {relations_csv} ({len(rel)} parent edges)")
    for e in result.errors:
        typer.echo(f"ERROR {e}", err=True)
    if result.errors:
        raise typer.Exit(code=1)
    typer.echo("spine OK")


crosswalk_app = typer.Typer(help="Code crosswalk commands (G02).", no_args_is_help=True)
app.add_typer(crosswalk_app, name="crosswalk")


@crosswalk_app.command("snapshot-nsdi")
def crosswalk_snapshot_nsdi() -> None:
    """Fetch NSDI GN and DS attributes (paged, polite) into raw storage."""
    from slf.datasets import crosswalk_admin

    ref = crosswalk_admin.snapshot_nsdi_attributes(from_env())
    typer.echo(f"snapshot {ref.key} sha256={ref.sha256}")


@crosswalk_app.command("build")
def crosswalk_build(
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    report: Annotated[Path, typer.Option(help="Report path.")] = Path(
        "../docs/research/geography/crosswalk-report.md"
    ),
) -> None:
    """Match DCS, NSDI, Lanka Data Layer and nuuuwan codes to spine p-codes."""
    import pandas as pd

    from slf.datasets import crosswalk_admin

    spine = pd.read_parquet(spine_dir / "geographies.parquet")
    mm_path = catalog / "geographies" / "manual-matches.csv"
    manual = pd.read_csv(mm_path, dtype=str) if mm_path.exists() else None
    b = crosswalk_admin.build(from_env(), spine, manual)
    for p in crosswalk_admin.write_outputs(b.results, catalog):
        typer.echo(f"wrote {p}")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(crosswalk_admin.render_report(b, spine), encoding="utf-8")
    typer.echo(f"wrote {report}")


geom_app = typer.Typer(help="Geometry QA commands (G03).", no_args_is_help=True)
app.add_typer(geom_app, name="geometry-qa")


@geom_app.command("snapshot-nsdi")
def geometry_snapshot_nsdi() -> None:
    """Fetch NSDI district and DS polygons (paged, polite) into raw storage."""
    from slf.datasets import geometry_qa

    ref = geometry_qa.snapshot_nsdi_geometry(from_env())
    typer.echo(f"snapshot {ref.key} sha256={ref.sha256} ({ref.size_bytes:,} bytes)")


@geom_app.command("build")
def geometry_build(
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path(
        "./data/build/geometry-qa"
    ),
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    report_dir: Annotated[Path, typer.Option(help="Report folder.")] = Path(
        "../docs/research/geography"
    ),
) -> None:
    """Run geometry QA on the canonical spine and compare with NSDI shapes."""
    import geopandas as gpd
    import pandas as pd

    from slf.datasets import crosswalk_admin, geometry_qa

    storage = from_env()
    versions = gpd.read_parquet(spine_dir / "geography_versions.geoparquet")
    if "status" in versions.columns:  # provisional units overlap COD-AB units by design
        versions = gpd.GeoDataFrame(versions[versions["status"] == "current"], crs=versions.crs)
    geos = pd.read_parquet(spine_dir / "geographies.parquet")
    nsdi_codes = pd.read_csv(catalog / "geographies" / "codes" / "nsdi.csv", dtype=str)
    try:
        ref = crosswalk_admin.latest(
            storage, "raw/nsdi/nsdi-admin-boundaries/", "nsdi_district_ds_geometry.json"
        )
        nsdi = geometry_qa.load_nsdi_geometry(storage, ref)
    except FileNotFoundError:
        ref, nsdi = None, None
        typer.echo("NSDI geometry snapshot not found; skipping the NSDI comparison", err=True)
    attrs = crosswalk_admin.parse_nsdi(
        storage,
        crosswalk_admin.latest(
            storage, "raw/nsdi/nsdi-admin-boundaries/", "nsdi_gn_ds_attributes.json"
        ),
    )
    gn_map = dict(zip(nsdi_codes["external_code"], nsdi_codes["geography_id"], strict=False))
    flagged = attrs[(attrs["level"] == 4) & attrs["extra"].notna()]
    disputes = pd.DataFrame(
        {
            "geography_id": [gn_map.get(c) for c in flagged["code"]],
            "nsdi_code": flagged["code"],
            "dispute": flagged["extra"],
        }
    )
    disputes = disputes.dropna(subset=["geography_id"]).drop_duplicates("geography_id")
    qa = geometry_qa.run(versions, geos, nsdi, nsdi_codes, ref, disputes)
    out_dir.mkdir(parents=True, exist_ok=True)
    gpkg = out_dir / "geometry_qa_cod-ab-v03.gpkg"
    geometry_qa.write_gpkg(qa, versions, nsdi, gpkg)
    img = geometry_qa.thumbnails(qa, versions, report_dir / "img")
    names = dict(zip(geos["geography_id"], geos["name_en"], strict=False))
    report = report_dir / "geometry-qa-cod-ab-v03.md"
    report.write_text(geometry_qa.render(qa, names, img), encoding="utf-8")
    typer.echo(f"wrote {gpkg}\nwrote {report}")


profile_app = typer.Typer(help="Profile vector space commands (A03).", no_args_is_help=True)
app.add_typer(profile_app, name="profile")


@profile_app.command("build")
def profile_build(
    observations: Annotated[Path, typer.Option(help="Census observations parquet.")] = Path(
        "./data/build/census-2024-gnd-tables/observations.parquet"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/profile"),
) -> None:
    """Build profile vectors, similar places, unusualness, contrasts and sensitivity."""
    import pandas as pd

    from slf import profile

    geos = pd.read_parquet(spine_dir / "geographies.parquet")
    result = profile.build_profile(pd.read_parquet(observations), geos, spine_dir, catalog, out_dir)
    qa = out_dir / "qa.md"
    qa.write_text(profile.render_qa(result, geos), encoding="utf-8")
    for level, r in result.levels.items():
        typer.echo(
            f"{level}: {len(r.fit.ids):,} places, {len(r.excluded)} excluded, "
            f"{len(r.fit.retained)} axes, decomposition error {r.check_max_error:.1e}"
        )
    for w in result.warnings:
        typer.echo(f"warning: {w}", err=True)
    typer.echo(f"QA report: {qa}")
    if result.warnings:
        raise typer.Exit(1)


audit_app = typer.Typer(help="Quality audits (Q01).", no_args_is_help=True)
app.add_typer(audit_app, name="audit")


@audit_app.command("q01")
def audit_q01(
    release_dir: Annotated[Path, typer.Option(help="Release folder to audit.")] = Path(
        "./data/build/releases-preview/v2026.11.7-preview.1"
    ),
    raw_dir: Annotated[Path, typer.Option(help="Raw snapshots folder.")] = Path("./data/raw"),
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    pdf_pages: Annotated[
        Path, typer.Option(help="Page text/PNG from scripts/pdf_pages.swift (pages 68, 202).")
    ] = Path("./data/build/audit/pdf-pages"),
    out_dir: Annotated[Path, typer.Option(help="Report folder.")] = Path("../docs/qa"),
    seed: Annotated[int, typer.Option(help="Random seed for the sample.")] = 20261112,
) -> None:
    """Draw the Q01 sample, re-trace each value to its raw source and write the lead's sheet."""
    import shutil

    import pandas as pd

    from slf import audit, audit_topics

    res = audit.run(release_dir, raw_dir, catalog, pdf_pages, seed)
    sheet = audit.lead_sheet(res, seed)
    topics = audit_topics.run(release_dir, raw_dir, seed)
    if topics is not None:
        extra = audit_topics.lead_rows(topics, first_check=len(sheet) + 1, seed=seed)
        sheet = pd.concat([sheet, extra], ignore_index=True)
        res.warnings.extend(topics.warnings)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"accuracy-audit-{res.release}"
    res.sample.to_csv(out_dir / f"{stem}-sample.csv", index=False)
    sheet.to_csv(out_dir / f"q01-lead-sheet-{res.release}.csv", index=False)
    report = audit.render(res, sheet)
    if topics is not None:
        topics.sample.to_csv(out_dir / f"{stem}-topics-sample.csv", index=False)
        report += audit_topics.render(topics)
    (out_dir / f"{stem}.md").write_text(report, encoding="utf-8")
    shots = out_dir / "screenshots" / "q01"
    shots.mkdir(parents=True, exist_ok=True)
    for png in sorted(pdf_pages.glob("page-*.png")):
        shutil.copy(png, shots / png.name)
    bad = audit.count_true(~(res.sample["source_match"] & res.sample["api_match"]))
    typer.echo(
        f"{len(res.sample)} values sampled (seed {seed}); {bad} failed re-trace or API check"
    )
    if res.pdf is not None:
        typer.echo(f"Final Report: {audit.count_true(res.pdf['match'])}/{len(res.pdf)} match")
    if topics is not None:
        t = topics.sample
        bad_t = audit.count_true(~(t["source_match"] & t["api_match"]))
        typer.echo(f"Topic tables: {len(t)} values sampled; {bad_t} failed re-trace or API check")
    for w in res.warnings:
        typer.echo(f"warning: {w}", err=True)
    typer.echo(f"report: {out_dir / (stem + '.md')}")
    if res.warnings:
        raise typer.Exit(1)


@audit_app.command("crosschecks")
def audit_crosschecks(
    release_dir: Annotated[Path, typer.Option(help="Release folder to check.")],
    pdf_pages: Annotated[
        Path,
        typer.Option(help="Final Report page text from scripts/pdf_pages.swift."),
    ] = Path("./data/build/audit/pdf-pages"),
    out_dir: Annotated[Path, typer.Option(help="Report folder.")] = Path("../docs/qa"),
) -> None:
    """Compare a release with DCS's own DS tables and its Final Report (independent checks)."""
    import json

    from slf import crosschecks
    from slf.crosschecks.final_report import PAGES

    missing = [n for n in PAGES if not (pdf_pages / f"page-{n:03d}.txt").exists()]
    if missing:
        typer.echo(
            "Final Report page text missing; run first:\n  swift scripts/pdf_pages.swift "
            f"<CPH2024_Final_Eng.pdf> {pdf_pages} {' '.join(str(n) for n in PAGES)}",
            err=True,
        )
        raise typer.Exit(2)
    latest = json.loads((release_dir / "api/v1/releases/latest.json").read_text("utf-8"))
    results = crosschecks.run_all(release_dir, pdf_pages)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / f"crosschecks-{latest['release']}.md"
    report.write_text(crosschecks.render(results, latest["release"]), encoding="utf-8")
    for r in results:
        typer.echo(f"{r.check}: {r.compared} compared, {len(r.differences)} differ")
    new, gone = crosschecks.unexplained(results)
    for message in new:
        typer.echo(f"new difference: {message}", err=True)
    for key in gone:
        typer.echo(f"known difference no longer seen: {key}", err=True)
    typer.echo(f"report: {report}")
    if new or gone:
        raise typer.Exit(1)


@profile_app.command("smoothing-experiment")
def profile_smoothing_experiment(
    observations: Annotated[Path, typer.Option(help="Census observations parquet.")] = Path(
        "./data/build/census-2024-gnd-tables/observations.parquet"
    ),
    out: Annotated[Path, typer.Option(help="Results JSON.")] = Path(
        "../docs/research/profile/gn-smoothing-experiment.json"
    ),
) -> None:
    """D-031 option (c): do smoothed values make GN similar-place lists stable? (research only)"""
    import json

    import pandas as pd

    from slf import profile_smoothing

    results = profile_smoothing.run(pd.read_parquet(observations))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    typer.echo(profile_smoothing.render(results))
    typer.echo(f"wrote {out}")
