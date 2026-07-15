from dataclasses import replace
from decimal import Decimal

from app.engines.metrics_engine import MetricsEngine
from app.engines.option_score_engine import OptionScoreEngine
from tests.conftest import build_option


def test_option_close_to_target_delta_scores_higher_than_far_delta():
    engine = OptionScoreEngine()

    close_option = build_option(delta=-0.20)
    far_option = replace(close_option, delta=Decimal("-0.45"))

    metrics = MetricsEngine.calculate(
        option=close_option,
        underlying_price=Decimal("280"),
    )

    close_score = engine.evaluate(option=close_option, metrics=metrics)
    far_score = engine.evaluate(option=far_option, metrics=metrics)

    assert close_score.delta > far_score.delta


def test_wider_spread_scores_lower_than_tight_spread():
    engine = OptionScoreEngine()

    tight = build_option(delta=-0.20)
    wide = replace(tight, bid=Decimal("2.0"), ask=Decimal("5.0"))

    metrics = MetricsEngine.calculate(
        option=tight,
        underlying_price=Decimal("280"),
    )

    tight_score = engine.evaluate(option=tight, metrics=metrics)
    wide_score = engine.evaluate(option=wide, metrics=metrics)

    assert tight_score.spread > wide_score.spread


def test_missing_delta_and_volume_do_not_raise():
    engine = OptionScoreEngine()

    option = build_option(delta=None)
    option = replace(option, volume=None)

    metrics = MetricsEngine.calculate(
        option=option,
        underlying_price=Decimal("280"),
    )

    score = engine.evaluate(option=option, metrics=metrics)

    assert score.delta == 0.0
    assert score.volume == 0.0


def test_score_has_no_premium_component():
    """
    Regression guard: the premium score was removed because it
    duplicated annualized_return (ROC vs ROC annualized, same
    underlying signal). ScoreResult should no longer expose it, and
    its 10-point weight was folded into annualized_return
    (35 -> 45 in constitution.yaml) rather than left unassigned.
    """
    engine = OptionScoreEngine()

    option = build_option(delta=-0.20)

    metrics = MetricsEngine.calculate(
        option=option,
        underlying_price=Decimal("280"),
    )

    score = engine.evaluate(option=option, metrics=metrics)

    assert not hasattr(score, "premium")
    assert engine.annualized_weight == 45


def test_total_score_ceiling_matches_constitution_weights():
    """
    delta(30) + spread(15) + volume(10) + annualized_return(45) = 100,
    the maximum achievable total score.
    """
    engine = OptionScoreEngine()

    assert (
        engine.delta_weight
        + engine.spread_weight
        + engine.volume_weight
        + engine.annualized_weight
    ) == 100
