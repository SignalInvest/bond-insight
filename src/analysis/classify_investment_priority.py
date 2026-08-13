from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_BOND_MARKET = PROJECT_ROOT / "data" / "raw" / "bond_market" / "bond_market_raw.csv"
RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"
BOND_DURATION_SENSITIVITY = PROJECT_ROOT / "data" / "processed" / "bond_duration_sensitivity.csv"
BOND_CREDIT_SPREAD = PROJECT_ROOT / "data" / "processed" / "bond_credit_spread.csv"
BOND_AFTER_TAX_YIELD = PROJECT_ROOT / "data" / "processed" / "bond_after_tax_yield.csv"
OUTPUT = PROJECT_ROOT / "data" / "processed" / "bond_investment_priority.csv"

# 신용스프레드 구간(%p). data/processed/bond_credit_spread.csv에서 ①의 YTM 이상치
# (calculate_after_tax_yield.OUTLIER_YTM)를 제외한 350건 기준 분포로 결정했다
# (25%=0.11, 50%=0.33, 75%=1.11). 국고채보다 낮거나 같으면(<=0) 안정 신호, 뚜렷하게
# 더 얹어주면(>0.5) 수익 신호로 본다.
SPREAD_STABLE_MAX = 0.0
SPREAD_YIELD_MIN = 0.5

# 종합판정에 쓰이는 지표 최소 개수. 3개 지표(등급/스프레드/Duration) 중 1개만 있는 채권은
# 신호가 한쪽으로 쏠려도 우연일 수 있어 판정하지 않는다.
MIN_AVAILABLE_SIGNALS = 2

STABLE = "STABLE"
NEUTRAL = "NEUTRAL"
YIELD = "YIELD"

PRIORITY_STABLE = "안정성 중심"
PRIORITY_BALANCED = "균형형"
PRIORITY_YIELD = "수익률 중심"
PRIORITY_INSUFFICIENT = "INSUFFICIENT_DATA"

_SIGNAL_SCORE = {STABLE: 1, NEUTRAL: 0, YIELD: -1}

# 신용등급 문자열(AAA, AA-, A0, BBB+ ...)에서 +/-/0 보조기호를 뗀 알파벳 등급만으로 분류.
# 국채/지방채처럼 등급 자체가 없는 채권(credit_rating이 결측)은 "안정"으로 임의 추정하지
# 않고 이 지표만 결측 처리한다 - 대신 신용스프레드(국고채와의 차이가 이미 신용위험을
# 반영)와 Duration으로 판단하게 둔다.
_RATING_STABLE_GRADES = {"AAA", "AA"}
_RATING_NEUTRAL_GRADES = {"A"}


def classify_rating_signal(credit_rating: str | float) -> str | None:
    """신용등급 문자열을 STABLE/NEUTRAL/YIELD 신호로 변환한다. 결측이면 None."""
    if pd.isna(credit_rating):
        return None
    grade = str(credit_rating).rstrip("+-0")
    if grade in _RATING_STABLE_GRADES:
        return STABLE
    if grade in _RATING_NEUTRAL_GRADES:
        return NEUTRAL
    return YIELD


def classify_spread_signal(credit_spread: float) -> str | None:
    """신용스프레드(%p)를 STABLE/NEUTRAL/YIELD 신호로 변환한다. 결측이면 None."""
    if pd.isna(credit_spread):
        return None
    if credit_spread <= SPREAD_STABLE_MAX:
        return STABLE
    if credit_spread <= SPREAD_YIELD_MIN:
        return NEUTRAL
    return YIELD


def classify_duration_signal(duration_sensitivity: str | float) -> str | None:
    """②(classify_duration_sensitivity)의 등급 라벨을 STABLE/NEUTRAL/YIELD 신호로 변환."""
    if pd.isna(duration_sensitivity):
        return None
    return {"저민감": STABLE, "중간": NEUTRAL, "고민감": YIELD}.get(duration_sensitivity)


def classify_investment_priority(rating_signal, spread_signal, duration_signal) -> tuple[str, int, int]:
    """3개 신호를 합산해 투자 성향을 판정한다.

    반환: (priority, total_score, available_signal_count)
      - available_signal_count가 MIN_AVAILABLE_SIGNALS 미만이면 priority=INSUFFICIENT_DATA
      - 합산 점수 > 0: 안정성 중심 / < 0: 수익률 중심 / == 0: 균형형(신호가 상쇄됨)
    """
    # pandas Series.apply()를 거치면 함수가 반환한 None이 float('nan')으로 바뀌는 경우가
    # 있어(`s is not None`으로는 안 걸러짐) pd.notna()로 결측을 판정한다.
    signals = [s for s in (rating_signal, spread_signal, duration_signal) if pd.notna(s)]
    available = len(signals)
    if available < MIN_AVAILABLE_SIGNALS:
        return PRIORITY_INSUFFICIENT, 0, available

    total = sum(_SIGNAL_SCORE[s] for s in signals)
    if total > 0:
        return PRIORITY_STABLE, total, available
    if total < 0:
        return PRIORITY_YIELD, total, available
    return PRIORITY_BALANCED, total, available


def build_investment_priority(
    bond_market: pd.DataFrame,
    info: pd.DataFrame,
    duration_sensitivity: pd.DataFrame,
    credit_spread: pd.DataFrame,
    after_tax_yield: pd.DataFrame,
) -> pd.DataFrame:
    """bond_market(YTM이 있는 359건) 기준으로 등급/스프레드/Duration 신호를 모아 종합 판정한다.

    반환 컬럼: isinCd, credit_rating, credit_spread, duration_sensitivity,
              rating_signal, spread_signal, duration_signal,
              total_score, available_signals, investment_priority
    """
    ratings = info.assign(
        credit_rating=info["kisScrsItmsKcdNm"]
        .fillna(info["kbpScrsItmsKcdNm"])
        .fillna(info["niceScrsItmsKcdNm"])
        .fillna(info["fnScrsItmsKcdNm"])
    )[["isinCd", "credit_rating"]].drop_duplicates("isinCd")

    outlier_ytm_isins = set(
        after_tax_yield.loc[after_tax_yield["calculation_status"] == "OUTLIER_YTM", "isinCd"]
    )

    result = bond_market[["isinCd"]].drop_duplicates("isinCd").merge(ratings, on="isinCd", how="left")
    result = result.merge(
        credit_spread[["isinCd", "credit_spread", "calculation_status"]].rename(
            columns={"calculation_status": "spread_calc_status"}
        ),
        on="isinCd",
        how="left",
    )
    # YTM 이상치(①의 OUTLIER_YTM)로 계산된 신용스프레드는 왜곡된 값이라 신호에서 제외한다.
    result.loc[result["isinCd"].isin(outlier_ytm_isins), "credit_spread"] = float("nan")
    result = result.merge(
        duration_sensitivity[["isinCd", "duration_sensitivity"]], on="isinCd", how="left"
    )

    result["rating_signal"] = result["credit_rating"].apply(classify_rating_signal)
    result["spread_signal"] = result["credit_spread"].apply(classify_spread_signal)
    result["duration_signal"] = result["duration_sensitivity"].apply(classify_duration_signal)

    outcomes = [
        classify_investment_priority(r, s, d)
        for r, s, d in zip(result["rating_signal"], result["spread_signal"], result["duration_signal"])
    ]
    result["total_score"] = [o[1] for o in outcomes]
    result["available_signals"] = [o[2] for o in outcomes]
    result["investment_priority"] = [o[0] for o in outcomes]

    return result[[
        "isinCd", "credit_rating", "credit_spread", "duration_sensitivity",
        "rating_signal", "spread_signal", "duration_signal",
        "total_score", "available_signals", "investment_priority",
    ]]


def main() -> None:
    bond_market = pd.read_csv(RAW_BOND_MARKET, dtype=str, usecols=["isinCd"])
    info = pd.read_csv(
        RAW_BOND_INFO, dtype=str,
        usecols=["isinCd", "kisScrsItmsKcdNm", "kbpScrsItmsKcdNm", "niceScrsItmsKcdNm", "fnScrsItmsKcdNm"],
    )
    duration_sensitivity = pd.read_csv(BOND_DURATION_SENSITIVITY)
    credit_spread = pd.read_csv(BOND_CREDIT_SPREAD)
    after_tax_yield = pd.read_csv(BOND_AFTER_TAX_YIELD)

    result = build_investment_priority(bond_market, info, duration_sensitivity, credit_spread, after_tax_yield)
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"[DONE] Investment priority CSV -> {OUTPUT} ({len(result)} rows)")
    print(result["investment_priority"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
