import pandas as pd

from src.analysis.calculate_after_tax_yield import (
    CALCULATED,
    MISSING_COUPON,
    MISSING_YTM,
    OUTLIER_YTM,
    YTM_DISPLAY_MAX_PCT,
    YTM_DISPLAY_MIN_PCT,
    build_after_tax_yield,
    calculate_after_tax_yield_approx,
    classify_after_tax_yield_status,
)


def test_calculates_after_tax_yield_approx_formula():
    assert abs(calculate_after_tax_yield_approx(3.398, 1.0) - 3.244) < 0.001


def test_classifies_normal_range_as_calculated():
    assert classify_after_tax_yield_status(3.4, 1.0) == CALCULATED
    assert classify_after_tax_yield_status(YTM_DISPLAY_MIN_PCT, 1.0) == CALCULATED
    assert classify_after_tax_yield_status(YTM_DISPLAY_MAX_PCT, 1.0) == CALCULATED


def test_classifies_out_of_range_ytm_as_outlier():
    assert classify_after_tax_yield_status(YTM_DISPLAY_MAX_PCT + 0.01, 6.7) == OUTLIER_YTM
    assert classify_after_tax_yield_status(YTM_DISPLAY_MIN_PCT - 0.01, 5.06) == OUTLIER_YTM
    assert classify_after_tax_yield_status(249.639, 6.7) == OUTLIER_YTM


def test_classifies_missing_inputs():
    assert classify_after_tax_yield_status(float("nan"), 1.0) == MISSING_YTM
    assert classify_after_tax_yield_status(3.4, float("nan")) == MISSING_COUPON


def test_builds_after_tax_yield_with_guard_applied():
    bond_market = pd.DataFrame({
        "isinCd": ["KR-normal", "KR-outlier", "KR-no-coupon"],
        "clprBnfRt": ["3.4", "249.639", "45.589"],
    })
    info = pd.DataFrame({
        "isinCd": ["KR-normal", "KR-outlier"],
        "bondSrfcInrt": ["1.0", "6.7"],
    })

    result = build_after_tax_yield(bond_market, info).set_index("isinCd")

    normal = result.loc["KR-normal"]
    assert normal["calculation_status"] == CALCULATED
    assert abs(normal["after_tax_yield_approx"] - 3.246) < 0.001

    outlier = result.loc["KR-outlier"]
    assert outlier["calculation_status"] == OUTLIER_YTM
    assert pd.isna(outlier["after_tax_yield_approx"])

    no_coupon = result.loc["KR-no-coupon"]
    assert no_coupon["calculation_status"] == MISSING_COUPON
    assert pd.isna(no_coupon["after_tax_yield_approx"])


def test_row_count_and_status_partition_invariants():
    """merge 전후로 행 수가 조용히 늘어나지 않는지, status 4종 카운트 합이 전체와
    같은지(누락 없이 매 행이 정확히 하나의 상태로 분류되는지) 검증한다."""
    bond_market = pd.DataFrame({
        "isinCd": ["KR-a", "KR-b", "KR-c", "KR-d"],
        "clprBnfRt": ["3.4", None, "5.0", "20.0"],
    })
    info = pd.DataFrame({
        "isinCd": ["KR-a", "KR-c"],
        "bondSrfcInrt": ["1.0", "2.0"],
    })

    result = build_after_tax_yield(bond_market, info)

    assert len(result) == len(bond_market)
    assert result["isinCd"].is_unique
    assert result["calculation_status"].value_counts().sum() == len(result)


def test_duplicate_isin_in_market_data_passes_through_unchanged():
    """이 모듈은 시세 데이터의 isinCd 중복을 제거하지 않는다 - 원본이 종목당 1행이라는
    전제이며, 전제가 깨지면 결과 행 수도 그대로 늘어난다는 현재 동작을 문서화한다."""
    bond_market = pd.DataFrame({
        "isinCd": ["KR-dup", "KR-dup"],
        "clprBnfRt": ["3.4", "3.5"],
    })
    info = pd.DataFrame({"isinCd": ["KR-dup"], "bondSrfcInrt": ["1.0"]})

    result = build_after_tax_yield(bond_market, info)

    assert len(result) == 2
    assert not result["isinCd"].is_unique
