from datetime import date, timedelta
from decimal import Decimal

from app.engines.metrics_engine import MetricsEngine
from tests.conftest import build_option


def test_calculate_returns_expected_metrics_shape():
    option = build_option(delta=-0.20)

    metrics = MetricsEngine.calculate(
        option=option,
        underlying_price=Decimal("280"),
    )

    # Premium = mark * multiplier = 4.1 * 100
    assert metrics.premium == Decimal("410.00")

    # Capital required = strike * multiplier = 250 * 100
    assert metrics.capital_required == Decimal("25000.00")

    # Return on capital = premium / capital_required
    assert metrics.return_on_capital == metrics.premium / metrics.capital_required

    assert metrics.break_even == option.strike - option.mark

    assert metrics.days_to_expiration >= 1


def test_days_to_expiration_is_never_less_than_one():
    option = build_option(delta=-0.20)

    # Force an expiration in the past relative to "today" to check the floor.
    from dataclasses import replace

    past_option = replace(option, expiration=date.today() - timedelta(days=5))

    metrics = MetricsEngine.calculate(
        option=past_option,
        underlying_price=Decimal("280"),
    )

    assert metrics.days_to_expiration == 1


def test_zero_underlying_price_does_not_raise():
    option = build_option(delta=-0.20)

    metrics = MetricsEngine.calculate(
        option=option,
        underlying_price=Decimal("0"),
    )

    assert metrics.downside_protection == Decimal("0")
