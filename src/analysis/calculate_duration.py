import sys
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

# 이 파일은 src 패키지 내부 모듈(calculate_metrics)을 import하는 첫 번째 파일이다.
# __init__.py/pyproject.toml이 없는 implicit namespace package 구조라, 이 스크립트를
# `python src/analysis/calculate_duration.py`처럼 직접 실행하면 sys.path[0]이 이 파일이
# 있는 폴더(src/analysis/)가 되어 `from src.analysis...` import가 실패한다. 아래에서
# 레포 루트를 sys.path에 직접 넣어 직접 실행/모듈 실행(-m)/pytest 어느 쪽에서도 되게 한다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.calculate_metrics import (  # noqa: E402
    PERPETUAL_SENTINEL,
    STATUS_NORMAL,
    calc_remaining_maturity,
    determine_maturity_status,
    parse_bond_dates,
)


# =========================================================
# 1. 프로젝트 경로
# =========================================================

RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"
RAW_BOND_MARKET = PROJECT_ROOT / "data" / "raw" / "bond_market" / "bond_market_raw.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. Duration 상수
# =========================================================

FACE_VALUE = 10000  # 국내 채권 시세(clprPrc)는 액면 10,000원 기준으로 고시된다는 시장 관행을 가정

# 이자지급주기(intPayCyclCtt) 문자열 -> 연간 지급 횟수
FREQ_PER_YEAR = {"1개월": 12, "2개월": 6, "3개월": 4, "6개월": 2, "12개월": 1}

# 단일 현금흐름(만기에 원리금 일시 상환)으로 간주할 수 있는 이자유형
SINGLE_CASHFLOW_TYPES = {"복리채", "할인채"}
COUPON_TYPE = "이표채"

# YTM 유효성 판정 기준. "계산 가능 여부"와 "계산값을 얼마나 신뢰할지"는 다른 질문이라 분리한다.
YTM_INVALID_FLOOR_PCT = -100  # 이하이면 (1+y)<=0이 되어 Modified Duration 공식이 수학적으로 깨짐 -> 계산 자체를 하지 않음
YTM_OUTLIER_THRESHOLD_PCT = 30  # 초과는 "부실채권"이 아니라 별도로 표시하는 고수익률 관찰치

# 채권 1건당 정확히 하나만 붙는 배제/적격 라벨. 아래 순서가 그대로 판정 우선순위다.
NO_MARKET_DATA = "NO_MARKET_DATA"
EXCLUDED_PERPETUAL = "EXCLUDED_PERPETUAL"
EXCLUDED_OPTION = "EXCLUDED_OPTION"
EXCLUDED_EQUITY_LINKED = "EXCLUDED_EQUITY_LINKED"
EXCLUDED_UNSUPPORTED_TYPE = "EXCLUDED_UNSUPPORTED_TYPE"
FAILED_MISSING_COUPON_INFO = "FAILED_MISSING_COUPON_INFO"
ELIGIBLE = "ELIGIBLE"

# 계산 단계에서 채권 1건당 정확히 하나만 붙는 계산 상태 라벨 ("계산됨"과 "신뢰도"를 분리)
FAILED_MISSING_YTM = "FAILED_MISSING_YTM"
FAILED_INVALID_YTM = "FAILED_INVALID_YTM"
FAILED_INVALID_SCHEDULE = "FAILED_INVALID_SCHEDULE"
CALCULATED = "CALCULATED"
CALCULATED_HIGH_YTM = "CALCULATED_HIGH_YTM"


# =========================================================
# 3. 계산 로직
# =========================================================

def build_coupon_schedule(reference_date, maturity_date, next_coupon_date, months_per_period):
    """reference_date 이후, maturity_date까지의 쿠폰 지급일 목록을 만든다.

    반환: (dates, schedule_estimated, stub_period)
      - schedule_estimated: next_coupon_date가 없거나 reference_date보다 과거라서
        maturity_date에서 거꾸로 역산했으면 True. raw data가 준 실제 다음 지급일을
        그대로 썼으면 False.
      - stub_period: 정기 주기를 그대로 밟아서 나온 마지막 정기 지급일이 maturity_date와
        정확히 일치하지 않아(예: 6개월 주기인데 남은 기간이 3개월뿐인 경우), 만기일을
        별도 현금흐름으로 강제 추가했으면 True. 이 경우 실제 마지막 이자기간이 짧거나 길
        수 있는데 raw data(발행조건표 없음)만으로는 실제 stub 여부/길이를 확인할 수 없다.
        이 함수는 "만기일에 원금 + 정기 쿠폰 1회분"을 지급한다고 근사할 뿐, 실제 스케줄을
        보장하지 않는다.
    """
    schedule_estimated = next_coupon_date is None or next_coupon_date < reference_date
    if not schedule_estimated:
        d = next_coupon_date
    else:
        d = maturity_date
        while d - relativedelta(months=months_per_period) > reference_date:
            d = d - relativedelta(months=months_per_period)

    dates = []
    while d < maturity_date:
        dates.append(d)
        d = d + relativedelta(months=months_per_period)
    stub_period = d != maturity_date
    dates.append(maturity_date)
    return dates, schedule_estimated, stub_period


def macaulay_modified_duration_coupon_bond(
    reference_date, maturity_date, next_coupon_date,
    coupon_rate_pct, cycle_str, ytm_pct, face=FACE_VALUE,
):
    """이표채: 쿠폰 스케줄을 만들어 각 현금흐름을 YTM으로 할인 후 Macaulay/Modified Duration 계산.

    할인 convention: 연 복리(annual compounding), Act/365 (t = 경과일수/365). 실제 종가와의
    재현 오차는 youngeun/test2_duration.py의 feasibility check([검증3])에서 확인했다.

    반환: (theoretical_price, macaulay_duration_years, modified_duration_years,
           n_cashflows, schedule_estimated, stub_period)
    """
    months_per_period = 12 // FREQ_PER_YEAR[cycle_str]
    dates, schedule_estimated, stub_period = build_coupon_schedule(
        reference_date, maturity_date, next_coupon_date, months_per_period
    )
    n = len(dates)

    coupon_per_period = face * (coupon_rate_pct / 100) / FREQ_PER_YEAR[cycle_str]
    y = ytm_pct / 100

    pv_sum = 0.0
    weighted_sum = 0.0
    for i, d in enumerate(dates):
        cash_flow = coupon_per_period + (face if i == n - 1 else 0)
        t_years = (d - reference_date).days / 365
        pv = cash_flow / (1 + y) ** t_years
        pv_sum += pv
        weighted_sum += t_years * pv

    macaulay = weighted_sum / pv_sum
    modified = macaulay / (1 + y)
    return pv_sum, macaulay, modified, n, schedule_estimated, stub_period


def duration_single_cashflow(remaining_years, ytm_pct):
    """복리채/할인채: 만기에 현금흐름이 하나뿐이므로 Macaulay Duration은 항상 잔존만기와 같다
    (현금흐름 금액이 얼마든 가중평균 시점은 그 하나의 시점 자체이기 때문 - 쿠폰 스케줄 불필요).

    반환: (macaulay_duration_years, modified_duration_years)
    """
    macaulay = remaining_years
    modified = macaulay / (1 + ytm_pct / 100)
    return macaulay, modified


def classify_ytm(ytm_pct):
    """YTM 하나의 유효성을 판정한다. "계산 가능 여부"와 "계산값을 얼마나 신뢰할지"를 분리하기
    위한 함수 - MISSING/INVALID는 계산 자체를 하지 않고, HIGH_OUTLIER는 계산은 하되 별도 표시한다."""
    if pd.isna(ytm_pct):
        return "MISSING"
    if ytm_pct <= YTM_INVALID_FLOOR_PCT:
        return "INVALID"
    if ytm_pct > YTM_OUTLIER_THRESHOLD_PCT:
        return "HIGH_OUTLIER"
    return "NORMAL"


def classify_bond_eligibility(maturity_status, optn_tcd_nm, pclr_bond_kcd_nm, bond_int_tcd_nm, cycle_str):
    """만기 있는(NORMAL) + 옵션 없음 + 주식연계 아님 + 이자유형/주기 파악됨 -> ELIGIBLE.
    그 외에는 배제 사유를 하나만 반환한다(우선순위: 영구채 > 옵션 > 주식연계 > 미지원유형 > 정보결측)."""
    if maturity_status != STATUS_NORMAL:
        return EXCLUDED_PERPETUAL
    if optn_tcd_nm != "옵션해당사항없음":
        return EXCLUDED_OPTION
    if pclr_bond_kcd_nm != "주식관련해당사항없음":
        return EXCLUDED_EQUITY_LINKED
    if bond_int_tcd_nm not in (SINGLE_CASHFLOW_TYPES | {COUPON_TYPE}):
        return EXCLUDED_UNSUPPORTED_TYPE
    if bond_int_tcd_nm == COUPON_TYPE and cycle_str not in FREQ_PER_YEAR:
        return FAILED_MISSING_COUPON_INFO
    return ELIGIBLE


# =========================================================
# 4. bond_info 전체 -> Duration 파생 테이블
# =========================================================

def build_derived_bond_duration(info: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    """bond_info 전체(LEFT)에 bond_market(YTM/가격)을 붙여 Duration을 계산한다.

    market에 없는 채권도 결과에 그대로 남고 calculation_status=NO_MARKET_DATA로 표시된다
    (bond_maturity.csv와 동일하게 "전체를 다 담고 상태로 구분"하는 방식).

    필요 컬럼:
      info: isinCd, basDt, bondExprDt, bondSrfcInrt, intPayCyclCtt, bondIntTcdNm,
            nxtmCopnDt, optnTcdNm, pclrBondKcdNm
      market: isinCd, clprPrc, clprBnfRt

    반환 컬럼: isinCd, calculation_status, macaulay_duration, modified_duration,
              schedule_estimated, stub_period
    """
    market = market.assign(ytm=pd.to_numeric(market["clprBnfRt"], errors="coerce"))
    merged = info.merge(
        market[["isinCd", "clprPrc", "ytm"]], on="isinCd", how="left", indicator=True
    )

    dates = parse_bond_dates(merged["basDt"], merged["bondExprDt"])
    rm = calc_remaining_maturity(dates["reference_date"], dates["maturity_date"])
    merged = merged.assign(
        reference_date=dates["reference_date"],
        maturity_date=dates["maturity_date"],
        remaining_years=rm["remaining_years"],
    )
    merged["maturity_status"] = [
        determine_maturity_status(d, p)
        for d, p in zip(rm["remaining_days"], dates["is_perpetual"])
    ]

    has_market = merged["_merge"] == "both"

    eligibility = pd.Series(NO_MARKET_DATA, index=merged.index, dtype="object")
    eligibility[has_market] = [
        classify_bond_eligibility(ms, opt, pclr, bt, cyc)
        for ms, opt, pclr, bt, cyc in zip(
            merged.loc[has_market, "maturity_status"], merged.loc[has_market, "optnTcdNm"],
            merged.loc[has_market, "pclrBondKcdNm"], merged.loc[has_market, "bondIntTcdNm"],
            merged.loc[has_market, "intPayCyclCtt"],
        )
    ]
    merged["eligibility"] = eligibility

    calculation_status = eligibility.copy()
    macaulay_duration = pd.Series(float("nan"), index=merged.index, dtype="float64")
    modified_duration = pd.Series(float("nan"), index=merged.index, dtype="float64")
    schedule_estimated = pd.Series(pd.NA, index=merged.index, dtype="object")
    stub_period = pd.Series(pd.NA, index=merged.index, dtype="object")

    eligible_idx = merged.index[eligibility == ELIGIBLE]
    for idx in eligible_idx:
        row = merged.loc[idx]
        ytm = row["ytm"]
        ytm_class = classify_ytm(ytm)

        if row["bondIntTcdNm"] in SINGLE_CASHFLOW_TYPES:
            if ytm_class == "MISSING":
                calculation_status[idx] = FAILED_MISSING_YTM
                continue
            if ytm_class == "INVALID":
                calculation_status[idx] = FAILED_INVALID_YTM
                continue
            mac_d, mod_d = duration_single_cashflow(row["remaining_years"], ytm)
            calculation_status[idx] = CALCULATED if ytm_class == "NORMAL" else CALCULATED_HIGH_YTM
            macaulay_duration[idx] = mac_d
            modified_duration[idx] = mod_d
            continue

        # 이표채
        coupon = pd.to_numeric(row["bondSrfcInrt"], errors="coerce")
        if pd.isna(coupon):
            calculation_status[idx] = FAILED_MISSING_COUPON_INFO
            continue
        if ytm_class == "MISSING":
            calculation_status[idx] = FAILED_MISSING_YTM
            continue
        if ytm_class == "INVALID":
            calculation_status[idx] = FAILED_INVALID_YTM
            continue

        ncd = pd.to_datetime(row["nxtmCopnDt"], format="%Y%m%d", errors="coerce")
        ncd = None if pd.isna(ncd) else ncd
        try:
            _, mac_d, mod_d, _, estimated, stub = macaulay_modified_duration_coupon_bond(
                row["reference_date"], row["maturity_date"], ncd, coupon, row["intPayCyclCtt"], ytm,
            )
        except Exception:
            calculation_status[idx] = FAILED_INVALID_SCHEDULE
            continue

        calculation_status[idx] = CALCULATED if ytm_class == "NORMAL" else CALCULATED_HIGH_YTM
        macaulay_duration[idx] = mac_d
        modified_duration[idx] = mod_d
        schedule_estimated[idx] = estimated
        stub_period[idx] = stub

    result = pd.DataFrame({
        "isinCd": merged["isinCd"],
        "calculation_status": calculation_status,
        "macaulay_duration": macaulay_duration,
        "modified_duration": modified_duration,
        "schedule_estimated": schedule_estimated,
        "stub_period": stub_period,
    })
    return result


# =========================================================
# 5. 실행 (원본 채권정보 -> 파생 CSV 저장)
# =========================================================

def main():
    info = pd.read_csv(
        RAW_BOND_INFO, dtype=str, encoding="utf-8-sig",
        usecols=["isinCd", "basDt", "bondExprDt", "bondSrfcInrt", "intPayCyclCtt",
                 "bondIntTcdNm", "nxtmCopnDt", "optnTcdNm", "pclrBondKcdNm"],
    )
    market = pd.read_csv(
        RAW_BOND_MARKET, dtype=str, encoding="utf-8-sig",
        usecols=["isinCd", "clprPrc", "clprBnfRt"],
    )

    derived = build_derived_bond_duration(info, market)

    output_path = PROCESSED_DIR / "bond_duration.csv"
    derived.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[DONE] Duration 파생 CSV 저장 완료 -> {output_path} ({len(derived)}행)")
    print(derived["calculation_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
