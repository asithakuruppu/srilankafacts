"""The cross-check runner fails on any difference it cannot explain, and on stale explanations."""

from __future__ import annotations

from decimal import Decimal

from slf import crosschecks
from slf.crosschecks.common import Result
from slf.crosschecks.final_report import _compare, _one_decimal


def _results(skip: int | None = None) -> list[Result]:
    """Results that reproduce every KNOWN difference (optionally leaving one out)."""
    by_check: dict[str, dict[str, str]] = {}
    for i, (check, key) in enumerate(crosschecks.KNOWN):
        if i != skip:
            by_check.setdefault(check, {})[key] = "known"
    return [Result(check, 10, diffs) for check, diffs in by_check.items()]


def test_known_differences_pass_and_new_ones_fail():
    assert crosschecks.unexplained(_results()) == ([], [])
    results = _results()
    results[0].differences["LK9 x"] = "boom"
    found, gone = crosschecks.unexplained(results)
    assert found == [f"{results[0].check}: boom"] and gone == []


def test_a_known_difference_that_disappears_is_reported():
    check, key = next(iter(crosschecks.KNOWN))
    _, gone = crosschecks.unexplained(_results(skip=0))
    assert gone == [f"{check}: {key}"]


def test_known_keys_are_scoped_to_their_check():
    _check, key = next(iter(crosschecks.KNOWN))
    results = [*_results(), Result("Some other check", 1, {key: "same key, other check"})]
    found, _ = crosschecks.unexplained(results)
    assert found == ["Some other check: same key, other check"]


def test_known_list_covers_the_two_investigated_cases_only():
    assert len(crosschecks.KNOWN) == 44 and len(set(crosschecks.KNOWN.values())) == 2
    assert {check for check, _ in crosschecks.KNOWN} == {
        crosschecks.A5_CHECK,
        crosschecks.FR_1112_CHECK,
    }
    assert all(key.startswith("LK") for _, key in crosschecks.KNOWN)


def test_compare_and_rounding():
    result = Result("c")
    _compare(result, "LK a", "label", 5, 5)
    _compare(result, "LK b", "label", 5, 6)
    _compare(result, "LK c", "label", 5, None)  # missing in the release: reported, not a crash
    assert result.compared == 3 and list(result.differences) == ["LK b", "LK c"]
    # half-up, as printed reports round
    assert _one_decimal(55.35) == Decimal("55.4") and _one_decimal(55.3364) == Decimal("55.3")


def test_render_lists_new_differences():
    text = crosschecks.render([Result("c", 3, {"LK9 x": "boom"})], "v0")
    assert "| c | 3 | 1 | 0 |" in text and "- c: boom" in text
