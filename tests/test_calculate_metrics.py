import pandas as pd

from src.analysis.calculate_metrics import (
    EXPIRED_LABEL,
    PERPETUAL_LABEL,
    PERPETUAL_SENTINEL,
    STATUS_EXPIRED,
    STATUS_NORMAL,
    STATUS_PERPETUAL,
    bucket_remaining_years,
    calc_remaining_maturity,
    determine_maturity_status,
    parse_bond_dates,
)


def test_basic_calculation():
    ref = pd.Series(pd.to_datetime(["2026-01-01"]))
    mat = pd.Series(pd.to_datetime(["2029-01-01"]))
    result = calc_remaining_maturity(ref, mat)

    expected_days = (pd.Timestamp("2029-01-01") - pd.Timestamp("2026-01-01")).days  # 1096
    assert result["remaining_days"].iloc[0] == expected_days
    assert abs(result["remaining_years"].iloc[0] - expected_days / 365.25) < 1e-9


def test_zero_remaining_is_normal_and_under_one_year():
    ref = pd.Series(pd.to_datetime(["2026-08-10"]))
    mat = pd.Series(pd.to_datetime(["2026-08-10"]))
    result = calc_remaining_maturity(ref, mat)

    status = determine_maturity_status(result["remaining_days"].iloc[0], is_perpetual=False)
    assert status == STATUS_NORMAL
    assert bucket_remaining_years(result["remaining_years"].iloc[0], status) == "1년 이하"


def test_bucket_boundaries_stay_normal_beyond_100_years():
    cases = {
        0.5: "1년 이하",
        1.0: "1년 이하",
        1.01: "1~3년",
        3.0: "1~3년",
        3.01: "3~5년",
        5.0: "3~5년",
        5.01: "5~10년",
        10.0: "5~10년",
        10.01: "10년 이상",
        25.0: "10년 이상",
        101.0: "10년 이상",  # 100년을 넘어도 정상 채권이면 영구채가 아니라 '10년 이상'
    }
    for years, expected in cases.items():
        assert bucket_remaining_years(years, STATUS_NORMAL) == expected


def test_negative_remaining_is_expired_not_under_one_year():
    """음수 잔존만기가 '1년 이하'로 새지 않고 EXPIRED/'만기경과'로 분리되는지 확인"""
    ref = pd.Series(pd.to_datetime(["2026-08-10"]))
    mat = pd.Series(pd.to_datetime(["2025-08-10"]))
    result = calc_remaining_maturity(ref, mat)

    remaining_days = result["remaining_days"].iloc[0]
    status = determine_maturity_status(remaining_days, is_perpetual=False)
    assert status == STATUS_EXPIRED

    bucket = bucket_remaining_years(result["remaining_years"].iloc[0], status)
    assert bucket == EXPIRED_LABEL
    assert bucket != "1년 이하"


def test_perpetual_sentinel_detected_before_datetime_conversion():
    """만기일이 99991231(영구채 sentinel)이면 datetime 변환 전에 먼저 걸러져서
    '10년 이상'이 아니라 PERPETUAL 상태/별도 라벨로 분류되는지 확인"""
    bas_dt = pd.Series(["20260810"])
    bond_expr_dt = pd.Series([PERPETUAL_SENTINEL])

    dates = parse_bond_dates(bas_dt, bond_expr_dt)
    assert dates["is_perpetual"].iloc[0]
    assert pd.isna(dates["maturity_date"].iloc[0])

    metrics = calc_remaining_maturity(dates["reference_date"], dates["maturity_date"])
    status = determine_maturity_status(metrics["remaining_days"].iloc[0], is_perpetual=True)
    assert status == STATUS_PERPETUAL
    assert bucket_remaining_years(metrics["remaining_years"].iloc[0], status) == PERPETUAL_LABEL
