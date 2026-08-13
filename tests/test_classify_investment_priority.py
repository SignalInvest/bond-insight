import pandas as pd

from src.analysis.classify_investment_priority import (
    NEUTRAL,
    PRIORITY_BALANCED,
    PRIORITY_INSUFFICIENT,
    PRIORITY_STABLE,
    PRIORITY_YIELD,
    STABLE,
    YIELD,
    build_investment_priority,
    classify_duration_signal,
    classify_investment_priority,
    classify_rating_signal,
    classify_spread_signal,
)


def test_classify_rating_signal_strips_modifiers():
    assert classify_rating_signal("AAA") == STABLE
    assert classify_rating_signal("AA-") == STABLE
    assert classify_rating_signal("AA0") == STABLE
    assert classify_rating_signal("A+") == NEUTRAL
    assert classify_rating_signal("A0") == NEUTRAL
    assert classify_rating_signal("BBB+") == YIELD
    assert classify_rating_signal("BB-") == YIELD
    assert classify_rating_signal(float("nan")) is None


def test_classify_spread_signal_thresholds():
    assert classify_spread_signal(-0.5) == STABLE
    assert classify_spread_signal(0.0) == STABLE
    assert classify_spread_signal(0.3) == NEUTRAL
    assert classify_spread_signal(0.5) == NEUTRAL
    assert classify_spread_signal(0.51) == YIELD
    assert classify_spread_signal(float("nan")) is None


def test_classify_duration_signal_maps_tier_labels():
    assert classify_duration_signal("저민감") == STABLE
    assert classify_duration_signal("중간") == NEUTRAL
    assert classify_duration_signal("고민감") == YIELD
    assert classify_duration_signal(float("nan")) is None


def test_requires_minimum_two_signals():
    priority, score, available = classify_investment_priority(STABLE, None, None)
    assert priority == PRIORITY_INSUFFICIENT
    assert available == 1


def test_majority_signals_decide_priority():
    assert classify_investment_priority(STABLE, STABLE, NEUTRAL)[0] == PRIORITY_STABLE
    assert classify_investment_priority(YIELD, YIELD, NEUTRAL)[0] == PRIORITY_YIELD
    assert classify_investment_priority(STABLE, YIELD, None)[0] == PRIORITY_BALANCED


def test_build_investment_priority_excludes_outlier_ytm_spread():
    bond_market = pd.DataFrame({"isinCd": ["KR-stable", "KR-outlier-ytm"]})
    info = pd.DataFrame({
        "isinCd": ["KR-stable", "KR-outlier-ytm"],
        "kisScrsItmsKcdNm": ["AAA", "BBB+"],
        "kbpScrsItmsKcdNm": [None, None],
        "niceScrsItmsKcdNm": [None, None],
        "fnScrsItmsKcdNm": [None, None],
    })
    duration_sensitivity = pd.DataFrame({
        "isinCd": ["KR-stable", "KR-outlier-ytm"],
        "duration_sensitivity": ["저민감", "저민감"],
    })
    credit_spread = pd.DataFrame({
        "isinCd": ["KR-stable", "KR-outlier-ytm"],
        "credit_spread": [-0.1, 245.9],
        "calculation_status": ["CALCULATED", "CALCULATED"],
    })
    after_tax_yield = pd.DataFrame({
        "isinCd": ["KR-stable", "KR-outlier-ytm"],
        "calculation_status": ["CALCULATED", "OUTLIER_YTM"],
    })

    result = build_investment_priority(
        bond_market, info, duration_sensitivity, credit_spread, after_tax_yield
    ).set_index("isinCd")

    stable = result.loc["KR-stable"]
    assert stable["spread_signal"] == STABLE
    assert stable["investment_priority"] == PRIORITY_STABLE

    outlier = result.loc["KR-outlier-ytm"]
    assert pd.isna(outlier["credit_spread"])
    # pandas Series.apply()를 거치면 None이 float('nan')으로 바뀌는 경우가 있어 pd.isna()로 확인
    assert pd.isna(outlier["spread_signal"])
    # 등급(BBB+=YIELD) + Duration(저민감=STABLE) 2개 신호만 남아 합산 0 -> 균형형
    assert outlier["investment_priority"] == PRIORITY_BALANCED
