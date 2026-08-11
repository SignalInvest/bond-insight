from pathlib import Path

import pandas as pd


# =========================================================
# 1. 프로젝트 경로
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. 잔존만기(Remaining Maturity) 상수
# =========================================================

# 채권 탐색 필터용 구간. (하한, 상한] 규칙으로 상한 값을 기준으로 매칭한다.
# 0 <= remaining_years인 정상(NORMAL) 채권에만 적용한다.
# 영구채/만기경과/결측은 bucket_remaining_years에서 상태(status) 기준으로 먼저 분리한다.
BUCKET_THRESHOLDS = [
    (1, "1년 이하"),
    (3, "1~3년"),
    (5, "3~5년"),
    (10, "5~10년"),
    (float("inf"), "10년 이상"),
]

# bondExprDt에 등장하는 영구채/신종자본증권용 sentinel 값 (실제 만기가 없다는 뜻)
PERPETUAL_SENTINEL = "99991231"
PERPETUAL_LABEL = "영구채(만기없음)"
EXPIRED_LABEL = "만기경과"

# maturity_status 값
STATUS_NORMAL = "NORMAL"
STATUS_EXPIRED = "EXPIRED"
STATUS_PERPETUAL = "PERPETUAL"
STATUS_MISSING = "MISSING"


# =========================================================
# 3. 잔존만기 계산 로직
# =========================================================

def parse_bond_dates(bas_dt: pd.Series, bond_expr_dt: pd.Series) -> pd.DataFrame:
    """basDt/bondExprDt(YYYYMMDD 문자열)를 reference_date/maturity_date로 변환.

    99991231(영구채 sentinel)은 pd.to_datetime()에 넘기기 전에 문자열 상태에서 먼저
    걸러내어 is_perpetual=True, maturity_date=NaT로 처리한다. pandas의 datetime64는
    9999-12-31을 표현할 수 있는 범위가 아니라서(OutOfBoundsDatetime) 그대로 변환을
    시도하면 안 된다.
    """
    is_perpetual = bond_expr_dt.eq(PERPETUAL_SENTINEL)

    reference_date = pd.to_datetime(bas_dt, format="%Y%m%d", errors="coerce")
    maturity_date = pd.to_datetime(
        bond_expr_dt.where(~is_perpetual),
        format="%Y%m%d",
        errors="coerce",
    )

    return pd.DataFrame(
        {
            "reference_date": reference_date,
            "maturity_date": maturity_date,
            "is_perpetual": is_perpetual,
        }
    )


def calc_remaining_maturity(reference_date: pd.Series, maturity_date: pd.Series) -> pd.DataFrame:
    """reference_date, maturity_date(둘 다 datetime64)로부터 remaining_days/years 계산.

    maturity_date가 NaT(영구채/파싱실패)이면 remaining_days/years도 NaN이 된다.
    """
    remaining_days = (maturity_date - reference_date).dt.days
    remaining_years = remaining_days / 365.25
    return pd.DataFrame(
        {"remaining_days": remaining_days, "remaining_years": remaining_years}
    )


def determine_maturity_status(remaining_days: float, is_perpetual: bool) -> str:
    """remaining_days/is_perpetual로부터 상태(NORMAL/EXPIRED/PERPETUAL/MISSING)를 판정.

    영구채/만기경과/정상 채권을 서로 다른 상품으로 취급하기 위해 bucket과 분리했다.
    """
    if is_perpetual:
        return STATUS_PERPETUAL
    if pd.isna(remaining_days):
        return STATUS_MISSING
    if remaining_days < 0:
        return STATUS_EXPIRED
    return STATUS_NORMAL


def bucket_remaining_years(years: float, status: str) -> str:
    """잔존만기(년)를 채권 탐색 필터 구간으로 분류.

    status가 NORMAL이 아니면(영구채/만기경과/결측) 구간 분류 대신 상태별 라벨을 반환한다.
    """
    if status == STATUS_PERPETUAL:
        return PERPETUAL_LABEL
    if status == STATUS_EXPIRED:
        return EXPIRED_LABEL
    if status == STATUS_MISSING or pd.isna(years):
        return "unknown"

    for upper, label in BUCKET_THRESHOLDS:
        if years <= upper:
            return label
    return BUCKET_THRESHOLDS[-1][1]


def build_derived_bond_maturity(df: pd.DataFrame) -> pd.DataFrame:
    """원본 채권 정보(isinCd, basDt, bondExprDt 컬럼 필요)로부터 Tableau용 파생 테이블 생성.

    반환 컬럼: isinCd, reference_date, maturity_date, remaining_days,
              remaining_years, maturity_status, maturity_bucket
    """
    dates = parse_bond_dates(df["basDt"], df["bondExprDt"])
    metrics = calc_remaining_maturity(dates["reference_date"], dates["maturity_date"])

    result = pd.DataFrame({"isinCd": df["isinCd"]})
    result["reference_date"] = dates["reference_date"]
    result["maturity_date"] = dates["maturity_date"]
    result["remaining_days"] = metrics["remaining_days"]
    result["remaining_years"] = metrics["remaining_years"]
    result["maturity_status"] = [
        determine_maturity_status(d, p)
        for d, p in zip(result["remaining_days"], dates["is_perpetual"])
    ]
    result["maturity_bucket"] = [
        bucket_remaining_years(y, s)
        for y, s in zip(result["remaining_years"], result["maturity_status"])
    ]
    return result


# =========================================================
# 4. 실행 (원본 채권정보 -> 파생 CSV 저장)
# =========================================================

def main():
    df = pd.read_csv(
        RAW_BOND_INFO,
        dtype=str,
        usecols=["isinCd", "basDt", "bondIssuDt", "bondExprDt"],
    )

    derived = build_derived_bond_maturity(df)

    output_path = PROCESSED_DIR / "bond_maturity.csv"
    derived.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[DONE] 잔존만기 파생 CSV 저장 완료 -> {output_path} ({len(derived)}행)")


if __name__ == "__main__":
    main()
