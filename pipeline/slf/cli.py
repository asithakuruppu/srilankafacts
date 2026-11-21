"""Command-line interface: `slf --help`."""

from __future__ import annotations

import json
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


@app.command("upload")
def upload(
    release_dir: Annotated[Path, typer.Option(help="Built public release folder.")],
    prefix: Annotated[
        str | None, typer.Option(help="Key prefix; default releases/<version>.")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option(help="List what would be uploaded; send nothing.")
    ] = False,
    workers: Annotated[int, typer.Option(help="Files sent in parallel (1-64).")] = 1,
) -> None:
    """Upload a publishable release to the S3/R2 bucket named by SLF_S3_BUCKET."""
    from slf.upload import NotPublishableError, upload_release

    bucket = os.environ.get("SLF_S3_BUCKET")
    if not bucket:
        typer.echo("SLF_S3_BUCKET must be set", err=True)
        raise typer.Exit(code=2)
    try:
        import boto3  # type: ignore[import-not-found]
    except ImportError:
        typer.echo("needs the optional extra: uv sync --extra s3", err=True)
        raise typer.Exit(code=2) from None
    from botocore.config import Config  # type: ignore[import-not-found]

    client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("SLF_S3_ENDPOINT"),
        region_name="auto",
        config=Config(
            retries={"max_attempts": 10, "mode": "adaptive"},
            connect_timeout=20,
            max_pool_connections=max(10, workers),
        ),
    )  # R2 accepts only "auto" (not AWS regions from the machine config)
    try:
        res = upload_release(
            release_dir,
            client,
            bucket,
            prefix,
            dry_run,
            workers=min(max(workers, 1), 64),
            progress=lambda d, t: (
                typer.echo(f"  {d}/{t} files", err=True) if d % 500 == 0 else None
            ),
        )
    except NotPublishableError as exc:
        typer.echo(f"ERROR {exc}", err=True)
        raise typer.Exit(code=1) from None
    verb = "would upload" if dry_run else "uploaded"
    typer.echo(
        f"{verb} {len(res.uploaded)} files ({res.bytes_uploaded / 1e6:.1f} MB); "
        f"{len(res.skipped_existing)} already present and left unchanged"
    )


@app.command("verify-upload")
def verify_upload_cmd(
    release_dir: Annotated[Path, typer.Option(help="Local release folder that was uploaded.")],
    prefix: Annotated[
        str | None, typer.Option(help="Key prefix; default releases/<version>.")
    ] = None,
    sample: Annotated[
        int, typer.Option(help="Files to download and hash against CHECKSUMS.sha256.")
    ] = 20,
) -> None:
    """Check the bucket named by SLF_S3_BUCKET matches a local release (read-only)."""
    from slf.upload import NotPublishableError
    from slf.verify_upload import verify_upload

    bucket = os.environ.get("SLF_S3_BUCKET")
    if not bucket:
        typer.echo("SLF_S3_BUCKET must be set", err=True)
        raise typer.Exit(code=2)
    try:
        import boto3  # type: ignore[import-not-found]
    except ImportError:
        typer.echo("needs the optional extra: uv sync --extra s3", err=True)
        raise typer.Exit(code=2) from None
    from botocore.config import Config  # type: ignore[import-not-found]

    client = boto3.client(
        "s3",
        endpoint_url=os.environ.get("SLF_S3_ENDPOINT"),
        region_name="auto",
        config=Config(retries={"max_attempts": 10, "mode": "adaptive"}, connect_timeout=20),
    )
    try:
        res = verify_upload(release_dir, client, bucket, prefix, sample)
    except NotPublishableError as exc:
        typer.echo(f"ERROR {exc}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"{res.prefix}: {res.local_files} local files, {res.remote_files} in bucket")
    typer.echo(
        f"ETag = MD5 checked: {res.etag_checked}; multipart (size only): "
        f"{res.multipart_size_only}; downloaded and SHA-256 checked: {res.hash_checked}"
    )
    for label, items in [
        ("MISSING", res.missing),
        ("EXTRA", res.extra),
        ("SIZE MISMATCH", res.size_mismatch),
        ("ETAG MISMATCH", res.etag_mismatch),
        ("SHA-256 MISMATCH", res.hash_mismatch),
    ]:
        for item in items[:50]:
            typer.echo(f"{label} {item}", err=True)
        if len(items) > 50:
            typer.echo(f"{label} ... and {len(items) - 50} more", err=True)
    if not res.ok:
        raise typer.Exit(code=1)
    typer.echo("OK: bucket matches the release")


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
    identity_observations: Annotated[
        Path, typer.Option(help="Topic-table observations parquet (ethnic group and religion).")
    ] = Path("./data/build/census-2024-topic-tables/observations.parquet"),
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
    frames = [pd.read_parquet(observations)]
    if identity_observations.exists():
        identity = pd.read_parquet(identity_observations)
        # only the ethnic-group and religion counts: the rest of the topic tables is not an input
        ids = identity["indicator_id"].astype(str)
        frames.append(identity.loc[ids.isin(profile.IDENTITY)])
    result = profile.build_profile(pd.concat(frames), geos, spine_dir, catalog, out_dir)
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


@profile_app.command("spaces")
def profile_spaces(
    observations: Annotated[Path, typer.Option(help="Census observations parquet.")] = Path(
        "./data/build/census-2024-gnd-tables/observations.parquet"
    ),
    identity_observations: Annotated[
        Path, typer.Option(help="Topic-table observations parquet (ethnic group and religion).")
    ] = Path("./data/build/census-2024-topic-tables/observations.parquet"),
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    profile_dir: Annotated[Path, typer.Option(help="Profile build (`slf profile build`).")] = Path(
        "./data/build/profile-v03"
    ),
    history_dir: Annotated[
        Path | None, typer.Option(help="History build (`slf history build`); private, D-038.")
    ] = Path("./data/build/history"),
    release_dir: Annotated[
        Path | None, typer.Option(help="Release whose admin.json names the text space indexes.")
    ] = None,
    runs: Annotated[int, typer.Option(help="Bootstrap runs per k for the typology.")] = 50,
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/spaces"),
) -> None:
    """Build vector spaces v2: typology, trajectory (private), composite and text."""
    import json

    import pandas as pd

    from slf import profile, spaces

    geos = pd.read_parquet(spine_dir / "geographies.parquet")
    frames = [pd.read_parquet(observations)]
    if identity_observations.exists():
        identity = pd.read_parquet(identity_observations)
        frames.append(identity.loc[identity["indicator_id"].astype(str).isin(profile.IDENTITY)])
    if release_dir is not None:
        admin = json.loads((release_dir / "api/v1/geographies/admin.json").read_text())[
            "geographies"
        ]
    else:
        admin = geos.to_dict("records")
    summary = spaces.build_all(
        pd.concat(frames), geos, profile_dir, history_dir, admin, out_dir, runs
    )
    typer.echo(json.dumps(summary, indent=1, default=str))
    if summary["refit_max_difference"] > 1e-6:  # stored profile vectors are float32
        typer.echo("error: rebuilt DS profile differs from the stored profile build", err=True)
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
    raw_dir: Annotated[Path, typer.Option(help="Raw snapshots folder.")] = Path("./data/raw"),
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
    results = crosschecks.run_all(release_dir, pdf_pages, raw_dir)
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


history_app = typer.Typer(
    help="Census history (G06): 2012->2024 DS change, district series.", no_args_is_help=True
)
app.add_typer(history_app, name="history")


@history_app.command("snapshot")
def history_snapshot() -> None:
    """Snapshot the 2012 GN file (nuuuwan mirror), Abstract 2024 Tables 2.1 and 2.7."""
    from slf import history
    from slf.storage import from_env

    for ref in history.snapshot(from_env()):
        typer.echo(f"{'reused' if ref.reused else 'stored'} {ref.key} sha256={ref.sha256[:12]}")


@history_app.command("estimates")
def history_estimates(
    raw_root: Annotated[Path, typer.Option(help="Folder holding raw/ (a data root).")] = Path(
        "./data/raw"
    ),
    catalog: Annotated[Path, typer.Option(help="Catalogue root.")] = Path("../catalog"),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path(
        "./data/build/population-estimates"
    ),
) -> None:
    """National annual population estimates 1891-1946, checked against DCS census totals."""
    from slf import population_estimates

    typer.echo(json_dumps(population_estimates.build(raw_root, catalog, out_dir)))


@history_app.command("build")
def history_build(
    pages: Annotated[
        Path, typer.Option(help="Folder with gn2012/, abstract27/, abstract21/, fr2024/ text.")
    ] = Path("./data/build/history/pdf-pages"),
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    out_dir: Annotated[Path, typer.Option(help="Build folder.")] = Path("./data/build/history"),
    qa_dir: Annotated[Path, typer.Option(help="Reviewable QA tables.")] = Path(
        "../docs/qa/data/boundary-change-2012-2024"
    ),
) -> None:
    """Classify DS changes 2012->2024, write relations, comparisons and the district series."""
    from slf import history
    from slf.storage import from_env

    storage = from_env()
    missing = [k for k in history.PDF_PAGES if not (pages / k).is_dir()]
    if missing:
        typer.echo("PDF page text missing; for each, run:", err=True)
        for k in missing:
            prefix, name, which = history.PDF_PAGES[k]
            ref = history.latest_snapshot(storage, prefix, name)
            typer.echo(
                f"  swift scripts/pdf_pages.swift <data>/{ref.key} {pages / k} <pages: {which}>",
                err=True,
            )
        raise typer.Exit(2)
    result = history.run(storage, pages, catalog)
    rel = catalog / "geographies" / "relations" / "succession_ds_2012-2024.csv"
    for p in history.write(result, out_dir, rel, qa_dir):
        typer.echo(f"wrote {p}")
    c = result.checks
    for year, src in (("2012", "gn_file"), ("2024", "gn_workbook")):
        typer.echo(
            f"{year}: {src} {c[f'national_{year}_{src}']:,}; Table 3.3 "
            f"{c[f'national_{year}_table_3_3']:,}; DS sum {c[f'national_{year}_ds_sum']:,}"
        )
    typer.echo(
        f"DS 2012: {c['ds_2012_count']} (Table 2.3: {c['ds_2012_count_table_2_3']}); "
        f"in Abstract 2.7: {c['ds_2012_rows_in_abstract_2_7']}"
    )
    typer.echo(
        "2012 unit change types: "
        + str(result.result.units_2012["change_type"].value_counts().to_dict())
    )
    typer.echo(
        "2024 unit change types: "
        + str(result.result.units_2024["change_type"].value_counts().to_dict())
    )
    typer.echo(
        "comparison labels: " + str(result.result.comparison["comparison"].value_counts().to_dict())
    )


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


electoral_app = typer.Typer(help="Electoral geography commands (G05, scheme electoral).")
app.add_typer(electoral_app, name="electoral")


@electoral_app.command("build")
def electoral_build(
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build.")] = Path(
        "./data/build/geography-spine"
    ),
    census_dir: Annotated[
        list[Path], typer.Option(help="Census build folders with observations.parquet.")
    ] = [  # noqa: B006
        Path("./data/build/census-2024-gnd-tables"),
        Path("./data/build/census-2024-topic-tables"),
    ],
    results: Annotated[Path, typer.Option(help="election-results observations.")] = Path(
        "./data/build/election-results/observations.parquet"
    ),
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    out_dir: Annotated[Path, typer.Option(help="Where to write the build.")] = Path(
        "./data/build/electoral"
    ),
) -> None:
    """Write ED/PD codes and relations to the catalogue; run G05 checks and denominators.

    Needs `slf snapshot election-results` (for the register) and its page text. Anything derived
    from nuuuwan's gig-data stays in the build folder (no licence; internal QA only).
    """
    import pandas as pd

    from slf.datasets import election_snapshot as snap
    from slf.datasets import electoral_geography as eg
    from slf.datasets.election_results import build_dir

    storage = from_env()
    register = snap.latest(storage, snap.REGISTER_FILE)
    text_root = build_dir() / snap.DATASET_ID / "text"
    problems = snap.extract_text([register], storage, text_root)
    reg = eg.parse_register(snap.page_texts(snap.text_dir(text_root, register)))
    for p in problems + reg.problems:
        typer.echo(f"register: {p}", err=True)
    if problems or reg.problems:
        raise typer.Exit(1)
    for path in eg.write_catalog(reg, register, catalog):
        typer.echo(f"wrote {path}")
    obs = pd.read_parquet(results)
    electors = obs[(obs["indicator_id"] == "electors_registered") & obs["breakdown"].isna()]
    result = eg.build(
        storage,
        reg,
        spine_dir,
        census_dir,
        catalog,
        {
            str(g): float(v)
            for g, v in zip(electors["geography_id"], electors["value"], strict=True)
        },
        out_dir,
    )
    for p in result.outputs:
        typer.echo(f"wrote {p}")
    for e in result.errors:
        typer.echo(f"error: {e}", err=True)
    if result.errors:
        raise typer.Exit(1)


composition_app = typer.Typer(
    help="GN-composed geographies (G05, schemes la and health).", no_args_is_help=True
)
app.add_typer(composition_app, name="composition")


@composition_app.command("build")
def composition_build(
    scheme: Annotated[str, typer.Option(help="la (local authorities) or health (MOH areas).")],
    vintage: Annotated[str, typer.Option(help="Vintage label, for example mopa-2025.")] = "",
    units: Annotated[
        Path | None, typer.Option(help="Unit list CSV: unit_code,name[,kind].")
    ] = None,
    membership: Annotated[
        Path | None, typer.Option(help="Membership CSV: gn_code,unit_code[,weight].")
    ] = None,
    source_dataset: Annotated[
        str | None, typer.Option(help="Catalogue dataset id of the membership list.")
    ] = None,
    code_system: Annotated[
        str, typer.Option(help="Crosswalk for gn_code: a file in codes/, or 'pcode'.")
    ] = "pcode",
    method: Annotated[
        str, typer.Option(help="Relation method: official_list, attribute, overlay_area ...")
    ] = "official_list",
    gig_internal: Annotated[
        bool,
        typer.Option(help="Internal run on nuuuwan gig-data (no licence; nothing committed)."),
    ] = False,
    with_geometry: Annotated[
        bool, typer.Option(help="With --gig-internal: also fetch unit shapes for the IoU check.")
    ] = False,
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build.")] = Path(
        "./data/build/geography-spine"
    ),
    census_dir: Annotated[
        list[Path], typer.Option(help="Census build folders with observations.parquet.")
    ] = [  # noqa: B006
        Path("./data/build/census-2024-gnd-tables"),
        Path("./data/build/census-2024-topic-tables"),
    ],
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    out_dir: Annotated[
        Path | None, typer.Option(help="Where to write the build (default data/build/<scheme>).")
    ] = None,
) -> None:
    """Compose a non-nesting scheme from GN divisions; run G05 checks and denominators.

    Codes and relations go to the catalogue only if the membership dataset's recorded rights
    allow it. Otherwise the run is internal: files carry `internal` in their names and stay in
    the build folder.
    """
    from slf.datasets import composed_geography as cg

    if scheme not in cg.SCHEMES:
        typer.echo(f"unknown scheme {scheme!r}; known: {sorted(cg.SCHEMES)}", err=True)
        raise typer.Exit(2)
    spec = cg.SCHEMES[scheme]
    geoms: dict[str, object] = {}
    totals: dict[str, float] | None = None
    if gig_internal:
        unit_rows, member_rows, geoms, totals = cg.gig_inputs(
            from_env(), spec, with_geometry=with_geometry
        )
        source_dataset, code_system, method = cg.GIG_SOURCE_DATASET, "nuuuwan", "attribute"
        vintage = vintage or "gig-2026-11"
    else:
        if units is None or membership is None or source_dataset is None or not vintage:
            typer.echo(
                "need --units, --membership, --source-dataset and --vintage (or --gig-internal)",
                err=True,
            )
            raise typer.Exit(2)
        unit_rows, member_rows = cg.read_units(units), cg.read_membership(membership)
    publishable, rights_note = cg.rights_allow_catalog(catalog, source_dataset)
    if gig_internal:
        publishable = False
    composed = cg.compose(
        spec,
        unit_rows,
        member_rows,
        cg.read_crosswalk(catalog, code_system),
        cg.spine_gn_ids(spine_dir),
        method=f"{method} ({source_dataset})",
        source=source_dataset,
    )
    result = cg.build(
        composed,
        vintage=vintage,
        code_system=source_dataset,
        relation_method=method,
        spine_dir=spine_dir,
        census_dirs=census_dir,
        catalog=catalog,
        out_dir=out_dir or Path(DEFAULT_BUILD_DIR) / scheme,
        publishable=publishable,
        rights_note=rights_note,
        unit_geoms=geoms or None,
        published_totals=totals,
        published_label="nuuuwan's own unit populations (unlicensed, comparison only)"
        if gig_internal
        else "published totals",
    )
    typer.echo(f"{scheme}: {rights_note}")
    for miss in cg.missing_shapes:
        typer.echo(f"  shape not fetched: {miss}", err=True)
    for key, value in result.summary.items():
        typer.echo(f"  {key}: {value}")
    for p in result.outputs:
        typer.echo(f"wrote {p}")
    from slf.datasets import composed_profiles as cp

    out = out_dir or Path(DEFAULT_BUILD_DIR) / scheme
    prof, summary = cp.build_profiles(
        out, scheme, publishable=publishable, source_note=f"{source_dataset} ({rights_note})"
    )
    typer.echo(f"wrote {prof}: {summary}")


@composition_app.command("profile")
def composition_profile(
    scheme: Annotated[str, typer.Option(help="la or health.")],
    build_dir: Annotated[
        Path | None, typer.Option(help="Composition build folder (default data/build/<scheme>).")
    ] = None,
    publishable: Annotated[
        bool, typer.Option(help="Read the files without `_internal`; only after a rights gate.")
    ] = False,
) -> None:
    """Write per-unit profiles from an existing composition build (no download needed)."""
    from slf.datasets import composed_profiles as cp

    folder = build_dir or Path(DEFAULT_BUILD_DIR) / scheme
    out, summary = cp.build_profiles(
        folder,
        scheme,
        publishable=publishable,
        source_note="internal run on nuuuwan gig-data (no licence); not for publication"
        if not publishable
        else "see composition QA",
    )
    typer.echo(f"wrote {out}: {summary}")


atlas_app = typer.Typer(
    help="Web atlas bundle: display geometry, neighbours, profile and change files.",
    no_args_is_help=True,
)
app.add_typer(atlas_app, name="atlas")


@atlas_app.command("export")
def atlas_export(
    release_dir: Annotated[Path, typer.Option(help="Release folder to read.")],
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    profile_dir: Annotated[
        Path | None, typer.Option(help="Profile build folder (`slf profile build`).")
    ] = None,
    history_dir: Annotated[
        Path | None, typer.Option(help="History build folder (`slf history build`).")
    ] = None,
    catalog: Annotated[
        Path | None, typer.Option(help="Catalogue folder (ED grouping, election source).")
    ] = Path("../catalog"),
    spaces_dir: Annotated[
        Path | None, typer.Option(help="Vector spaces v2 folder (`slf profile spaces`).")
    ] = None,
    grid_dir: Annotated[
        Path | None, typer.Option(help="Grid build folder (`slf grid build`).")
    ] = None,
    landscape_dir: Annotated[
        Path | None, typer.Option(help="Landscape build folder (`slf spatial build`).")
    ] = None,
    subnational_dir: Annotated[
        Path | None, typer.Option(help="Sub-national build folder (`slf subnational build`).")
    ] = None,
    events_dir: Annotated[
        Path | None, typer.Option(help="Events build folder (`slf events`).")
    ] = None,
    hazard_dir: Annotated[
        Path | None,
        typer.Option(help="HeiGIT access and DesInventar build (`slf hazard-access build`)."),
    ] = None,
    units_dir: Annotated[
        Path | None,
        typer.Option(help="Build folder holding la/ and health/ (publishable profiles only)."),
    ] = None,
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/atlas"),
    public: Annotated[
        bool,
        typer.Option(
            "--public",
            help="Bundle for a public site: needs a publishable release; leaves out the D-038 "
            "change and trajectory files and the named features (D-049).",
        ),
    ] = False,
) -> None:
    """Write the derived files the map-first website reads (local, never part of a release)."""
    from slf.atlas import export

    manifest = export(
        release_dir,
        spine_dir,
        out_dir,
        profile_dir,
        history_dir,
        catalog,
        spaces_dir,
        grid_dir,
        landscape_dir,
        subnational_dir,
        events_dir,
        public=public,
        hazard_dir=hazard_dir,
        units_dir=units_dir,
    )
    geometry = manifest["geometry"]
    typer.echo(f"atlas bundle for {manifest['release']} -> {out_dir / manifest['release']}")
    typer.echo(
        f"geometry: {geometry['gn_polygons']} GN, {geometry['ds_polygons']} DS, "
        f"{geometry['detail_bytes'] / 1e6:.1f} MB detail"
    )
    typer.echo(f"adjacency pairs: {manifest['adjacency']['pairs']}")
    typer.echo(f"clusters: {manifest['clusters']['indicators']} indicators")
    typer.echo(f"profile: {manifest['profile']}")
    typer.echo(f"change: {manifest['change']}")
    typer.echo(f"electoral: {manifest['electoral']}")
    typer.echo(f"spaces: {manifest['spaces']}")
    typer.echo(f"grid: {manifest['grid']}")
    typer.echo(f"landscape: {manifest['landscape']}")
    typer.echo(f"features: {manifest['features']}")
    typer.echo(f"extra: {manifest['extra']}")


spatial_app = typer.Typer(
    help="Open spatial data: snapshots and place roll-ups (landscape lens).", no_args_is_help=True
)
app.add_typer(spatial_app, name="spatial")


@spatial_app.command("snapshot")
def spatial_snapshot(
    manifest: Annotated[Path, typer.Option(help="Manifest of original files.")] = Path(
        "../catalog/acquisition/spatial-manifest.csv"
    ),
    only: Annotated[str | None, typer.Option(help="Snapshot one dataset id only.")] = None,
    refresh: Annotated[bool, typer.Option(help="Fetch again even if a snapshot is held.")] = False,
    inventory: Annotated[Path | None, typer.Option(help="Write the inventory table here.")] = None,
) -> None:
    """Snapshot every original file in the manifest into raw/ (immutable, hashed, dated)."""
    from slf.spatial import acquire

    rows = acquire.read_manifest(manifest)
    if only:
        rows = [r for r in rows if r.dataset == only]
    results = acquire.acquire(from_env(), rows, refresh=refresh)
    failed = [r for r in results if r.ref is None]
    held = [r for r in results if r.ref is not None]
    total = sum(r.ref.size_bytes for r in held if r.ref is not None)
    typer.echo(f"{len(held)} of {len(results)} files held, {total / 1e6:.1f} MB")
    for r in failed:
        typer.echo(f"FAILED {r.row.dataset} {r.row.filename}: {r.error}")
    if inventory:
        inventory.write_text(acquire.inventory_markdown(results), encoding="utf-8")
    if failed:
        raise typer.Exit(1)


@spatial_app.command("overture")
def spatial_overture(
    theme: Annotated[str, typer.Argument(help="buildings or places")],
    release: Annotated[str, typer.Option(help="Overture release id, e.g. 2026-10-21.0")],
    data_root: Annotated[Path, typer.Option(help="Data root to write raw/overture/ under.")] = Path(
        "./data"
    ),
) -> None:
    """Extract Sri Lanka's rows of an Overture theme from the public release (large download)."""
    from slf.spatial import overture

    meta = overture.extract(theme, release, data_root)
    typer.echo(json_dumps(meta))


def json_dumps(value: object) -> str:
    import json

    return json.dumps(value, indent=2)


@spatial_app.command("build")
def spatial_build(
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/landscape"),
    data_root: Annotated[
        list[Path] | None, typer.Option(help="Data roots holding raw/ (repeatable).")
    ] = None,
) -> None:
    """Roll open raster and point layers up to every place (terrain, cover, water, built-up)."""
    from slf.spatial import build

    result = build.build(data_root or [Path("./data")], spine_dir, out_dir)
    typer.echo(json_dumps(result))
    typer.echo(f"report: {out_dir / 'qa.md'}")
    if result["errors"]:
        raise typer.Exit(1)


@spatial_app.command("catalogue")
def spatial_catalogue(
    catalog: Annotated[Path, typer.Option(help="Catalogue root.")] = Path("../catalog"),
) -> None:
    """Write the landscape and feature indicator entries from the build's own specs."""
    from slf.spatial import layers

    for spec in layers.SPECS.values():
        (catalog / "indicators" / f"{spec.id}.yaml").write_text(
            layers.indicator_yaml(spec), encoding="utf-8"
        )
    typer.echo(f"wrote {len(layers.SPECS)} indicator entries")


@spatial_app.command("space")
def spatial_space(
    landscape_dir: Annotated[Path, typer.Option(help="Landscape build folder.")] = Path(
        "./data/build/landscape"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    profile_dir: Annotated[
        Path | None, typer.Option(help="Profile build folder, for cross-space contrasts.")
    ] = None,
) -> None:
    """Build the proposed `landscape` vector space and its similar-place lists (D-045)."""
    import pandas as pd

    from slf.spatial import space

    summary = space.build(
        pd.read_parquet(landscape_dir / "observations.parquet"),
        pd.read_parquet(spine_dir / "geographies.parquet"),
        landscape_dir,
        profile_dir,
    )
    for level, info in summary["levels"].items():
        typer.echo(
            f"{level}: {info['places']} places, {info['axes_retained']} axes, "
            f"{info['variance_explained_retained']:.1%} of variance"
        )
    typer.echo(f"wrote {landscape_dir / 'vectors'}")


@spatial_app.command("findings")
def spatial_findings(
    landscape_dir: Annotated[Path, typer.Option(help="Landscape build folder.")] = Path(
        "./data/build/landscape"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    census_gn: Annotated[Path, typer.Option(help="Census 2024 GN observations.")] = Path(
        "./data/build/census-2024-gnd-tables/observations.parquet"
    ),
    census_topics: Annotated[Path, typer.Option(help="Census 2024 topic observations.")] = Path(
        "./data/build/census-2024-topic-tables/observations.parquet"
    ),
    data_root: Annotated[
        list[Path] | None, typer.Option(help="Data roots holding raw/ (repeatable).")
    ] = None,
) -> None:
    """Join the landscape layers to Census 2024 by place and write findings.json (analysis only)."""
    from slf.spatial import findings

    out = findings.run(
        data_root or [Path("./data")], spine_dir, landscape_dir, census_gn, census_topics
    )
    typer.echo(f"wrote {landscape_dir / 'findings.json'} ({', '.join(out)})")


grid_app = typer.Typer(help="Analytic grid (H3) and GN-to-hex weights.", no_args_is_help=True)
app.add_typer(grid_app, name="grid")


@grid_app.command("build")
def grid_build(
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/grid"),
    resolution: Annotated[int, typer.Option(help="H3 resolution.")] = 9,
) -> None:
    """Build H3 cells over the GN divisions and equal-share GN-to-hex weights (D-014)."""
    from slf import grid

    summary = grid.build(spine_dir, out_dir, resolution)
    for key, value in summary.items():
        typer.echo(f"{key}: {value}")


@app.command("resolve")
def resolve(
    lon: Annotated[float, typer.Option(help="Longitude (EPSG:4326).")],
    lat: Annotated[float, typer.Option(help="Latitude (EPSG:4326).")],
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    relations_dir: Annotated[Path, typer.Option(help="Relations folder.")] = Path(
        "../catalog/geographies/relations"
    ),
) -> None:
    """Which GN, DS, district, province and electoral district contain a point."""
    from slf import resolver

    typer.echo(resolver.as_json(resolver.Resolver(spine_dir, relations_dir).resolve(lon, lat)))


subnational_app = typer.Typer(
    help="Stage 3 sub-national indicators from p-coded open tables.", no_args_is_help=True
)
app.add_typer(subnational_app, name="subnational")


@subnational_app.command("build")
def subnational_build(
    raw_root: Annotated[Path, typer.Option(help="Folder holding raw/<source>/<dataset>/.")] = Path(
        "./data/raw"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path(
        "./data/build/subnational"
    ),
) -> None:
    """Poverty (OPHI), rainfall and vegetation (WFP), rural access (HeiGIT), joined by p-code."""
    from slf import subnational

    summary = subnational.build(raw_root, spine_dir, out_dir)
    typer.echo(f"{summary['rows']} rows, {len(summary['indicators'])} indicators")
    for item in summary["unmatched_or_incomplete"] + summary["not_held"]:
        typer.echo(f"  {item}")
    typer.echo(f"report: {out_dir / 'qa.md'}")


@app.command("freshness")
def freshness_check(
    catalog: Annotated[Path, typer.Option(help="Catalogue folder.")] = Path("../catalog"),
    raw_root: Annotated[
        list[Path] | None,
        typer.Option(help="Folders holding raw/<source>/<dataset>/ (repeatable)."),
    ] = None,
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/freshness"),
    probe: Annotated[
        bool, typer.Option(help="HEAD each landing page for ETag/Last-Modified (polite, slow).")
    ] = False,
) -> None:
    """Release calendar: what is held, what is scheduled, what is overdue (D05)."""
    from slf import freshness

    calendar = freshness.build(catalog, raw_root or [Path("./data/raw")], out_dir, probe=probe)
    typer.echo(f"{len(calendar['datasets'])} datasets: {calendar['counts']}")
    for row in calendar["datasets"]:
        if row["state"] == "overdue" or row["page_changed"]:
            typer.echo(f"  {row['state']}: {row['dataset_id']} (last {row['last_snapshot']})")
    typer.echo(f"wrote {out_dir / 'calendar.json'}")


@app.command("evalset")
def evalset(
    release_dir: Annotated[Path, typer.Option(help="Release folder to draw answers from.")],
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/evals"),
    size: Annotated[int, typer.Option(help="Number of questions.")] = 150,
) -> None:
    """AI evaluation set (A02): questions with expected answers copied from the release."""
    from slf import evalset as module

    summary = module.build(release_dir, out_dir, size)
    typer.echo(json.dumps(summary, indent=2))


@app.command("events")
def events_build(
    raw_root: Annotated[Path, typer.Option(help="Folder holding raw/<source>/<dataset>/.")] = Path(
        "./data/raw"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path("./data/build/events"),
) -> None:
    """Events by place: 2025 flood extent, yearly fire detections, storm passes (D-020)."""
    from slf import events

    summary = events.build(raw_root, spine_dir, out_dir)
    typer.echo(json.dumps(summary, indent=2)[:3000])


hazard_app = typer.Typer(
    help="HeiGIT accessibility and DesInventar records: crosswalks, then indicators.",
    no_args_is_help=True,
)
app.add_typer(hazard_app, name="hazard-access")


@hazard_app.command("build")
def hazard_access_build(
    raw_root: Annotated[Path, typer.Option(help="Folder holding raw/<source>/<dataset>/.")] = Path(
        "./data/raw"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    catalog: Annotated[
        Path, typer.Option(help="Catalogue root (writes geographies/codes).")
    ] = Path("../catalog"),
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = Path(
        "./data/build/hazard-access"
    ),
) -> None:
    """Write the heigit-iso and desinventar crosswalks, then the joinable indicators."""
    from slf import hazard_access

    summary = hazard_access.build(raw_root, spine_dir, catalog, out_dir, out_dir / "_work")
    typer.echo(f"{summary['rows']} rows, {len(summary['indicators'])} indicators")


@hazard_app.command("checks")
def hazard_access_checks(
    raw_root: Annotated[Path, typer.Option(help="Folder holding raw/<source>/<dataset>/.")] = Path(
        "./data/raw"
    ),
    spine_dir: Annotated[Path, typer.Option(help="Geography spine build folder.")] = Path(
        "./data/build/geography-spine"
    ),
    release_dir: Annotated[
        Path, typer.Option(help="A release folder (census 2024 figures).")
    ] = Path("./data/build/releases/v2026.11.19"),
    build_dir: Annotated[Path, typer.Option(help="`slf hazard-access build` output.")] = Path(
        "./data/build/hazard-access"
    ),
    catalog: Annotated[Path, typer.Option(help="Catalogue root.")] = Path("../catalog"),
) -> None:
    """Cross-check the indicators against independent figures; writes checks.md and checks.json."""
    from slf import hazard_checks

    checks = hazard_checks.run(
        raw_root, spine_dir, release_dir, build_dir / "observations.parquet", catalog
    )
    path = hazard_checks.write(checks, build_dir)
    for c in checks:
        typer.echo(f"{c.id}: {c.result}")
    typer.echo(f"report -> {path}")
