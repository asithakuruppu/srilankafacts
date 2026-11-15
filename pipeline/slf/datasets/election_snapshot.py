"""Snapshots of Election Commission files for the election atlas (Stage 2).

The Election Commission of Sri Lanka publishes the 2024 presidential election results as one PDF
per polling division, one postal-vote PDF per electoral district, one PDF per district and
all-island summaries, linked from a single results page. The page itself is snapshotted first, and
the list of PDFs comes from that snapshot, so the file list has provenance too.

The register of electors by polling division (2016-2025) is the official list of the 22 electoral
districts and 160 polling divisions with their letters and names.

Requests are paced (``DELAY_SECONDS``) and each file is fetched once: an existing snapshot with the
same file name is reused. A failed download is recorded, never silently skipped.
"""

from __future__ import annotations

import json
import re
import shutil
import ssl
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from slf.snapshot import SnapshotRef, snapshot_bytes, snapshot_url
from slf.storage import Storage

SOURCE_ID = "election-commission"
DATASET_ID = "election-results"
EC_BASE = "https://elections.gov.lk"
PRE2024_INDEX_URL = f"{EC_BASE}/si/elections/PRE_2024_Results.html"
PRE2024_INDEX_FILE = "PRE_2024_Results.html"
PRE2024_PDF_RE = re.compile(
    r'href="(https://elections\.gov\.lk/web/wp-content/uploads/2024/09/PRE_2024_Results/'
    r'([A-Za-z0-9_]+\.pdf))"'
)
REGISTER_URL = (
    f"{EC_BASE}/web/wp-content/uploads/2026/10/All_District_Registered_Electores_2016_2025.pdf"
)
REGISTER_FILE = "All_District_Registered_Electores_2016_2025.pdf"
LICENCE_NOTE = "rights unclear: no terms of use found on elections.gov.lk (2026-11-15)"
DELAY_SECONDS = 1.0


def ssl_context() -> ssl.SSLContext:
    """A verifying context using the certifi bundle (installed with pyproj).

    elections.gov.lk's chain ends at a Sectigo R46 root that Python's default store here does not
    have; certifi does. Verification stays on.
    """
    import certifi

    return ssl.create_default_context(cafile=certifi.where())


@dataclass
class SnapshotLog:
    stored: list[SnapshotRef] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)


def latest(storage: Storage, filename: str) -> SnapshotRef:
    """The most recent snapshot of ``filename`` for this dataset."""
    keys = sorted(
        k for k in storage.list(f"raw/{SOURCE_ID}/{DATASET_ID}") if k.endswith("/" + filename)
    )
    if not keys:
        raise FileNotFoundError(f"no snapshot {filename}; run `slf snapshot {DATASET_ID}`")
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})


def pdf_links(index_html: str) -> list[tuple[str, str]]:
    """(url, filename) for each result PDF linked from the results page, in page order.

    Links whose file name starts with ``XXX`` are placeholders on the page (for example
    ``XXXVanni_Displaced_V1.pdf``) and are not fetched.
    """
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for url, name in PRE2024_PDF_RE.findall(index_html):
        if name in seen or name.startswith("XXX"):
            continue
        seen.add(name)
        out.append((url, name))
    return out


def _fetch(storage: Storage, url: str, filename: str, log: SnapshotLog) -> SnapshotRef | None:
    try:
        return latest(storage, filename)
    except FileNotFoundError:
        pass
    try:
        ref = snapshot_url(
            storage,
            source=SOURCE_ID,
            dataset=DATASET_ID,
            url=url,
            filename=filename,
            licence_note=LICENCE_NOTE,
            timeout=90.0,
            ssl_context=ssl_context(),
        )
    except Exception as exc:  # recorded, never dropped (AGENTS rule 6)
        log.failed.append((url, f"{type(exc).__name__}: {exc}"))
        return None
    time.sleep(DELAY_SECONDS)
    if not storage.get(ref.key)[:5].startswith(b"%PDF") and filename.endswith(".pdf"):
        log.failed.append((url, "response is not a PDF (the server may have sent an error page)"))
    log.stored.append(ref)
    return ref


def snapshot_all(storage: Storage) -> tuple[SnapshotRef, SnapshotLog]:
    """Snapshot the results page, every result PDF it links and the register of electors."""
    log = SnapshotLog()
    index = _fetch(storage, PRE2024_INDEX_URL, PRE2024_INDEX_FILE, log)
    if index is None:
        raise RuntimeError(f"could not fetch {PRE2024_INDEX_URL}: {log.failed}")
    html = storage.get(index.key).decode("utf-8", errors="replace")
    for url, name in pdf_links(html):
        _fetch(storage, url, name, log)
    _fetch(storage, REGISTER_URL, REGISTER_FILE, log)
    if log.failed:
        report = "\n".join(f"{u}\t{e}" for u, e in log.failed)
        snapshot_bytes(
            storage,
            source=SOURCE_ID,
            dataset=DATASET_ID,
            filename="snapshot-failures.tsv",
            content=report.encode(),
            licence_note="pipeline log",
        )
    return index, log


# --- page text (PDFKit text layer + on-device Vision OCR, macOS) -----------------------------

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"


def text_dir(text_root: Path, ref: SnapshotRef) -> Path:
    """Where the page text of one snapshot lives: keyed by the snapshot's sha256."""
    name = ref.key.rsplit("/", 1)[-1]
    return text_root / ref.sha256[:16] / name


def extract_text(refs: list[SnapshotRef], storage: Storage, text_root: Path) -> list[str]:
    """Run ``scripts/pdf_ocr.swift`` (compiled once) for snapshots whose text is not cached.

    Returns problems (unreadable files). The text is derived data in the build folder; the raw
    snapshot is never touched.
    """
    todo = [r for r in refs if not any(text_dir(text_root, r).glob("page-*.ocr.json"))]
    if not todo:
        return []
    if shutil.which("swiftc") is None:
        return [f"{r.key}: no page text and swiftc is not available (macOS only)" for r in todo]
    text_root.mkdir(parents=True, exist_ok=True)
    binary = text_root / "pdf_ocr"
    source = SCRIPTS_DIR / "pdf_ocr.swift"
    if not binary.exists() or binary.stat().st_mtime < source.stat().st_mtime:
        subprocess.run(["swiftc", "-O", str(source), "-o", str(binary)], check=True)
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        for ref in todo:
            target = text_dir(text_root, ref)
            pdf = Path(tmp) / target.name
            pdf.write_bytes(storage.get(ref.key))
            for _attempt in range(3):  # Vision occasionally fails transiently; retry
                done = subprocess.run(
                    [str(binary), str(target.parent), str(pdf)], capture_output=True, text=True
                )
                if done.returncode == 0:
                    break
                shutil.rmtree(target, ignore_errors=True)  # never keep partial page text
            else:
                problems.append(f"{ref.key}: {done.stderr.strip() or 'pdf_ocr failed'}")
    return problems


def page_texts(directory: Path) -> dict[int, str]:
    return {int(p.stem[-3:]): p.read_text(encoding="utf-8") for p in directory.glob("page-*.txt")}


def page_ocr(directory: Path) -> dict[int, list[dict[str, object]]]:
    return {
        int(p.name[5:8]): json.loads(p.read_text(encoding="utf-8"))
        for p in directory.glob("page-*.ocr.json")
    }


def latest_any(storage: Storage, source: str, dataset: str, filename: str) -> SnapshotRef:
    """The most recent snapshot of ``filename`` for any source/dataset pair."""
    keys = sorted(k for k in storage.list(f"raw/{source}/{dataset}") if k.endswith("/" + filename))
    if not keys:
        raise FileNotFoundError(f"no snapshot {filename} under raw/{source}/{dataset}")
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})
