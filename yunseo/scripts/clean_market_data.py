"""bond_market_raw.csv -> 정제된 채권 시세 (isin당 1행, 시세 기준일 1일치).

원본 프로젝트의 data/는 읽기 전용으로만 쓰고, 결과는 yunseo/output/에 저장한다.
컬럼명은 기존 data/processed/bond_market.csv와 동일하게 맞춰서, 그 파일을 그대로 대체할 수 있게 한다.
"""

from pathlib import Path

import pandas as pd

YUNSEO_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = YUNSEO_DIR.parent
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "bond_market" / "bond_market_raw.csv"
OUT_PATH = YUNSEO_DIR / "output" / "bond_market_clean.csv"

COLUMN_MAP = {
    "basDt": "date",
    "srtnCd": "short_code",
    "isinCd": "isin_code",
    "itmsNm": "bond_name",
    "mrktCtg": "market_type",
    "clprPrc": "close_price",
    "clprVs": "close_change",
    "clprBnfRt": "close_yield",
    "mkpPrc": "open_price",
    "mkpBnfRt": "open_yield",
    "hiprPrc": "high_price",
    "hiprBnfRt": "high_yield",
    "loprPrc": "low_price",
    "loprBnfRt": "low_yield",
    "trqu": "volume",
    "trPrc": "trading_value",
}

NUMERIC_COLUMNS = [
    "close_price", "close_change", "close_yield",
    "open_price", "open_yield", "high_price", "high_yield",
    "low_price", "low_yield", "volume", "trading_value",
]


def clean_bond_market(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    df = df[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)

    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d").dt.strftime("%Y-%m-%d")
    df["bond_name"] = df["bond_name"].str.strip()
    df["market_type"] = df["market_type"].str.strip()
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def main() -> None:
    cleaned = clean_bond_market()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(cleaned)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
