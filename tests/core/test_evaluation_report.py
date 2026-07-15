from decimal import Decimal

from app.core.evaluation_report import EvaluationReport
from app.core.recommendation import Recommendation
from app.core.result import RuleResult
from app.core.rule_status import RuleStatus


def _passing_result(rule_id: str, score: str = "10") -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        status=RuleStatus.PASS,
        score=Decimal(score),
        message="ok",
    )


def _failing_result(rule_id: str, blocker: bool = True) -> RuleResult:
    return RuleResult(
        rule_id=rule_id,
        status=RuleStatus.FAIL,
        score=Decimal("0"),
        message="failed",
        blocker=blocker,
    )


def test_max_score_scales_with_number_of_rules():
    report = EvaluationReport(
        results=[_passing_result("A"), _passing_result("B")]
    )

    assert report.max_score == Decimal("20")


def test_recommendation_is_reject_when_any_blocker_fails():
    report = EvaluationReport(
        results=[_passing_result("A"), _failing_result("B", blocker=True)]
    )

    assert report.passed is False
    assert report.recommendation is Recommendation.REJECT


def test_recommendation_reaches_strong_buy_with_all_rules_passing():
    """
    Regression test: recommendation used to compare `score` against
    fixed absolute thresholds (90/75), but the real maximum possible
    score depends on the number of rules (10 points each) - with the
    6 real Constitution rules, max_score is 60, making the old
    fixed 90 threshold mathematically unreachable for anyone. STRONG_BUY
    should be reachable when every rule passes, regardless of how
    many rules exist.
    """
    report = EvaluationReport(
        results=[_passing_result(str(i)) for i in range(6)]
    )

    assert report.score == report.max_score
    assert report.recommendation is Recommendation.STRONG_BUY


def test_recommendation_is_buy_between_75_and_90_percent():
    # 6 rules, all PASS except one scoring 6 (WARNING-level) instead
    # of 10: 56/60 = 93.3%... use a mix that lands in the BUY band.
    report = EvaluationReport(
        results=[
            _passing_result("A", "10"),
            _passing_result("B", "10"),
            _passing_result("C", "10"),
            _passing_result("D", "10"),
            _passing_result("E", "6"),
            _passing_result("F", "0"),
        ]
    )

    # max_score is still 60 (6 rules x 10), actual score is 46 -> 76.7%
    assert report.score == Decimal("46")
    assert report.recommendation is Recommendation.BUY


def test_recommendation_is_watch_below_75_percent():
    report = EvaluationReport(
        results=[
            _passing_result("A", "10"),
            _passing_result("B", "0"),
            _passing_result("C", "0"),
            _passing_result("D", "0"),
            _passing_result("E", "0"),
            _passing_result("F", "0"),
        ]
    )

    assert report.recommendation is Recommendation.WATCH
