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
