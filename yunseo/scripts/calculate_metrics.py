"""표3(파생 데이터)을 만든다: 기본 데이터.csv + 시장 흐름 데이터.csv -> 파생 데이터.csv

원본 프로젝트의 data/는 읽기 전용으로만 쓰고(3y/5y/10y 국고채 금리 조회용),
결과는 yunseo/output/에 저장한다.

계산 대상 필터링 (yunseo/SKILL.md 3-1, yunseo/ARCHITECTURE.md 4):
- is_fixed_rate == True AND has_option == False 인 채권만 duration 계열 계산
- interest_payment_cycle이 비어있는 채권(할인채)은 이표 없이 만기에 원금만 상환하는 단일 현금흐름으로 처리
- real_yield / relative_yield_spread는 필터와 무관하게 전부 계산
"""

from pathlib import Path

import numpy as np
import pandas as pd

YUNSEO_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = YUNSEO_DIR.parent
OUTPUT_DIR = YUNSEO_DIR / "output"

BASIC_PATH = OUTPUT_DIR / "기본 데이터.csv"
FLOW_PATH = OUTPUT_DIR / "시장 흐름 데이터.csv"
MARKET_RATES_PATH = PROJECT_ROOT / "data" / "processed" / "market_rates_daily.csv"
OUT_PATH = OUTPUT_DIR / "파생 데이터.csv"

FACE_VALUE = 10000.0  # 국내 채권 시세는 액면 10,000원 기준으로 호가됨


def _tenor_treasury(remaining_years: float, row: pd.Series) -> float:
    """잔존만기에 가장 가까운 국고채(3y/5y/10y) 금리를 고른다 (SKILL.md 3-2)."""
    if pd.isna(remaining_years):
        return np.nan
    if remaining_years <= 4:
        return row["treasury_3y"]
    if remaining_years <= 7.5:
        return row["treasury_5y"]
    return row["treasury_10y"]


def _cash_flow_metrics(coupon_rate: float, payments_per_year: float, remaining_years: float, ytm_pct: float):
    """현금흐름표 기반 macaulay_duration/modified_duration/잔여이자합/상환원금을 계산.

    payments_per_year가 없으면(할인채) 만기에 원금만 상환하는 단일 현금흐름으로 처리.
    실제 이표 지급일(nxtmCopnDt 등) 대신 오늘~만기를 균등 분할한 근사 스케줄을 사용한다 (1차 근사).
    """
    if pd.isna(remaining_years) or remaining_years <= 0 or pd.isna(ytm_pct):
        return np.nan, np.nan, np.nan, np.nan

    y = ytm_pct / 100.0

    if pd.isna(payments_per_year) or payments_per_year <= 0:
        macaulay = remaining_years
        modified = macaulay / (1 + y)
        return macaulay, modified, 0.0, FACE_VALUE

    m = payments_per_year
    n = max(1, round(remaining_years * m))
    times = [i / m for i in range(1, n + 1)]
    times[-1] = remaining_years  # 마지막 현금흐름을 실제 만기일에 맞춤

    coupon_amt = FACE_VALUE * (coupon_rate / 100.0) / m
    cashflows = [coupon_amt] * n
    cashflows[-1] += FACE_VALUE

    pv = [cf / ((1 + y / m) ** i) for i, cf in enumerate(cashflows, start=1)]
    total_pv = sum(pv)
    if total_pv <= 0:
        return np.nan, np.nan, np.nan, np.nan

    macaulay = sum(t * p for t, p in zip(times, pv)) / total_pv
    modified = macaulay / (1 + y / m)
    total_coupons = coupon_amt * n
    return macaulay, modified, total_coupons, FACE_VALUE


def build_bond_derived() -> pd.DataFrame:
    basic = pd.read_csv(BASIC_PATH, encoding="utf-8-sig")
    flow = pd.read_csv(FLOW_PATH, encoding="utf-8-sig")
    rates = pd.read_csv(MARKET_RATES_PATH, encoding="utf-8-sig")[
        ["date", "treasury_3y", "treasury_5y", "treasury_10y"]
    ]

    df = basic.merge(flow, on="date", how="left").merge(rates, on="date", how="left")

    remaining_years = df["remaining_maturity"] / 365.0
    df["real_yield"] = df["ytm"] - df["cpi_yoy"]
    df["relative_yield_spread"] = [
        (df.loc[i, "ytm"] - _tenor_treasury(remaining_years[i], df.loc[i]))
        if not pd.isna(remaining_years[i]) else np.nan
        for i in df.index
    ]

    eligible = df["is_fixed_rate"].astype("boolean").fillna(False) & ~df["has_option"].astype("boolean").fillna(True)

    macaulay_list, modified_list, coupons_list, redemption_list = [], [], [], []
    for i in df.index:
        if eligible[i]:
            mac, mod, coupons, redemption = _cash_flow_metrics(
                df.loc[i, "coupon_rate"], df.loc[i, "payments_per_year"],
                remaining_years[i], df.loc[i, "ytm"],
            )
        else:
            mac, mod, coupons, redemption = np.nan, np.nan, np.nan, np.nan
        macaulay_list.append(mac)
        modified_list.append(mod)
        coupons_list.append(coupons)
        redemption_list.append(redemption)

    df["macaulay_duration"] = macaulay_list
    df["modified_duration"] = modified_list
    df["short_price_sensitivity"] = -df["modified_duration"] * df["short_rate_change"]
    df["long_price_sensitivity"] = -df["modified_duration"] * df["long_rate_change"]

    expected_profit = pd.Series(redemption_list, index=df.index) + pd.Series(coupons_list, index=df.index) - df["close_price"]
    df["expected_maturity_profit"] = expected_profit
    df["expected_maturity_return"] = df["expected_maturity_profit"] / df["close_price"]

    out_columns = [
        "date", "isin", "bond_name", "has_option", "is_fixed_rate",
        "macaulay_duration", "modified_duration",
        "short_price_sensitivity", "long_price_sensitivity",
        "real_yield", "relative_yield_spread",
        "expected_maturity_profit", "expected_maturity_return",
    ]
    return df[out_columns]


def main() -> None:
    derived = build_bond_derived()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    derived.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(derived)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
