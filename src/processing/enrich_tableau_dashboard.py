from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_CSV = PROJECT_ROOT / "data" / "processed" / "tableau_bond_dashboard.csv"
RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"

ENRICHED_COLUMNS = ["coupon_rate", "issue_date", "credit_rating"]

RAW_INFO_COLUMNS = [
    "isinCd", "bondSrfcInrt", "bondIssuDt",
    "kisScrsItmsKcdNm", "kbpScrsItmsKcdNm", "niceScrsItmsKcdNm", "fnScrsItmsKcdNm",
]


def enrich_tableau_dashboard(dashboard: pd.DataFrame, info: pd.DataFrame) -> pd.DataFrame:
    """tableau_bond_dashboard.csv(프론트 B안이 읽는 CSV)에 표면금리·발행일·신용등급을 조인한다.

    frontend/src/lib/bond-data.ts가 couponRate/issueDate를 null로, rating을
    "국채면 무조건 AAA"로 하드코딩해온 이유가 이 컬럼들 자체가 CSV에 없었기 때문이다.
    src/analysis/calculate_after_tax_yield.py, src/analysis/classify_investment_priority.py와
    동일하게 bond_info_raw.csv에서 isin_code 기준으로 조인한다.

    - 표면금리: bondSrfcInrt
    - 발행일: bondIssuDt(YYYYMMDD) -> YYYY-MM-DD로 변환(다른 날짜 컬럼과 형식 통일)
    - 신용등급: kis > kbp > nice > fn 우선순위로 첫 값 채택(기존 "기본 데이터.csv" 생성
      로직 및 backend/app/services/diagnosis_service.py와 동일한 우선순위). 국채/지방채처럼
      등급 자체가 없는 채권은 그대로 결측으로 남긴다 - "국채니까 AAA"로 임의 추정하지 않는다
      (classify_investment_priority.py의 설계 원칙과 동일).

    이미 조인된 컬럼이 있으면(재실행) 덮어쓰도록 먼저 제거한다 - idempotent하게 반복
    실행 가능해야 파생 컬럼이 조용히 중복되는 사고를 막을 수 있다.
    """
    dashboard = dashboard.drop(columns=[c for c in ENRICHED_COLUMNS if c in dashboard.columns])

    enrichment = info.rename(columns={"isinCd": "isin_code", "bondSrfcInrt": "coupon_rate", "bondIssuDt": "issue_date"})
    enrichment["coupon_rate"] = pd.to_numeric(enrichment["coupon_rate"], errors="coerce")
    enrichment["issue_date"] = pd.to_datetime(
        enrichment["issue_date"], format="%Y%m%d", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    enrichment["credit_rating"] = (
        enrichment["kisScrsItmsKcdNm"]
        .fillna(enrichment["kbpScrsItmsKcdNm"])
        .fillna(enrichment["niceScrsItmsKcdNm"])
        .fillna(enrichment["fnScrsItmsKcdNm"])
    )
    enrichment = enrichment[["isin_code", "coupon_rate", "issue_date", "credit_rating"]].drop_duplicates("isin_code")

    return dashboard.merge(enrichment, on="isin_code", how="left")


def main() -> None:
    dashboard = pd.read_csv(DASHBOARD_CSV)
    info = pd.read_csv(RAW_BOND_INFO, dtype=str, usecols=RAW_INFO_COLUMNS)

    result = enrich_tableau_dashboard(dashboard, info)
    assert len(result) == len(dashboard), "조인 후 행 수가 원본과 달라짐"

    result.to_csv(DASHBOARD_CSV, index=False, encoding="utf-8-sig")
    print(f"[DONE] coupon_rate/issue_date/credit_rating 컬럼 추가 -> {DASHBOARD_CSV} ({len(result)}행)")
    for col in ("coupon_rate", "issue_date", "credit_rating"):
        print(f"{col} 결측: {result[col].isna().sum()}건")


if __name__ == "__main__":
    main()
