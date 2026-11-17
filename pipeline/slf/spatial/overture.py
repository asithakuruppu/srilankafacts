"""Extract Sri Lanka's rows from an Overture Maps release (public S3, no account).

Overture publishes each theme as global GeoParquet files, so there is no "Sri Lanka file" to
snapshot. This reads only the row groups whose bounding boxes touch Sri Lanka's bounding box and
writes one GeoParquet file per theme under ``raw/overture/<dataset>/<time>/`` with a
``.meta.json`` recording the release, the filter, the columns kept and the sha256 of the file
written. The extract is our file, not Overture's bytes; the release id makes it repeatable.

Only physical and naming attributes are kept (AGENTS rule 11): no addresses, phones, websites
or social links.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from pyarrow import fs

BUCKET = "overturemaps-us-west-2"
# Sri Lanka's bounding box with a small margin (COD-AB v03 extent is 79.52-81.88 E, 5.92-9.84 N)
BBOX = (79.45, 5.85, 81.95, 9.90)


@dataclass(frozen=True)
class Theme:
    dataset: str
    path: str
    columns: tuple[str, ...]
    licence: str


THEMES: dict[str, Theme] = {
    "buildings": Theme(
        "overture-buildings",
        "theme=buildings/type=building",
        (
            "id",
            "geometry",
            "bbox",
            "sources",
            "subtype",
            "class",
            "height",
            "num_floors",
            "roof_shape",
            "names",
        ),
        "ODbL 1.0 (Overture buildings; includes OpenStreetMap, Microsoft and Google data)",
    ),
    "places": Theme(
        "overture-places",
        "theme=places/type=place",
        (
            "id",
            "geometry",
            "bbox",
            "sources",
            "names",
            "basic_category",
            "taxonomy",
            "operating_status",
            "confidence",
            "brand",
        ),
        "CDLA-Permissive-2.0 (Overture places; per-row sources listed in `sources`)",
    ),
}


def _read_with_retry(
    fragment: ds.Fragment, columns: list[str], condition: pc.Expression
) -> pa.Table:
    """Read one global file's matching rows; network errors are retried, then raised."""
    delay = 5.0
    for attempt in range(6):
        try:
            return fragment.to_table(columns=columns, filter=condition)
        except OSError:
            if attempt == 5:
                raise
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def extract(theme_key: str, release: str, data_root: Path) -> dict[str, object]:
    theme = THEMES[theme_key]
    s3 = fs.S3FileSystem(anonymous=True, region="us-west-2")
    dataset = ds.dataset(
        f"{BUCKET}/release/{release}/{theme.path}/", filesystem=s3, format="parquet"
    )
    xmin, ymin, xmax, ymax = BBOX
    touches = (
        (pc.field("bbox", "xmin") <= xmax)
        & (pc.field("bbox", "xmax") >= xmin)
        & (pc.field("bbox", "ymin") <= ymax)
        & (pc.field("bbox", "ymax") >= ymin)
    )
    columns = [c for c in theme.columns if c in dataset.schema.names]
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"{theme.dataset}-lk-{release}.parquet"
    # Written outside raw/ first: a failed run must never leave a partial file among snapshots.
    work = data_root / "tmp" / f"{theme.dataset}-{stamp}"
    work.mkdir(parents=True, exist_ok=False)
    partial = work / name
    schema = pa.schema([dataset.schema.field(c) for c in columns], metadata=dataset.schema.metadata)
    rows = 0
    fragments = list(dataset.get_fragments())
    with pq.ParquetWriter(partial, schema, compression="zstd") as writer:
        for number, fragment in enumerate(fragments, start=1):
            table = _read_with_retry(fragment, columns, touches)
            if table.num_rows:
                writer.write_table(table.cast(schema))
                rows += table.num_rows
            if number % 25 == 0 or number == len(fragments):
                print(
                    f"{theme.dataset}: {number}/{len(fragments)} files read, {rows} rows",
                    flush=True,
                )
    folder = data_root / "raw" / "overture" / theme.dataset / stamp
    folder.mkdir(parents=True, exist_ok=False)
    target = folder / name
    partial.rename(target)
    work.rmdir()
    sha = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    meta = {
        "key": f"raw/overture/{theme.dataset}/{stamp}/{name}",
        "sha256": sha.hexdigest(),
        "url": f"s3://{BUCKET}/release/{release}/{theme.path}/",
        "retrieved_at": stamp,
        "size_bytes": target.stat().st_size,
        "licence_note": theme.licence,
        "extract": {
            "release": release,
            "bbox_filter_xmin_ymin_xmax_ymax": BBOX,
            "columns_kept": columns,
            "columns_dropped": sorted(set(dataset.schema.names) - set(columns)),
            "rows": rows,
            "note": "Extract written by slf.spatial.overture; sha256 is of this file, not of "
            "Overture's global files.",
        },
    }
    (folder / f"{name}.meta.json").write_text(json.dumps(meta, indent=2))
    return meta
