"""Public-release rights gate and D-030 notices (release builder)."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from slf.catalog import Catalog, CatalogReport, check_links, load_decisions
from slf.release import (
    _dataset_rights,
    _notice_markdown,
    public_release_refusals,
    release_notices,
    release_use,
)
from slf.schemas import Dataset, PublicationDecision, Rights, Source, Spatial

TODAY = dt.date(2026, 11, 12)
ATTRIBUTION = "Source: Department of Census and Statistics."
NOTICE = "No reuse terms published; will correct or remove on request."


def _catalog(status: str, publication: PublicationDecision | None) -> Catalog:
    evidence = ["memo"] if status in ("open", "permitted_with_conditions") else []
    source = Source(
        id="src",
        name="Source",
        publisher_type="government",
        rights=Rights(status=status, evidence=evidence, last_reviewed=TODAY),  # type: ignore[arg-type]
    )
    dataset = Dataset(
        id="ds",
        source="src",
        title="Dataset",
        publication=publication,
        spatial=Spatial(support="national", crs_source="not_applicable"),  # type: ignore[call-arg]
    )
    return Catalog(sources={"src": source}, datasets={"ds": dataset})


def _decision(decision: str = "D-030") -> PublicationDecision:
    return PublicationDecision(
        decision=decision,
        use="non_commercial",
        attribution=ATTRIBUTION,
        notice=NOTICE,
        takedown_days=7,
        decided=TODAY,
    )


def test_unclear_rights_without_decision_are_refused():
    refusals = public_release_refusals(_catalog("unclear", None), ["ds"], {"D-030": "Accepted"})
    assert len(refusals) == 1
    assert "rights unclear" in refusals[0]


def test_accepted_decision_allows_public_release_of_unclear_rights():
    cat = _catalog("unclear", _decision())
    assert public_release_refusals(cat, ["ds"], {"D-030": "Accepted"}) == []


def test_decision_must_be_accepted_in_the_log():
    cat = _catalog("unclear", _decision())
    proposed = public_release_refusals(cat, ["ds"], {"D-030": "Proposed"})
    missing = public_release_refusals(cat, ["ds"], {})
    no_log = public_release_refusals(cat, ["ds"], None)
    assert "Proposed" in proposed[0]
    assert "not in the decision log" in missing[0]
    assert "not in the decision log" in no_log[0]


def test_restricted_rights_are_refused_and_open_rights_pass():
    assert public_release_refusals(_catalog("restricted", None), ["ds"], {})
    assert public_release_refusals(_catalog("open", None), ["ds"], {}) == []
    assert public_release_refusals(_catalog("unclear", None), ["missing"], {})


def test_catalogue_rejects_decision_on_non_unclear_rights_and_unaccepted_decision():
    report = CatalogReport()
    check_links(_catalog("open", _decision()), report, {"D-030": "Accepted"})
    assert any("applies only while rights are unclear" in e for e in report.errors)

    report = CatalogReport()
    check_links(_catalog("unclear", _decision("D-999")), report, {"D-030": "Accepted"})
    assert any("D-999 is not in the decision log" in e for e in report.errors)

    report = CatalogReport()
    check_links(_catalog("unclear", _decision()), report, {"D-030": "Accepted"})
    assert report.errors == []
    assert not any("ds:" in n for n in report.not_publishable)


def test_payloads_carry_use_attribution_and_notice():
    datasets = [_dataset_rights(_catalog("unclear", _decision()), "ds")]
    assert datasets[0]["use"] == "non_commercial"
    assert datasets[0]["rights_status"] == "unclear"
    assert release_use(datasets) == "non_commercial"
    notices = release_notices(datasets)
    assert notices == [
        {
            "dataset_id": "ds",
            "use": "non_commercial",
            "attribution": ATTRIBUTION,
            "notice": NOTICE,
            "decision": "D-030",
        }
    ]
    text = _notice_markdown(notices)
    assert ATTRIBUTION in text and NOTICE in text and "not a licence" in text


def test_unknown_commercial_reuse_is_never_marked_any_use():
    datasets = [_dataset_rights(_catalog("unclear", None), "ds")]
    assert datasets[0]["use"] == "non_commercial"
    assert release_notices(datasets) == []


def test_decision_log_parser_reads_status(tmp_path: Path):
    log = tmp_path / "decision-log.md"
    log.write_text(
        "# Log\n\n## D-001: First\n- **Status:** Accepted · 2026-01-01\n- **Context:** x\n\n"
        "## D-002: Second\n- **Status:** Proposed · 2026-01-02\n",
        encoding="utf-8",
    )
    assert load_decisions(log) == {"D-001": "Accepted", "D-002": "Proposed"}
    assert load_decisions(tmp_path / "absent.md") is None


def test_repository_decision_log_has_d030_accepted():
    log = Path(__file__).resolve().parents[2] / "docs" / "decisions" / "decision-log.md"
    decisions = load_decisions(log)
    assert decisions is not None
    assert decisions.get("D-030") == "Accepted"
