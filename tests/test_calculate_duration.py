import pandas as pd

from src.analysis.calculate_duration import (
    FREQ_PER_YEAR,
    build_coupon_schedule,
    duration_single_cashflow,
    macaulay_modified_duration_coupon_bond,
)


def test_par_bond_textbook_case():
    """교과서 예시: 3년 만기, 표면금리 5%, 연 1회 이자지급, YTM 5%(액면가=시장가)인 채권.
    기준: 손계산 결과 Macaulay Duration 약 2.859년이어야 한다."""
    ref = pd.Timestamp("2026-01-01")
    mat = pd.Timestamp("2029-01-01")
    ncd = pd.Timestamp("2027-01-01")
    price, mac_d, mod_d, n, estimated, stub = macaulay_modified_duration_coupon_bond(
        ref, mat, ncd, coupon_rate_pct=5.0, cycle_str="12개월", ytm_pct=5.0, face=100
    )
    assert n == 3
    assert not estimated and not stub
    assert abs(price - 100) < 0.5
    assert abs(mac_d - 2.859) < 0.01
    assert mod_d < mac_d


def test_zero_coupon_duration_equals_maturity():
    """단일 현금흐름 채권(복리채/할인채)의 Duration은 항상 잔존만기와 같아야 하고,
    Modified = Macaulay / (1+YTM) 관계가 YTM 0%/양수 모두에서 성립해야 한다."""
    for ytm in (0.0, 4.0, 10.0):
        mac_d, mod_d = duration_single_cashflow(remaining_years=7.0, ytm_pct=ytm)
        assert mac_d == 7.0
        assert abs(mod_d - 7.0 / (1 + ytm / 100)) < 1e-9


def test_higher_ytm_gives_lower_modified_duration():
    """다른 조건이 같을 때 YTM이 높을수록 Modified Duration은 작아야 한다(할인 효과)."""
    ref = pd.Timestamp("2026-01-01")
    mat = pd.Timestamp("2031-01-01")
    ncd = pd.Timestamp("2026-07-01")
    _, _, mod_low, *_ = macaulay_modified_duration_coupon_bond(ref, mat, ncd, 3.0, "6개월", ytm_pct=2.0)
    _, _, mod_high, *_ = macaulay_modified_duration_coupon_bond(ref, mat, ncd, 3.0, "6개월", ytm_pct=8.0)
    assert mod_high < mod_low


def test_coupon_schedule_all_frequencies():
    """intPayCyclCtt에 나오는 5가지 주기(1/2/3/6/12개월) 모두 스케줄을 만들 수 있어야 하고,
    현금흐름 개수는 잔존기간을 주기로 나눈 값과 정확히 일치해야 한다(stub 없는 정상 케이스)."""
    ref = pd.Timestamp("2026-01-01")
    mat = pd.Timestamp("2028-01-01")  # 정확히 2년(24개월) 후 - 모든 주기와 나누어떨어짐
    ncd_by_cycle = {
        "1개월": pd.Timestamp("2026-02-01"),
        "2개월": pd.Timestamp("2026-03-01"),
        "3개월": pd.Timestamp("2026-04-01"),
        "6개월": pd.Timestamp("2026-07-01"),
        "12개월": pd.Timestamp("2027-01-01"),
    }
    for cycle, ncd in ncd_by_cycle.items():
        months = 12 // FREQ_PER_YEAR[cycle]
        dates, estimated, stub = build_coupon_schedule(ref, mat, ncd, months)
        expected_n = 24 // months
        assert len(dates) == expected_n
        assert not estimated
        assert not stub
        assert dates[-1] == mat


def test_missing_next_coupon_date_falls_back_and_flags_estimated():
    """next_coupon_date가 없으면(raw data 일부 결측/과거값) 만기에서 역산하고,
    반환되는 schedule_estimated 플래그가 True여야 한다 (신뢰도 구분용)."""
    ref = pd.Timestamp("2026-01-01")
    mat = pd.Timestamp("2028-01-01")
    dates, estimated, stub = build_coupon_schedule(ref, mat, None, months_per_period=6)
    assert estimated is True
    assert dates[-1] == mat


def test_stub_period_detected_when_cycle_does_not_align_with_maturity():
    """차기이자지급일 + 주기를 계속 더해도 만기일에 정확히 도달하지 못하면(짧은 마지막
    이자기간이 있을 수 있음) stub_period=True로 표시해야 한다."""
    ref = pd.Timestamp("2026-01-01")
    ncd = pd.Timestamp("2026-10-15")
    mat = pd.Timestamp("2027-03-31")  # ncd + 6개월(2027-04-15)과 정확히 안 맞음
    dates, estimated, stub = build_coupon_schedule(ref, mat, ncd, months_per_period=6)
    assert not estimated
    assert stub is True
    assert dates[-1] == mat
