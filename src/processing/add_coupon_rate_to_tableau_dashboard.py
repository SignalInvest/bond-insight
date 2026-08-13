from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_CSV = PROJECT_ROOT / "data" / "processed" / "tableau_bond_dashboard.csv"
RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"

ENRICHED_COLUMNS = ["coupon_rate", "issue_date"]


def add_coupon_rate_and_issue_date(dashboard: pd.DataFrame, info: pd.DataFrame) -> pd.DataFrame:
    """tableau_bond_dashboard.csv(프론트 B안이 읽는 CSV)에 표면금리·발행일을 조인해 붙인다.

    frontend/src/lib/bond-data.ts가 지금까지 couponRate/issueDate를 null로 하드코딩해온
    이유가 이 컬럼 자체가 없었기 때문 - src/analysis/calculate_after_tax_yield.py와
    동일하게 bond_info_raw.csv의 bondSrfcInrt(표면금리)·bondIssuDt(발행일, YYYYMMDD)를
    isin_code 기준으로 조인한다. 발행일은 나머지 날짜 컬럼(maturity_date)과 형식을
    맞추기 위해 YYYY-MM-DD로 변환한다.

    이미 조인된 컬럼이 있으면(재실행) 덮어쓰도록 먼저 제거한다 - idempotent하게 반복
    실행 가능해야 파생 컬럼이 조용히 중복되는 사고를 막을 수 있다.
    """
    dashboard = dashboard.drop(columns=[c for c in ENRICHED_COLUMNS if c in dashboard.columns])

    enrichment = info.rename(
        columns={"isinCd": "isin_code", "bondSrfcInrt": "coupon_rate", "bondIssuDt": "issue_date"}
    )[["isin_code", "coupon_rate", "issue_date"]].drop_duplicates("isin_code")
    enrichment["coupon_rate"] = pd.to_numeric(enrichment["coupon_rate"], errors="coerce")
    enrichment["issue_date"] = pd.to_datetime(
        enrichment["issue_date"], format="%Y%m%d", errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    return dashboard.merge(enrichment, on="isin_code", how="left")


def main() -> None:
    dashboard = pd.read_csv(DASHBOARD_CSV)
    info = pd.read_csv(RAW_BOND_INFO, dtype=str, usecols=["isinCd", "bondSrfcInrt", "bondIssuDt"])

    result = add_coupon_rate_and_issue_date(dashboard, info)
    assert len(result) == len(dashboard), "조인 후 행 수가 원본과 달라짐"

    result.to_csv(DASHBOARD_CSV, index=False, encoding="utf-8-sig")
    print(f"[DONE] coupon_rate/issue_date 컬럼 추가 -> {DASHBOARD_CSV} ({len(result)}행)")
    print(f"coupon_rate 결측: {result['coupon_rate'].isna().sum()}건")
    print(f"issue_date 결측: {result['issue_date'].isna().sum()}건")


if __name__ == "__main__":
    main()
