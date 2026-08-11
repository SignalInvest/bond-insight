"""표1(기본 데이터), 표2(시장 흐름 데이터)를 만든다.

원본 프로젝트의 data/는 읽기 전용으로만 쓰고, 결과는 yunseo/output/에 저장한다.
표1은 yunseo/output/bond_info_clean.csv(clean_bond_data.py 결과) + data/processed/bond_market.csv를 isin으로 조인.
표2는 data/processed/market_rates_daily.csv + cpi_monthly.csv를 date로 조인.

확정된 값 (yunseo/SKILL.md "결정된 값" 참고):
- N = 20영업일 (short_rate_change/long_rate_change)
"""

from pathlib import Path

import pandas as pd

YUNSEO_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = YUNSEO_DIR.parent
OUTPUT_DIR = YUNSEO_DIR / "output"

BOND_INFO_CLEAN_PATH = OUTPUT_DIR / "bond_info_clean.csv"
BOND_MARKET_PATH = PROJECT_ROOT / "data" / "processed" / "bond_market.csv"
MARKET_RATES_PATH = PROJECT_ROOT / "data" / "processed" / "market_rates_daily.csv"
CPI_PATH = PROJECT_ROOT / "data" / "processed" / "cpi_monthly.csv"

BASIC_OUT_PATH = OUTPUT_DIR / "기본 데이터.csv"
FLOW_OUT_PATH = OUTPUT_DIR / "시장 흐름 데이터.csv"

N_DAYS = 20  # 확정된 값: 20영업일

BASIC_SPEC_COLUMNS = [
    "date", "isin", "bond_name", "issuer", "bond_type", "credit_rating",
    "issue_date", "maturity_date", "remaining_maturity", "coupon_rate",
    "interest_payment_cycle", "close_price", "ytm", "volume", "trading_value",
]
BASIC_EXTRA_COLUMNS = ["payments_per_year", "has_option", "is_fixed_rate"]

FLOW_COLUMNS = [
    "date", "base_rate", "cpi_yoy", "yield_spread_10y_3y",
    "credit_spread", "policy_spread", "short_rate_change", "long_rate_change",
]


def build_market_flow() -> pd.DataFrame:
    rates = pd.read_csv(MARKET_RATES_PATH, encoding="utf-8-sig")
    rates["date"] = pd.to_datetime(rates["date"])
    rates = rates.sort_values("date").reset_index(drop=True)

    cpi = pd.read_csv(CPI_PATH, encoding="utf-8-sig")
    cpi["date"] = pd.to_datetime(cpi["date"])
    cpi = cpi.sort_values("date").reset_index(drop=True)
    # 전년동월 대비 상승률: 월별 데이터가 연속이라 12행 전 = 12개월 전으로 계산
    cpi["cpi_yoy"] = cpi["cpi"].pct_change(12) * 100

    # 월별 cpi_yoy를 일별 시세에 forward-fill (그 달 발표된 값을 해당 월부터 다음 값이 나오기 전까지 적용)
    merged = pd.merge_asof(rates, cpi[["date", "cpi_yoy"]], on="date", direction="backward")

    merged = merged.rename(columns={"yield_spread": "yield_spread_10y_3y"})
    merged["short_rate_change"] = merged["treasury_3y"] - merged["treasury_3y"].shift(N_DAYS)
    merged["long_rate_change"] = merged["treasury_10y"] - merged["treasury_10y"].shift(N_DAYS)

    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    return merged[FLOW_COLUMNS]


def build_bond_basic() -> pd.DataFrame:
    info = pd.read_csv(BOND_INFO_CLEAN_PATH, encoding="utf-8-sig")
    market = pd.read_csv(BOND_MARKET_PATH, encoding="utf-8-sig")

    merged = market.merge(info, left_on="isin_code", right_on="isin", how="left")

    unmatched = merged[merged["isin"].isna()]
    if len(unmatched):
        codes = ", ".join(unmatched["isin_code"].tolist())
        print(f"[경고] bond_info_clean과 매칭되지 않은 isin {len(unmatched)}건: {codes}")

    merged["isin"] = merged["isin"].fillna(merged["isin_code"])
    # bond_name은 market 쪽 컬럼이 그대로 남아있음 (info에는 동명 컬럼이 없어 충돌 없음, SKILL.md 1-1)
    merged["ytm"] = merged["close_yield"]

    maturity_dt = pd.to_datetime(merged["maturity_date"], errors="coerce")
    date_dt = pd.to_datetime(merged["date"], errors="coerce")
    merged["remaining_maturity"] = (maturity_dt - date_dt).dt.days

    for col in BASIC_EXTRA_COLUMNS:
        if col == "has_option":
            merged[col] = merged[col].astype("boolean")
        elif col == "is_fixed_rate":
            merged[col] = merged[col].astype("boolean")

    out = merged[BASIC_SPEC_COLUMNS + BASIC_EXTRA_COLUMNS]
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    flow = build_market_flow()
    flow.to_csv(FLOW_OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(flow)} rows -> {FLOW_OUT_PATH}")

    basic = build_bond_basic()
    basic.to_csv(BASIC_OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(basic)} rows -> {BASIC_OUT_PATH}")


if __name__ == "__main__":
    main()
