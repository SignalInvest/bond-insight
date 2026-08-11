"""bond_info_raw.csv -> 정제된 채권 발행정보 (isin당 1행).

원본 프로젝트의 data/, src/는 읽기 전용으로만 쓰고, 결과는 yunseo/output/에 저장한다.

확정된 규칙 (yunseo/SKILL.md, yunseo/AGENT.md 참고):
- bond_type: scrsItmsKcdNm 10종 -> 6종(국채/지방채/특수채/금융채/회사채/유동화증권) 매핑
- credit_rating: KIS -> FN -> KBP -> NICE 순서로 첫 값 채택
- interest_payment_cycle 문자열 -> 연간 지급횟수(payments_per_year) 파싱
- has_option: optnTcd가 '0000'(옵션해당사항없음)이 아니면 True
- is_fixed_rate: irtChngDcdNm에 "변동"이 포함되지 않으면 True
"""

from pathlib import Path

import pandas as pd

YUNSEO_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = YUNSEO_DIR.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"
OUT_PATH = YUNSEO_DIR / "output" / "bond_info_clean.csv"

BOND_TYPE_MAP = {
    "국채": "국채",
    "지방채": "지방채",
    "지방공사채": "지방채",
    "특수채": "특수채",
    "금융채": "금융채",
    "일반회사채": "회사채",
    "유동화SPC채": "유동화증권",
    "MBS": "유동화증권",
    "SLBS": "유동화증권",
    "유사집합투자기구채": "유동화증권",
}

RATING_PRIORITY = [
    "kisScrsItmsKcdNm",
    "fnScrsItmsKcdNm",
    "kbpScrsItmsKcdNm",
    "niceScrsItmsKcdNm",
]

CYCLE_TO_PAYMENTS_PER_YEAR = {
    "1개월": 12,
    "2개월": 6,
    "3개월": 4,
    "6개월": 2,
    "12개월": 1,
}


def _parse_yyyymmdd(series: pd.Series) -> pd.Series:
    """YYYYMMDD 문자열 -> 'YYYY-MM-DD' 문자열. pandas 표현 범위(~2262년)를 넘는 날짜(예: 99991231, 무기한채)는 그대로 8자리를 나눠서 남긴다."""
    s = series.astype(str).str.strip()
    parsed = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
    formatted = parsed.dt.strftime("%Y-%m-%d")
    out_of_range = parsed.isna() & s.str.match(r"^\d{8}$")
    formatted = formatted.where(~out_of_range, s.str[:4] + "-" + s.str[4:6] + "-" + s.str[6:8])
    return formatted


def _first_rating(row: pd.Series) -> str:
    for col in RATING_PRIORITY:
        value = row[col]
        if isinstance(value, str) and value.strip():
            return value.strip()
    return pd.NA


def clean_bond_info(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str).fillna("")

    out = pd.DataFrame()
    out["isin"] = df["isinCd"].str.strip()
    out["issuer"] = df["bondIsurNm"].str.strip()
    out["bond_type"] = df["scrsItmsKcdNm"].str.strip().map(BOND_TYPE_MAP)
    out["credit_rating"] = df.apply(_first_rating, axis=1)
    out["issue_date"] = _parse_yyyymmdd(df["bondIssuDt"])
    out["maturity_date"] = _parse_yyyymmdd(df["bondExprDt"])
    out["coupon_rate"] = pd.to_numeric(df["bondSrfcInrt"], errors="coerce")
    out["interest_payment_cycle"] = df["intPayCyclCtt"].str.strip()
    out["payments_per_year"] = out["interest_payment_cycle"].map(CYCLE_TO_PAYMENTS_PER_YEAR)
    out["has_option"] = df["optnTcd"].str.strip().replace("", "0000") != "0000"
    out["is_fixed_rate"] = ~df["irtChngDcdNm"].str.contains("변동", na=False)

    unmapped = out["bond_type"].isna().sum()
    if unmapped:
        missing_types = sorted(set(df.loc[out["bond_type"].isna(), "scrsItmsKcdNm"]))
        raise ValueError(f"bond_type 매핑에 없는 원본 종류 {unmapped}건: {missing_types}")

    return out


def main() -> None:
    cleaned = clean_bond_info()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(cleaned)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
