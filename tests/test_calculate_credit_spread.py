import pandas as pd

from src.analysis.calculate_credit_spread import CALCULATED, build_credit_spread, interpolate_treasury_rate


def test_interpolates_treasury_curve():
    assert interpolate_treasury_rate(2, 3.0, 3.5, 4.0) == 3.0
    assert interpolate_treasury_rate(4, 3.0, 3.5, 4.0) == 3.25
    assert interpolate_treasury_rate(7.5, 3.0, 3.5, 4.0) == 3.75
    assert interpolate_treasury_rate(15, 3.0, 3.5, 4.0) == 4.0


def test_builds_individual_credit_spread():
    info = pd.DataFrame({"isinCd": ["KR1"], "bondExprDt": ["20300807"]})
    market = pd.DataFrame({"isinCd": ["KR1"], "basDt": ["20260807"], "clprBnfRt": ["4.25"]})
    rates = pd.DataFrame({
        "date": ["2026-08-07"], "treasury_3y": [3.0],
        "treasury_5y": [3.5], "treasury_10y": [4.0],
    })

    result = build_credit_spread(info, market, rates).iloc[0]

    assert abs(result["benchmark_treasury_rate"] - 3.25) < 0.001
    assert abs(result["credit_spread"] - 1.0) < 0.001
    assert result["calculation_status"] == CALCULATED
