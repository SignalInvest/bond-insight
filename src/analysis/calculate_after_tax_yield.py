from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_BOND_MARKET = PROJECT_ROOT / "data" / "raw" / "bond_market" / "bond_market_raw.csv"
RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"
OUTPUT = PROJECT_ROOT / "data" / "processed" / "bond_after_tax_yield.csv"

# 원천징수세율 15.4%(이자소득세 14% + 지방소득세 1.4%). 현재 MVP에서는 상품 종류와
# 무관한 고정값으로 취급한다. 채권 종류별(이표채/할인채/복리채) 과세 방식 차이나 세법
# 개정은 반영하지 않으므로, 반영이 필요해지면 이 상수/계산식 자체를 바꿔야 한다.
WITHHOLDING_TAX_RATE = 0.154  # 15.4%

# 세후 예상수익률을 화면에 노출할지 판정하는 안전 기준(%p)이며, "정상/비정상 채권"을
# 가르는 금융적 기준이 아니다. YTM이 이 범위를 벗어나면(관찰 사실) 표면금리가 정상이어도
# 근사식 결과를 노출하지 않는다 - 왜 YTM이 큰지(부실/디폴트 위험인지, 다른 가격 요인인지)는
# 이 모듈이 판단하지 않으며, 신용/가격 데이터로 별도 확인이 필요하다. 선형 근사식을 YTM이
# 수십~수백%인 채권에 그대로 적용하면 "세후 예상수익률 249%" 같은 숫자가 나와 초보자에게
# 일반적인 채권 수익률처럼 오인될 수 있어 이를 막기 위한 제품 안전장치다. 실제 데이터
# (2026-08-07, 358건) 기준 350건(약 97.8%)이 이 범위 안에 있었다(관찰 결과일 뿐, 이
# 임계값의 금융적 근거는 아님).
YTM_DISPLAY_MIN_PCT = -5.0
YTM_DISPLAY_MAX_PCT = 15.0

CALCULATED = "CALCULATED"
MISSING_YTM = "MISSING_YTM"
MISSING_COUPON = "MISSING_COUPON"
OUTLIER_YTM = "OUTLIER_YTM"


def classify_after_tax_yield_status(ytm_pct: float, coupon_rate_pct: float) -> str:
    """계산 가능 여부와 노출 가능 여부를 함께 판정한다. 결측이 아니라도 YTM이
    YTM_DISPLAY_MIN_PCT~YTM_DISPLAY_MAX_PCT를 벗어나면 계산 자체를 하지 않고
    OUTLIER_YTM으로 표시한다(잘못된 숫자가 화면에 남지 않도록 계산 단계에서 막는다).
    OUTLIER_YTM은 "이 채권이 부실/디폴트"라는 판정이 아니라 "선형 근사식으로 세후
    예상수익률을 안전하게 표시할 수 있는 범위를 벗어났다"는 뜻일 뿐이다."""
    if pd.isna(ytm_pct):
        return MISSING_YTM
    if pd.isna(coupon_rate_pct):
        return MISSING_COUPON
    if ytm_pct < YTM_DISPLAY_MIN_PCT or ytm_pct > YTM_DISPLAY_MAX_PCT:
        return OUTLIER_YTM
    return CALCULATED


def calculate_after_tax_yield_approx(ytm_pct: float, coupon_rate_pct: float) -> float:
    """세후 예상수익률 근사값(%p) = YTM - 표면금리 x 원천징수세율(15.4%).

    표면이자(쿠폰)에만 이자소득세가 붙고 매매차익은 비과세라는 가정 하의 선형 근사식이다.
    정확한 세후 IRR(쿠폰별 현금흐름 재계산)이 아니라 근사값이며, 가격이 액면가에 가까울수록
    근사 정확도가 높다. "실질수익률"(인플레이션 반영)이 아니라 "세후 예상수익률(근사)"이다.

    이 함수는 입력값의 결측/이상치 검사를 수행하지 않는다 - 호출 전
    classify_after_tax_yield_status()로 CALCULATED 상태인지 반드시 확인해야 한다.
    """
    return ytm_pct - coupon_rate_pct * WITHHOLDING_TAX_RATE


def build_after_tax_yield(bond_market: pd.DataFrame, info: pd.DataFrame) -> pd.DataFrame:
    """bond_market(YTM이 있는 종목만, 2026-08-07 기준 359건)에 표면금리를 조인해
    세후 예상수익률(근사값)을 계산한다.

    isinCd가 중복된 행이 입력에 있으면 그대로 중복된 채 결과에 남는다(이 함수는 시세
    중복을 제거하지 않는다 - 원본 시세 데이터가 종목당 1행이라는 전제이며, 이 전제가
    깨지면 결과 행 수가 조용히 늘어날 수 있으므로 호출 측에서 입력 무결성을 확인해야 한다).

    반환 컬럼: isinCd, ytm, coupon_rate, after_tax_yield_approx, calculation_status
    """
    coupons = info[["isinCd", "bondSrfcInrt"]].drop_duplicates("isinCd")
    merged = bond_market[["isinCd", "clprBnfRt"]].merge(coupons, on="isinCd", how="left")
    merged["ytm"] = pd.to_numeric(merged["clprBnfRt"], errors="coerce")
    merged["coupon_rate"] = pd.to_numeric(merged["bondSrfcInrt"], errors="coerce")

    merged["calculation_status"] = [
        classify_after_tax_yield_status(ytm, coupon)
        for ytm, coupon in zip(merged["ytm"], merged["coupon_rate"])
    ]
    merged["after_tax_yield_approx"] = [
        calculate_after_tax_yield_approx(ytm, coupon) if status == CALCULATED else float("nan")
        for ytm, coupon, status in zip(merged["ytm"], merged["coupon_rate"], merged["calculation_status"])
    ]

    return merged[["isinCd", "ytm", "coupon_rate", "after_tax_yield_approx", "calculation_status"]]


def main() -> None:
    bond_market = pd.read_csv(RAW_BOND_MARKET, dtype=str, usecols=["isinCd", "clprBnfRt"])
    info = pd.read_csv(RAW_BOND_INFO, dtype=str, usecols=["isinCd", "bondSrfcInrt"])
    result = build_after_tax_yield(bond_market, info)

    assert result["isinCd"].is_unique, "bond_market_raw.csv에 중복 isinCd가 있음 - 원본 데이터 확인 필요"
    assert len(result) == len(bond_market), "조인 후 행 수가 원본 시세 행 수와 달라짐"

    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"[DONE] After-tax yield (approx) CSV -> {OUTPUT} ({len(result)} rows)")
    print(result["calculation_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
