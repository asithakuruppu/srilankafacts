"""Parse Election Commission result sheets (Presidential Election 2024) from page text.

Each polling division (PD) and postal-vote sheet is two pages: a header (election, PD or "Postal
Vote Result", electoral district), a table of 38 candidates (ballot number, name, party abbreviation,
votes, percentage) and four totals (valid, rejected, polled, registered electors).

Many sheets are scans, so each value is read up to four ways:

1. ``ocr``: Vision OCR of the whole page (``page-NNN.ocr.json``);
2. ``strip``: Vision OCR of the right half of the page only (``page-NNN.strip.json``);
3. ``col``: Vision OCR of the votes column only (``page-NNN.col.json``);
4. ``text``: the PDF's own text layer, when it has one (``page-NNN.txt``).

Rows are found by party abbreviation (a fixed set of 38 codes). A candidate's votes are accepted when
a read agrees with the printed percentage (``round(100 * votes / valid, 2)``, allowing for the sheet's
rounding). The sheet must then add up: candidates sum to valid votes and valid + rejected = polled.
If exactly the votes of some candidates are still unread, and the printed percentages and the sheet
total determine them uniquely, they are filled by that arithmetic and marked ``derived``; otherwise
they stay missing. Nothing is ever taken from another source.
"""

from __future__ import annotations

import itertools
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

# Ballot order as printed on every sheet (ballot number 4 is not on the sheets).
CANDIDATES: tuple[tuple[int, str, str], ...] = (
    (1, "IND1", "AKMEEMANA DAYARATHANA THERO"),
    (2, "DUA", "ABUBAKAR MOHAMED INFAS"),
    (3, "IND2", "SIRIPALA AMARASINGHE"),
    (5, "IND4", "K.K. PIYADASA"),
    (6, "IND5", "SARATH KEERTHIRATHNA"),
    (7, "IND6", "K.A. KULARATNA"),
    (8, "APP", "K.R. KRISHAN"),
    (9, "IND7", "PALLIMULLA KAPUGAMAGE ANURA SIDNEY JAYARATHNA"),
    (10, "SLCP", "DILITH JAYAWEERA"),
    (11, "USP", "SIRITUNGA JAYASURIYA"),
    (12, "IND8", "MYLVAGANAM THILAKARAJAH"),
    (13, "DUNF", "AGAMPODI PRASANGA SURANJEEWA ANOJ DE SILVA"),
    (14, "UNFF", "LALITH DE SILVA"),
    (15, "RJA", "AJANTHA DE ZOYSA"),
    (16, "NPP", "ANURA KUMARA DISSANAYAKE"),
    (17, "SLSP", "MAHINDA DEWAGE"),
    (18, "IND9", "ARIYANETHIRAN PAKKIYASELVAM"),
    (19, "IND10", "VICTOR PERERA"),
    (20, "IND11", "ANURUDDHA POLGAMPALA"),
    (21, "SJB", "SAJITH PREMADASA"),
    (22, "IND12", "SARATH FONSEKA"),
    (23, "IND13", "DISSANAYAKA MUDIYANSELAGE BANDARANAYAKE"),
    (24, "NDF", "SARATH BANDARANAYAKE"),
    (25, "JSP", "BATHTHARAMULLE SEELARATHANA THERO"),
    (26, "SPF", "NUWAN BOPEGE"),
    (27, "NSU", "SARATH MANAMENDRA"),
    (28, "IND14", "PEMASIRI MANAGE"),
    (29, "IND15", "ANURUDDHA ROSHAN RANASINGHE"),
    (30, "ELPP", "JANAKA RATNAYAKE"),
    (31, "SBP", "NAMAL RAJAPAKSHA"),
    (32, "SLPP", "NAMAL RAJAPAKSA"),
    (33, "JPF", "WIJEYADASA RAJAPAKSHE"),
    (34, "SLLP", "A.S.P. LIYANAGE"),
    (35, "AJP", "KEERTHIE WICKRAMARATNE"),
    (36, "NSSP", "PRIYANTHA WICKRAMASINGHE"),
    (37, "IND16", "RANIL WICKREMESINGHE"),
    (38, "SEP", "PANI WIJESIRIWARDENA"),
    (39, "NIF", "OSHALA HERATH"),
)
PARTY_CODES = tuple(c[1] for c in CANDIDATES)
TOTAL_LABELS = {
    "valid": "Total Number of Valid Votes",
    "rejected": "Number of Rejected Votes",
    "polled": "Number of Votes Polled",
    "electors": "Number of Registered Electors",
}
METHODS = ("ocr", "strip", "col", "text")

_NUM_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)(?![\d.,]*\s*%)(?![\d.])")
_PCT_RE = re.compile(r"(\d{1,3}(?:\.\d{1,2})?)\s*%")


def normalise_code(token: str) -> str | None:
    """Map an OCR'd token to a party code, allowing the usual O/0 and I/1/l confusions."""
    t = token.strip().upper().replace(" ", "")
    if t in PARTY_CODES:
        return t
    m = re.fullmatch(r"(IND|lND|1ND)([0-9OIL]{1,2})", t)
    if m:
        digits = m.group(2).replace("O", "0").replace("I", "1").replace("L", "1")
        code = f"IND{int(digits)}" if digits.isdigit() else None
        return code if code in PARTY_CODES else None
    return None


@dataclass
class Box:
    text: str
    x: float
    y: float
    w: float
    h: float

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def cx(self) -> float:
        return self.x + self.w / 2


def boxes(lines: Iterable[Mapping[str, object]]) -> list[Box]:
    return [
        Box(str(d["text"]), float(d["x"]), float(d["y"]), float(d["w"]), float(d["h"]))  # type: ignore[arg-type]
        for d in lines
    ]


@dataclass
class SheetPage:
    page: int
    ocr: list[Box]
    strip: list[Box]
    text: str
    col: list[Box] = field(default_factory=list)

    def sources(self) -> tuple[tuple[str, list[Box]], ...]:
        return (("ocr", self.ocr), ("strip", self.strip), ("col", self.col))


@dataclass
class Reading:
    """All reads of one value, by method, and the accepted value."""

    reads: dict[str, list[int]] = field(default_factory=dict)
    value: int | None = None
    how: str = ""  # agreed method(s), or "derived"
    page: int | None = None
    pct: float | None = None
    pct_checked: bool = False  # the value matches the printed percentage


@dataclass
class Sheet:
    file: str
    kind: str  # pd | postal
    ed_number: int | None
    ed_name: str | None
    pd_letter: str | None
    pd_name: str | None
    candidates: dict[str, Reading]
    totals: dict[str, Reading]
    printed_turnout: float | None
    problems: list[str] = field(default_factory=list)
    derived: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return all(r.value is not None for r in [*self.candidates.values(), *self.totals.values()])


def _ints(text: str) -> list[int]:
    return [int(m.replace(",", "")) for m in _NUM_RE.findall(text)]


def _row_band(bx: Box) -> tuple[float, float]:
    pad = max(bx.h, 0.008) * 0.9
    return bx.cy - pad, bx.cy + pad


def _in_band(b: Box, band: tuple[float, float]) -> bool:
    return band[0] <= b.cy <= band[1]


def _column_x(page_boxes: Sequence[Box], label: str) -> float | None:
    for b in page_boxes:
        if label.lower() in b.text.lower():
            return b.cx
    return None


def _header(pages: Sequence[SheetPage]) -> tuple[str, int | None, str | None, str | None, str | None]:
    blob = "\n".join(b.text for b in pages[0].ocr) + "\n" + pages[0].text
    kind = "postal" if re.search(r"Postal\s*Vote", blob, re.I) else "pd"
    ed = re.search(r"Electoral\s*District\s*:?\s*\n?\s*(\d{1,2})\s*-\s*([A-Za-z][A-Za-z \-]+)", blob)
    pdm = re.search(
        r"Polling\s*Division\s*:?\s*\n?\s*([A-Z]{1,2})\s*-\s*([A-Za-z][A-Za-z .\-]+)", blob
    )
    if not ed:  # OCR often splits "Electoral District :" and "1 - Colombo" into two boxes
        m = re.search(r"^\s*(\d{1,2})\s*-\s*([A-Za-z][A-Za-z \-]+)$", blob, re.M)
        ed = m
    return (
        kind,
        int(ed.group(1)) if ed else None,
        ed.group(2).strip() if ed else None,
        pdm.group(1) if pdm else None,
        pdm.group(2).strip() if pdm else None,
    )


_NAMES = {code: name for _b, code, name in CANDIDATES}
_BALLOT = {code: ballot for ballot, code, _n in CANDIDATES}


def _squash(text: str) -> str:
    return re.sub(r"[^A-Z]", "", text.upper())


def _anchor(page: SheetPage, code: str) -> Box | None:
    """The box that marks ``code``'s row: its party code, else the candidate's printed name."""
    for b in page.ocr + page.strip:
        words = b.text.split()
        if words and (normalise_code(b.text) == code or normalise_code(words[-1]) == code):
            return b
    name = _squash(_NAMES[code])
    for b in page.ocr:
        if _squash(re.sub(r"^\s*\d+\s*", "", b.text)) == name:
            return b
    return None


def _ocr_reads(page: SheetPage, source: list[Box], code: str) -> tuple[list[int], list[float]]:
    """Integers and percentages on the row of ``code`` in one OCR read of one page."""
    a = _anchor(page, code)
    if a is None:
        return [], []
    band = _row_band(a)
    pct_x = _pct_column_x(page)
    ints: list[int] = []
    pcts: list[float] = []
    for b in source:
        if not _in_band(b, band) or b.cx < 0.6:
            continue
        for p in _PCT_RE.findall(b.text):
            pcts.append(float(p))
        # drop percentages and party codes (their digits are not votes)
        rest = " ".join(w for w in _PCT_RE.sub(" ", b.text).split() if not normalise_code(w))
        if pct_x is not None and b.cx > pct_x - 0.03 and "%" not in b.text:
            continue  # a number in the percentage column without its % sign
        ints.extend(_ints(rest))
    return ints, pcts


def _pct_column_x(page: SheetPage) -> float | None:
    """Median x-centre of boxes that are a bare percentage, i.e. the percentage column."""
    xs = sorted(b.cx for b in page.ocr if re.fullmatch(r"\s*\d{1,3}\.\d{1,2}\s*%\s*", b.text))
    return xs[len(xs) // 2] if xs else None


def _text_reads(text: str, code: str) -> tuple[list[int], list[float]]:
    """Integers and percentages between ``code`` and the next party code in the text layer."""
    if not text:
        return [], []
    tokens = re.split(r"(\s+)", text)
    words = [t for t in tokens if t.strip()]
    idx = [i for i, w in enumerate(words) if normalise_code(w) == code]
    if not idx:
        return [], []
    i = idx[0]
    j = next((k for k in range(i + 1, len(words)) if normalise_code(words[k])), len(words))
    seg = " ".join(words[i + 1 : j])
    pcts = [float(p) for p in _PCT_RE.findall(seg)]
    return _ints(_PCT_RE.sub(" ", seg)), pcts


def _total_reads(page: SheetPage, source: list[Box], label: str) -> list[int]:
    anchors = [b for b in page.ocr if label.lower() in b.text.lower()]
    if not anchors:
        return []
    band = _row_band(anchors[0])
    out: list[int] = []
    for b in source:
        if _in_band(b, band) and b.cx > anchors[0].x + anchors[0].w * 0.5:
            out.extend(_ints(_PCT_RE.sub(" ", b.text.replace(label, ""))))
    return out


def _text_total(text: str, label: str) -> list[int]:
    m = re.search(re.escape(label) + r"\s*:?\s*([\d,]+)", text)
    return [int(m.group(1).replace(",", ""))] if m else []


def _pct_ok(votes: int, valid: int, pct: float) -> bool:
    if valid <= 0:
        return False
    return abs(100.0 * votes / valid - pct) <= 0.0051


def parse_sheet(file: str, pages: Sequence[SheetPage]) -> Sheet:
    kind, ed_no, ed_name, letter, pd_name = _header(pages)
    sheet = Sheet(file, kind, ed_no, ed_name, letter, pd_name, {}, {}, None)

    # Totals first: valid is needed to check candidate reads against printed percentages.
    for key, label in TOTAL_LABELS.items():
        r = Reading()
        for page in pages:
            for method, src in page.sources():
                vals = _total_reads(page, src, label)
                if vals:
                    r.reads.setdefault(method, []).extend(vals)
                    r.page = r.page or page.page
            vals = _text_total(page.text, label)
            if vals:
                r.reads.setdefault("text", []).extend(vals)
                r.page = r.page or page.page
        sheet.totals[key] = r
    _settle_totals(sheet)
    valid = sheet.totals["valid"].value

    for _ballot, code, _name in CANDIDATES:
        r = Reading()
        pcts: list[float] = []
        for page in pages:
            for method, src in page.sources():
                ints, ps = _ocr_reads(page, src, code)
                if ints:
                    r.reads.setdefault(method, []).extend(ints)
                if ints or ps:
                    r.page = r.page or page.page
                pcts.extend(ps)
            ints, ps = _text_reads(page.text, code)
            if ints:
                r.reads.setdefault("text", []).extend(ints)
            pcts.extend(ps)
        r.pct = _mode(pcts)
        _settle_candidate(r, valid)
        sheet.candidates[code] = r

    _repair_sum(sheet)
    _derive_missing(sheet)
    _check(sheet)
    return sheet


def _mode(values: Sequence[float]) -> float | None:
    if not values:
        return None
    best = max(set(values), key=values.count)
    return best


def _support(r: Reading, value: int) -> int:
    return sum(value in r.reads.get(m, []) for m in METHODS)


def _settle_totals(sheet: Sheet) -> None:
    """Pick totals that satisfy valid + rejected = polled, preferring values most reads agree on."""
    cands = {
        k: sorted({v for vals in r.reads.values() for v in vals}, key=lambda v, r=r: -_support(r, v))
        for k, r in sheet.totals.items()
    }
    for v, rj, p in itertools.product(
        cands["valid"] or [None], cands["rejected"] or [None], cands["polled"] or [None]
    ):
        if v is not None and rj is not None and p is not None and v + rj == p:
            for key, val in (("valid", v), ("rejected", rj), ("polled", p)):
                _accept(sheet.totals[key], val)
            break
    else:
        for key in ("valid", "rejected", "polled"):
            _accept_agreed(sheet.totals[key])
    _accept_agreed(sheet.totals["electors"])


def _accept_majority(r: Reading) -> None:
    """Accept the value read by at least two methods, if no other value has as much support."""
    seen = {v for vals in r.reads.values() for v in vals}
    ranked = sorted(seen, key=lambda v: -_support(r, v))
    if ranked and _support(r, ranked[0]) >= 2 and (
        len(ranked) == 1 or _support(r, ranked[1]) < _support(r, ranked[0])
    ):
        _accept(r, ranked[0])


def _accept(r: Reading, value: int) -> None:
    r.value = value
    r.how = "+".join(m for m in METHODS if value in r.reads.get(m, []))


def _accept_agreed(r: Reading) -> None:
    """Accept a value every method agrees on, else one with a clear majority of reads."""
    seen = {v for vals in r.reads.values() for v in vals}
    if len(seen) == 1:
        _accept(r, next(iter(seen)))
    else:
        _accept_majority(r)


def _settle_candidate(r: Reading, valid: int | None) -> None:
    """Accept a read that matches the printed percentage; else a clear majority of reads.

    Values accepted by majority alone are confirmed or undone by the sum check later.
    """
    seen = sorted({v for vals in r.reads.values() for v in vals})
    if valid is not None and r.pct is not None:
        ok = [v for v in seen if _pct_ok(v, valid, r.pct)]
        if len(ok) == 1:
            _accept(r, ok[0])
            r.pct_checked = True
            return
        if len(ok) > 1:  # prefer the value most methods agree on
            ranked = sorted(ok, key=lambda v: -_support(r, v))
            if _support(r, ranked[0]) > _support(r, ranked[1]):
                _accept(r, ranked[0])
                r.pct_checked = True
            return
    _accept_majority(r)


def _repair_sum(sheet: Sheet) -> None:
    """If candidates do not add up to valid votes, try other pct-consistent reads; unique fix only."""
    valid = sheet.totals["valid"].value
    if valid is None or any(r.value is None for r in sheet.candidates.values()):
        return
    total = sum(r.value for r in sheet.candidates.values())  # type: ignore[misc]
    if total == valid:
        return
    alternatives: list[tuple[str, int]] = []
    for code, r in sheet.candidates.items():
        for v in {v for vals in r.reads.values() for v in vals}:
            if v != r.value and (r.pct is None or _pct_ok(v, valid, r.pct)):
                alternatives.append((code, v))
    fixes = [
        (code, v)
        for code, v in alternatives
        if total - sheet.candidates[code].value + v == valid  # type: ignore[operator]
    ]
    if len(fixes) == 1:
        code, v = fixes[0]
        _accept(sheet.candidates[code], v)
        sheet.candidates[code].how += " (sum check)"


def _derive_missing(sheet: Sheet, max_combinations: int = 20000) -> None:
    """Fill unread candidate votes when printed percentages and the sheet total fix them uniquely."""
    valid = sheet.totals["valid"].value
    if valid is None:
        return
    missing = [c for c, r in sheet.candidates.items() if r.value is None]
    if not missing:
        return
    known = sum(r.value for r in sheet.candidates.values() if r.value is not None)
    residual = valid - known
    options: list[list[int]] = []
    for code in missing:
        r = sheet.candidates[code]
        reads = sorted({v for vals in r.reads.values() for v in vals})
        if r.pct is not None:
            pct = r.pct
            lo = max(0, int((pct - 0.0051) * valid / 100) - 1)
            hi = int((pct + 0.0051) * valid / 100) + 1
            in_range = [v for v in range(lo, hi + 1) if _pct_ok(v, valid, pct)]
            read_ok = [v for v in reads if v in in_range]
            options.append(read_ok or in_range)
        elif reads:
            options.append(reads)
        else:
            return
    size = 1
    for o in options:
        size *= max(len(o), 1)
    if size == 0 or size > max_combinations:
        return
    solutions = [combo for combo in itertools.product(*options) if sum(combo) == residual]
    if len(solutions) == 1:
        for code, value in zip(missing, solutions[0], strict=True):
            r = sheet.candidates[code]
            if any(value in vals for vals in r.reads.values()):
                _accept(r, value)
                r.how += " (sum check)"
            else:
                r.value = value
                r.how = "derived"
                sheet.derived.append(code)


def _check(sheet: Sheet) -> None:
    t = {k: r.value for k, r in sheet.totals.items()}
    for key, r in sheet.totals.items():
        if r.value is None:
            sheet.problems.append(f"{key}: unread or inconsistent (reads {r.reads})")
    for code, r in sheet.candidates.items():
        if r.value is None:
            sheet.problems.append(f"{code}: votes unread (reads {r.reads}, printed {r.pct}%)")
    if t["valid"] is not None and t["rejected"] is not None and t["polled"] is not None:
        if t["valid"] + t["rejected"] != t["polled"]:
            sheet.problems.append("valid + rejected != polled")
    adds_up = False
    if t["valid"] is not None and all(r.value is not None for r in sheet.candidates.values()):
        total = sum(r.value for r in sheet.candidates.values())  # type: ignore[misc]
        adds_up = total == t["valid"]
        if not adds_up:
            sheet.problems.append(f"candidates sum to {total}, valid is {t['valid']}")
    if not adds_up:
        # The sheet's total cannot confirm its rows: keep only values that its printed
        # percentages confirm. (Majority reads alone were wrong in 4 of 7,604 cases.)
        for code, r in sheet.candidates.items():
            if r.value is not None and not r.pct_checked:
                sheet.problems.append(
                    f"{code}: {r.value} withheld (sheet does not add up; not confirmed by "
                    f"its printed percentage)"
                )
                r.value = None
                r.how = "withheld"
    if t["polled"] is not None and t["electors"] is not None and t["polled"] > t["electors"]:
        sheet.problems.append("polled exceeds registered electors")
    if sheet.ed_number is None:
        sheet.problems.append("electoral district not read from the header")
    if sheet.kind == "pd" and sheet.pd_letter is None:
        sheet.problems.append("polling division not read from the header")
