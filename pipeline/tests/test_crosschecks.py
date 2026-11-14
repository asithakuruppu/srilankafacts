"""The cross-check runner fails on any difference it cannot explain, and on stale explanations."""

from __future__ import annotations

from decimal import Decimal

from slf import crosschecks
from slf.crosschecks.common import Result
from slf.crosschecks.final_report import _compare, _one_decimal


def _known_key() -> str:
    return next(iter(crosschecks.KNOWN))


def test_known_differences_pass_and_new_ones_fail():
    key = _known_key()
    others = {k: "x" for k in crosschecks.KNOWN if k != key}
    ok = Result("check", compared=10, differences={key: "known", **others})
    assert crosschecks.unexplained([ok]) == ([], [])

    new = Result("check", compared=10, differences={**ok.differences, "LK9 x": "boom"})
    found, gone = crosschecks.unexplained([new])
    assert found == ["check: boom"] and gone == []


def test_a_known_difference_that_disappears_is_reported():
    missing = {k: "x" for k in list(crosschecks.KNOWN)[1:]}
    _, gone = crosschecks.unexplained([Result("check", 10, missing)])
    assert gone == [_known_key()]


def test_known_list_covers_the_two_investigated_cases_only():
    reasons = set(crosschecks.KNOWN.values())
    assert len(crosschecks.KNOWN) == 44 and len(reasons) == 2
    assert all(k.startswith("LK") for k in crosschecks.KNOWN)


def test_compare_and_rounding():
    result = Result("c")
    _compare(result, "LK a", "label", 5, 5)
    _compare(result, "LK b", "label", 5, 6)
    assert result.compared == 2 and list(result.differences) == ["LK b"]
    # half-up, as printed reports round
    assert _one_decimal(55.35) == Decimal("55.4") and _one_decimal(55.3364) == Decimal("55.3")


def test_render_lists_new_differences():
    text = crosschecks.render([Result("c", 3, {"LK9 x": "boom"})], "v0")
    assert "| c | 3 | 1 | 0 |" in text and "- c: boom" in text
