"""Public corrections log: `docs/corrections/log.yaml` (data-model.md, CORRECTION)."""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator

from slf.schemas import Strict

Cause = Literal[
    "extraction",
    "harmonisation",
    "geography_match",
    "unit_or_scale",
    "rounding",
    "display",
    "source_ambiguity",
    "source_error",
]
RELEASE = re.compile(r"^v\d{4}\.\d{1,2}\.\d+(-preview\.\d+)?$")


class Correction(Strict):
    id: str = Field(pattern=r"^C-\d{3}$")
    found: dt.date
    fixed: dt.date | None = None
    scope: Literal["private_preview", "public"]
    affected_releases: list[str] = Field(min_length=1)
    fixed_in: str | None = None
    geographies: list[str] = Field(default_factory=list)
    indicators: str | list[str]
    values_changed: int = Field(ge=0)
    what_was_wrong: str = Field(min_length=20)
    what_changed: str = Field(min_length=20)
    cause: Cause
    evidence: list[str] = Field(min_length=1)
    approved_by: str | None = None

    @field_validator("affected_releases")
    @classmethod
    def _releases(cls, v: list[str]) -> list[str]:
        bad = [r for r in v if not RELEASE.match(r)]
        if bad:
            raise ValueError(f"not release versions: {bad}")
        return v


class CorrectionsLog(Strict):
    entries: list[Correction]


def load(path: Path) -> CorrectionsLog:
    log = CorrectionsLog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    ids = [e.id for e in log.entries]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path}: duplicate correction ids")
    for e in log.entries:
        if e.fixed_in and not RELEASE.match(e.fixed_in):
            raise ValueError(f"{e.id}: fixed_in {e.fixed_in!r} is not a release version")
        if e.fixed and e.fixed < e.found:
            raise ValueError(f"{e.id}: fixed before found")
    return log


def unapproved(log: CorrectionsLog) -> list[str]:
    """Entries a public release must not publish yet (wording not approved by the lead)."""
    return [e.id for e in log.entries if not e.approved_by]


def payload(log: CorrectionsLog, release: str) -> dict[str, object]:
    return {
        "release": release,
        "entries": [e.model_dump(mode="json") for e in log.entries],
    }
