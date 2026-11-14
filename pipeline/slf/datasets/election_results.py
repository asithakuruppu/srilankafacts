"""Presidential Election 2024 results by polling division and electoral district (Stage 2).

Source: Election Commission of Sri Lanka, 2024 presidential results page (one signed result sheet
per polling division, one postal-vote sheet per electoral district, district and all-island sheets).
See ``docs/research/sources/election-commission.md`` and ``docs/methods/election-results.md``.

Footprints:

- a PD sheet's values sit on the PD (``LK-PD-NNX``);
- a postal-vote sheet's values sit on the ED (``LK-ED-NN``) with breakdown ``vote_type: postal``.
  Postal votes are never pushed down to PDs;
- ED values (no breakdown) are the sum of the ED's PD sheets plus its postal sheet; the national
  values (``LK``) are the sum of all of them. On the Commission's sheets, an ED's registered
  electors are its PDs' electors plus its postal voters (checked against nuuuwan's ED rows), so the
  sum is like for like. Sums are checked against the district and all-island sheets where those read.

Values are OCR-extracted on-device (``election_parse``) and stay ``machine_extracted``. Values that
could not be read, or that a sheet's own arithmetic does not confirm, are ``not_available`` and go
to the verification sheet. nuuuwan's ``lk_elections`` TSV is a cross-check only.

Rights are unclear (no terms found): nothing here is publishable until a lead decision allows it.
"""

from __future__ import annotations

import io
import json
import os
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from slf.dataset import Dataset, QAReport, Row, check_observations
from slf.datasets import election_snapshot as snap
from slf.datasets.election_parse import CANDIDATES, Sheet, SheetPage, boxes, parse_sheet
from slf.datasets.electoral_geography import ed_id, parse_register, pd_id
from slf.snapshot import SnapshotRef, snapshot_url
from slf.storage import Storage

DATASET_ID = snap.DATASET_ID
VINTAGE = "ec-2024"
ELECTION_DATE = "2024-09-21"
CLAIM_PREFIX = "ec-pre2024"
NUUUWAN_COMMIT = "5bae5346e1e86711fc866657ff862a25e3f6b376"  # nuuuwan/lk_elections master, 2026-11-15
NUUUWAN_URL = (
    f"https://raw.githubusercontent.com/nuuuwan/lk_elections/{NUUUWAN_COMMIT}/public/data/"
    "elections/government-elections-presidential.regions-ec.2024.tsv"
)
NUUUWAN_FILE = "government-elections-presidential.regions-ec.2024.tsv"
SHEET_FILE_RE = re.compile(r"^(\d{1,2})_([A-Z]{1,2})\.pdf$")
TOTAL_INDICATORS = {
    "electors": "electors_registered",
    "polled": "votes_polled",
    "valid": "votes_valid",
    "rejected": "votes_rejected",
}
DISTRICT_FILES = {  # district result sheet per ED (file names as linked on the results page)
    1: "Colombo.pdf", 2: "Gampaha.pdf", 3: "Kalutara.pdf", 4: "Mahanuwara.pdf",
    5: "Matale.pdf", 6: "Nuwaraeliya.pdf", 7: "Galle.pdf", 8: "Matara.pdf",
    9: "Hambantota.pdf", 10: "Jaffna.pdf", 11: "Vanni.pdf", 12: "Batticaloa.pdf",
    13: "Digamadulla.pdf", 14: "Trincomalee.pdf", 15: "Kurunegala.pdf", 16: "Puttalam.pdf",
    17: "Anuradhapura.pdf", 18: "Polonnaruwa.pdf", 19: "Badulla.pdf", 20: "moneragala.pdf",
    21: "Ratnapura.pdf", 22: "Kegalle_D.pdf",
}  # fmt: skip
NATIONAL_FILE = "All_Island_Result.pdf"


def build_dir() -> Path:
    return Path(os.environ.get("SLF_BUILD_DIR", "./data/build"))


@dataclass
class Parsed:
    ref: SnapshotRef
    sheet: Sheet


def load_pages(directory: Path) -> list[SheetPage]:
    pages: list[SheetPage] = []
    for t in sorted(directory.glob("page-*.txt")):
        n = t.stem[-3:]

        def read(kind: str, n: str = n) -> list:
            path = directory / f"page-{n}.{kind}.json"
            return boxes(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else []

        pages.append(
            SheetPage(int(n), read("ocr"), read("strip"), t.read_text(encoding="utf-8"), read("col"))
        )
    return pages


def _pdf_refs(storage: Storage) -> dict[str, SnapshotRef]:
    """Latest snapshot per PDF file name."""
    refs: dict[str, SnapshotRef] = {}
    for key in sorted(storage.list(f"raw/{snap.SOURCE_ID}/{DATASET_ID}")):
        if key.endswith(".pdf.meta.json"):
            meta = json.loads(storage.get(key))
            ref = SnapshotRef(**{**meta, "reused": True})
            refs[ref.key.rsplit("/", 1)[-1]] = ref
    return refs


class ElectionResults(Dataset):
    dataset_id = DATASET_ID
    source_id = snap.SOURCE_ID

    def __init__(self) -> None:
        self.sheets: list[Parsed] = []
        self.checks: dict[int | str, Parsed] = {}
        self.register_pds: dict[str, str] = {}
        self.text_problems: list[str] = []
        self.nuuuwan: pd.DataFrame | None = None
        self.snapshot_failures: list[str] = []

    # -- snapshot ------------------------------------------------------------------------------

    def snapshot(self, storage: Storage) -> SnapshotRef:
        index, log = snap.snapshot_all(storage)
        self.snapshot_failures = [f"{u}: {e}" for u, e in log.failed]
        try:
            snap.latest_any(storage, "nuuuwan", "nuuuwan-lk-elections", NUUUWAN_FILE)
        except FileNotFoundError:
            snapshot_url(
                storage,
                source="nuuuwan",
                dataset="nuuuwan-lk-elections",
                url=NUUUWAN_URL,
                filename=NUUUWAN_FILE,
                licence_note="no licence (GitHub metadata 2026-11-15); cross-check only",
            )
        return index

    # -- extract -------------------------------------------------------------------------------

    def extract(self, storage: Storage, ref: SnapshotRef) -> list[Row]:
        refs = _pdf_refs(storage)
        text_root = build_dir() / DATASET_ID / "text"
        sheet_refs = {n: r for n, r in refs.items() if SHEET_FILE_RE.match(n)}
        check_refs = {
            **{ed: refs[f] for ed, f in DISTRICT_FILES.items() if f in refs},
            **({"LK": refs[NATIONAL_FILE]} if NATIONAL_FILE in refs else {}),
        }
        register = refs.get(snap.REGISTER_FILE)
        wanted = [*sheet_refs.values(), *check_refs.values(), *([register] if register else [])]
        self.text_problems = snap.extract_text(wanted, storage, text_root)

        if register is not None:
            reg = parse_register(snap.page_texts(snap.text_dir(text_root, register)))
            self.register_pds = {p.geography_id: p.name for p in reg.pds}
            self.register_problems = reg.problems
            self.register_ref = register
        for name, r in sorted(sheet_refs.items()):
            sheet = parse_sheet(name, load_pages(snap.text_dir(text_root, r)))
            self.sheets.append(Parsed(r, sheet))
        for key, r in check_refs.items():
            self.checks[key] = Parsed(r, parse_sheet(r.key.rsplit("/", 1)[-1], load_pages(snap.text_dir(text_root, r))))
        try:
            nref = snap.latest_any(storage, "nuuuwan", "nuuuwan-lk-elections", NUUUWAN_FILE)
            self.nuuuwan = pd.read_csv(io.BytesIO(storage.get(nref.key)), sep="\t").set_index(
                "entity_id"
            )
        except FileNotFoundError:
            self.nuuuwan = None
        rows: list[Row] = []
        for p in self.sheets:
            rows.extend(sheet_rows(p))
        return rows

    # -- harmonise -----------------------------------------------------------------------------

    def harmonise(self, rows: list[Row], ref: SnapshotRef) -> list[Row]:
        observations = [observation(r) for r in rows]
        observations += aggregate_rows(rows)
        observations += share_rows(observations)
        return observations

    # -- validate ------------------------------------------------------------------------------

    def validate(self, observations: list[Row]) -> QAReport:
        report = check_observations(self.dataset_id, observations)
        report.warnings += [f"text extraction: {p}" for p in self.text_problems]
        report.warnings += [f"snapshot: {p}" for p in self.snapshot_failures]
        report.errors += [f"register: {p}" for p in getattr(self, "register_problems", [])]
        pd_sheets = {
            pd_id(p.sheet.ed_number, p.sheet.pd_letter): p.sheet.file
            for p in self.sheets
            if p.sheet.kind == "pd" and p.sheet.ed_number and p.sheet.pd_letter
        }
        postal = {p.sheet.ed_number for p in self.sheets if p.sheet.kind == "postal"}
        missing = sorted(set(self.register_pds) - set(pd_sheets))
        extra = sorted(set(pd_sheets) - set(self.register_pds))
        if len(self.register_pds) != 160:
            report.errors.append(f"register lists {len(self.register_pds)} PDs, expected 160")
        if missing:
            report.errors.append(f"PDs in the register without a result sheet: {missing}")
        if extra:
            report.errors.append(f"result sheets for PDs not in the register: {extra}")
        if len(postal) != 22:
            report.errors.append(f"postal-vote sheets for {len(postal)} EDs, expected 22")
        for p in self.sheets:
            for problem in p.sheet.problems:
                report.warnings.append(f"{p.sheet.file}: {problem}")
        return report

    # -- publish -------------------------------------------------------------------------------

    def publish(self, observations: list[Row], report: QAReport, out_dir: str) -> list[str]:
        if not report.ok:
            raise RuntimeError(f"refusing to publish {self.dataset_id}: QA report has errors")
        out = Path(out_dir) / self.dataset_id
        out.mkdir(parents=True, exist_ok=True)
        frame = pd.DataFrame(observations)
        frame["breakdown"] = frame["breakdown"].map(
            lambda b: json.dumps(b, sort_keys=True) if b else None
        )
        frame = frame.sort_values(["geography_id", "indicator_id", "claim_id"]).reset_index(
            drop=True
        )
        paths = [out / "observations.parquet", out / "observations.csv", out / "qa.md"]
        frame.to_parquet(paths[0], index=False)
        frame.to_csv(paths[1], index=False)
        qa = qa_markdown(self, observations, report)
        paths[2].write_text(qa, encoding="utf-8")
        sheet = verification_sheet(self)
        paths.append(out / "verification-sheet.csv")
        sheet.to_csv(paths[-1], index=False)
        return [str(p) for p in paths]


# --- rows ------------------------------------------------------------------------------------


def _locator(file: str, page: int | None, what: str, how: str) -> str:
    where = f"p.{page}" if page else "page not identified"
    return f"{file} {where}, {what} (read: {how or 'unread'})"


def sheet_rows(p: Parsed) -> list[Row]:
    """One raw row per value on a PD or postal sheet."""
    s = p.sheet
    if s.ed_number is None or (s.kind == "pd" and s.pd_letter is None):
        return []
    if s.kind == "pd":
        geo, breakdown = pd_id(s.ed_number, s.pd_letter or ""), {}
    else:
        geo, breakdown = ed_id(s.ed_number), {"vote_type": "postal"}
    rows: list[Row] = []
    for key, indicator in TOTAL_INDICATORS.items():
        r = s.totals[key]
        rows.append(
            {
                "geo": geo,
                "indicator_id": indicator,
                "breakdown": dict(breakdown),
                "value": r.value,
                "how": r.how,
                "locator": _locator(s.file, r.page, f"line '{key}'", r.how),
                "sha": p.ref.sha256,
                "file": s.file,
                "kind": s.kind,
                "ed": s.ed_number,
            }
        )
    for ballot, code, name in CANDIDATES:
        r = s.candidates[code]
        rows.append(
            {
                "geo": geo,
                "indicator_id": "votes_candidate",
                "breakdown": {
                    **breakdown,
                    "ballot_number": str(ballot),
                    "party": code,
                    "candidate": name,
                },
                "value": r.value,
                "how": r.how,
                "locator": _locator(s.file, r.page, f"row '{code}' (ballot {ballot})", r.how),
                "sha": p.ref.sha256,
                "file": s.file,
                "kind": s.kind,
                "ed": s.ed_number,
            }
        )
    return rows


def _base(geo: str, indicator: str, breakdown: Mapping[str, str] | None) -> Row:
    key = ":".join(f"{k}={v}" for k, v in sorted((breakdown or {}).items()) if k != "candidate")
    unit = "persons" if indicator == "electors_registered" else "votes"
    universe = "registered_electors" if indicator == "electors_registered" else "votes"
    return {
        "claim_id": f"{CLAIM_PREFIX}:{geo}:{indicator}" + (f":{key}" if key else ""),
        "indicator_id": indicator,
        "geography_id": geo,
        "geography_vintage": VINTAGE,
        "period": ELECTION_DATE,
        "time_start": ELECTION_DATE,
        "time_end": ELECTION_DATE,
        "time_support": "snapshot",
        "support_type": "area_total",
        "footprint_ref": geo,
        "information_footprint_ref": None,
        "universe": universe,
        "collection_method": "admin_register",
        "sensitivity": "public",
        "revision_status": "final",
        "preferred": True,
        "breakdown": dict(breakdown) if breakdown else None,
        "unit": unit,
        "data_nature": "administrative_count",
        "verification": "machine_extracted",
        "dataset_id": DATASET_ID,
        "note_ids": [],
        "release": None,
    }


def observation(r: Row) -> Row:
    row = _base(r["geo"], r["indicator_id"], r["breakdown"] or None)
    ok = r["value"] is not None
    derived = r["how"] == "derived"
    row.update(
        {
            "value": float(r["value"]) if ok else None,
            "value_status": "normal" if ok else "not_available",
            "snapshot_sha256": r["sha"],
            "source_locator": r["locator"],
            "preferred_reason": (
                "Only claim: Election Commission result sheet"
                + (" (value fixed by the sheet's own total and printed percentages)" if derived else "")
            ),
            "note_ids": ["derived_from_sheet_total"] if derived else [],
        }
    )
    return row


def aggregate_rows(rows: list[Row]) -> list[Row]:
    """ED totals (PD sheets + postal sheet) and national totals; not_available if any part is."""
    parts: dict[tuple[str, str, str], list[Row]] = defaultdict(list)
    for r in rows:
        bd = {k: v for k, v in r["breakdown"].items() if k != "vote_type"}
        key = json.dumps(bd, sort_keys=True)
        parts[(ed_id(r["ed"]), r["indicator_id"], key)].append(r)
        parts[("LK", r["indicator_id"], key)].append(r)
    out: list[Row] = []
    for (geo, indicator, key), items in sorted(parts.items()):
        bd = json.loads(key) or None
        row = _base(geo, indicator, bd)
        complete = all(i["value"] is not None for i in items)
        files = sorted({i["file"] for i in items})
        shas = sorted({i["sha"] for i in items})
        row.update(
            {
                "value": float(sum(i["value"] for i in items)) if complete else None,
                "value_status": "normal" if complete else "not_available",
                # several sheets: the provenance is the list of files; the sha256 of the first
                "snapshot_sha256": shas[0],
                "source_locator": (
                    f"sum of {len(items)} result sheets ({len(files)} files: "
                    f"{', '.join(files[:4])}{'…' if len(files) > 4 else ''}), "
                    "polling divisions plus postal votes"
                ),
                "preferred_reason": "Sum of the Election Commission's PD and postal-vote sheets",
                "note_ids": ["aggregate"],
            }
        )
        out.append(row)
    return out


def share_rows(observations: list[Row]) -> list[Row]:
    """Turnout, rejected share and candidate shares, recomputed from counts."""
    by: dict[tuple[str, str, str], Row] = {}
    for o in observations:
        key = json.dumps(o["breakdown"] or {}, sort_keys=True)
        by[(o["geography_id"], o["indicator_id"], key)] = o
    out: list[Row] = []

    def emit(num: Row, den: Row, indicator: str) -> None:
        bd = num["breakdown"]
        row = _base(num["geography_id"], indicator, bd)
        ok = (
            num["value"] is not None
            and den["value"] is not None
            and den["value"] > 0
        )
        row.update(
            {
                "value": round(100.0 * num["value"] / den["value"], 4) if ok else None,
                "value_status": "normal" if ok else "not_available",
                "unit": "percent",
                "universe": "registered_electors" if indicator == "turnout" else "votes",
                "snapshot_sha256": num["snapshot_sha256"],
                "source_locator": f"computed: {num['claim_id']} / {den['claim_id']}",
                "preferred_reason": "Recomputed from the Election Commission's counts",
                "note_ids": [*num["note_ids"]],
            }
        )
        out.append(row)

    for (geo, indicator, key), o in sorted(by.items()):
        bd = json.loads(key)
        vt = {"vote_type": bd["vote_type"]} if "vote_type" in bd else {}
        vkey = json.dumps(vt, sort_keys=True)
        if indicator == "votes_polled" and (geo, "electors_registered", key) in by:
            emit(o, by[(geo, "electors_registered", key)], "turnout")
        elif indicator == "votes_rejected" and (geo, "votes_polled", key) in by:
            emit(o, by[(geo, "votes_polled", key)], "votes_rejected_share")
        elif indicator == "votes_candidate" and (geo, "votes_valid", vkey) in by:
            emit(o, by[(geo, "votes_valid", vkey)], "votes_candidate_share")
    return out


# --- QA --------------------------------------------------------------------------------------


def _value(observations: list[Row], geo: str, indicator: str, bd: Mapping[str, str] | None) -> float | None:
    key = json.dumps(dict(bd) if bd else {}, sort_keys=True)
    for o in observations:
        if (
            o["geography_id"] == geo
            and o["indicator_id"] == indicator
            and json.dumps(o["breakdown"] or {}, sort_keys=True) == key
        ):
            return o["value"]
    return None


def published_total_checks(ds: ElectionResults, observations: list[Row]) -> pd.DataFrame:
    """Our ED and national sums against values read from the district and all-island sheets.

    Only sheet values confirmed by their printed percentage (or the sheet's own arithmetic) are
    compared; the district sheets contain rotated text that OCR reads poorly.
    """
    index: dict[tuple[str, str, str], float | None] = {}
    for o in observations:
        if o["breakdown"] and "vote_type" in o["breakdown"]:
            continue
        bd = {k: v for k, v in (o["breakdown"] or {}).items() if k in ("party",)}
        index[(o["geography_id"], o["indicator_id"], json.dumps(bd))] = o["value"]
    rows = []
    for key, p in ds.checks.items():
        geo = "LK" if key == "LK" else ed_id(int(key))
        s = p.sheet
        for k, ind in TOTAL_INDICATORS.items():
            r = s.totals[k]
            if r.value is None:
                continue
            ours = index.get((geo, ind, json.dumps({})))
            rows.append({"geography_id": geo, "item": ind, "sheet": r.value, "ours": ours, "file": s.file})
        for _b, code, _n in CANDIDATES:
            r = s.candidates.get(code)
            if r is None or r.value is None or not (r.pct_checked or "sum" in r.how):
                continue
            ours = index.get((geo, "votes_candidate", json.dumps({"party": code})))
            rows.append({"geography_id": geo, "item": f"votes_candidate {code}", "sheet": r.value, "ours": ours, "file": s.file})
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame["difference"] = frame["ours"] - frame["sheet"]
    return frame


def nuuuwan_checks(ds: ElectionResults) -> pd.DataFrame:
    """Every value we read against nuuuwan's TSV (comparison only)."""
    if ds.nuuuwan is None:
        return pd.DataFrame()
    nu = ds.nuuuwan
    rows = []
    for p in ds.sheets:
        s = p.sheet
        if s.ed_number is None:
            continue
        eid = f"EC-{s.ed_number:02d}" + ((s.pd_letter or "?") if s.kind == "pd" else "P")
        items = [(k, s.totals[k]) for k in TOTAL_INDICATORS] + list(s.candidates.items())
        for name, r in items:
            theirs = nu.at[eid, name] if eid in nu.index and name in nu.columns else None
            rows.append(
                {
                    "file": s.file,
                    "nuuuwan_id": eid,
                    "item": name,
                    "ours": r.value,
                    "nuuuwan": None if theirs is None or pd.isna(theirs) else round(float(theirs)),
                    "how": r.how,
                }
            )
    return pd.DataFrame(rows)


def verification_sheet(ds: ElectionResults) -> pd.DataFrame:
    """Values for the lead to check: unread, withheld, derived, or differing from nuuuwan."""
    nu = nuuuwan_checks(ds)
    rows = []
    for _, r in nu.iterrows():
        reason = None
        if r["ours"] is None or pd.isna(r["ours"]):
            reason = "not read (not_available)"
        elif r["how"] == "derived":
            reason = "derived from the sheet's total and printed percentages"
        elif r["nuuuwan"] is not None and not pd.isna(r["nuuuwan"]) and r["ours"] != r["nuuuwan"]:
            reason = "differs from nuuuwan"
        if reason:
            rows.append({**r.to_dict(), "reason": reason, "lead_value": "", "lead_status": ""})
    return pd.DataFrame(rows)


def qa_markdown(ds: ElectionResults, observations: list[Row], report: QAReport) -> str:
    sheets = [p.sheet for p in ds.sheets]
    complete = [s for s in sheets if s.complete and not s.problems]
    nu = nuuuwan_checks(ds)
    read = nu[nu["ours"].notna()] if not nu.empty else nu
    both = read[read["nuuuwan"].notna()] if not read.empty else read
    agree = int((both["ours"] == both["nuuuwan"]).sum()) if not both.empty else 0
    differ = both[both["ours"] != both["nuuuwan"]] if not both.empty else both
    unread = int(nu["ours"].isna().sum()) if not nu.empty else 0
    derived = sum(len(s.derived) for s in sheets)
    checks = published_total_checks(ds, observations)
    lines = [
        f"# QA report: {DATASET_ID} (Presidential Election 2024)",
        "",
        f"- Result sheets parsed: {len(sheets)} "
        f"({sum(s.kind == 'pd' for s in sheets)} polling division, "
        f"{sum(s.kind == 'postal' for s in sheets)} postal-vote)",
        f"- Sheets complete and adding up (candidates = valid; valid + rejected = polled): "
        f"{len(complete)}",
        f"- Values on sheets: {len(nu)}; read: {len(read)}; not read or withheld: {unread}; "
        f"derived from sheet arithmetic: {derived}",
        f"- Against nuuuwan/lk_elections ({NUUUWAN_COMMIT[:7]}): {agree} agree, "
        f"{len(differ)} differ",
        f"- Observations: {report.checked}; errors {len(report.errors)}; "
        f"warnings {len(report.warnings)}",
        "",
        "## Differences from nuuuwan",
        "",
    ]
    if differ.empty:
        lines.append("None.")
    else:
        lines.append("| file | item | ours | nuuuwan | read by |")
        lines.append("|---|---|---|---|---|")
        for _, r in differ.iterrows():
            lines.append(f"| {r['file']} | {r['item']} | {int(r['ours'])} | {int(r['nuuuwan'])} | {r['how']} |")
    lines += ["", "## Sums against the Commission's district and all-island sheets", ""]
    if checks.empty:
        lines.append("No district or all-island values could be read.")
    else:
        compared = checks[checks["ours"].notna()]
        diff = compared[compared["difference"] != 0]
        lines.append(
            f"{len(compared)} values compared ({len(checks) - len(compared)} not comparable "
            f"because our sum is not_available); {len(diff)} differ."
        )
        if not diff.empty:
            lines += ["", "| place | item | sheet | ours | difference |", "|---|---|---|---|---|"]
            for _, r in diff.iterrows():
                lines.append(
                    f"| {r['geography_id']} | {r['item']} | {int(r['sheet'])} | "
                    f"{int(r['ours'])} | {int(r['difference'])} |"
                )
    lines += ["", report.to_markdown().split("\n", 2)[2]]
    return "\n".join(lines) + "\n"
