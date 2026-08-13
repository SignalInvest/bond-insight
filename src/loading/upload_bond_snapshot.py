"""yunseo/output/통합 데이터.csv(2026-08-07, 359건)를 bond_snapshot 테이블에 적재한다.

사전 조건: docs/sql/bond_snapshot.sql을 Supabase SQL Editor에서 먼저 실행해 테이블을
만들어둘 것. docs/SKILL_1035.md Step 1 참고.

CSV의 real_yield(YTM - CPI, 물가연동 실질금리) 컬럼은 이 화면에서 쓰지 않아 업로드 대상에서
제외한다 — Bond Overview의 "실질수익률(세후)"과 이름이 비슷해 헷갈리기 쉬우니 주의
(docs/SKILL_1035.md 1절 참고).
"""

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import get_supabase  # noqa: E402


CSV_PATH = PROJECT_ROOT / "yunseo/output/통합 데이터.csv"


def value_or_none(value):
    if pd.isna(value) or value == "":
        return None
    return value.item() if hasattr(value, "item") else value


def numeric(value):
    parsed = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(parsed) else float(parsed)


def integer(value):
    parsed = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(parsed) else int(parsed)


def boolean(value):
    if value is None or value == "" or (isinstance(value, float) and pd.isna(value)):
        return None
    return str(value).strip() == "True"


def build_records() -> list[dict]:
    frame = pd.read_csv(CSV_PATH, dtype=str)

    # KR381003GD86: bonds 테이블에도 없는 고아 ISIN(만기일 등 기본정보 전부 결측, YTM 45.589%인
    # 이상치) — src/loading/upload_supabase.py의 build_bond_market()가 이미 같은 이유로 제외하던
    # 행과 동일. maturity_date NOT NULL 제약과도 맞지 않아 여기서도 제외한다.
    missing_maturity = frame[frame["maturity_date"].isna() | (frame["maturity_date"] == "")]
    if not missing_maturity.empty:
        print(f"[bond_snapshot] skipped orphan ISINs (no maturity_date): {missing_maturity['isin'].tolist()}")
        frame = frame[~frame.index.isin(missing_maturity.index)]

    records = []
    for row in frame.to_dict(orient="records"):
        records.append({
            "isin_code": row["isin"],
            "reference_date": value_or_none(row["date"]),
            "bond_name": value_or_none(row["bond_name"]),
            "issuer": value_or_none(row.get("issuer")),
            "bond_type": value_or_none(row.get("bond_type")),
            "credit_rating": value_or_none(row.get("credit_rating")),
            "issue_date": value_or_none(row.get("issue_date")),
            "maturity_date": value_or_none(row.get("maturity_date")),
            "remaining_days": integer(row.get("remaining_maturity")),
            "coupon_rate": numeric(row.get("coupon_rate")),
            "close_price": numeric(row.get("close_price")),
            "ytm": numeric(row.get("ytm")),
            "volume": integer(row.get("volume")),
            "trading_value": numeric(row.get("trading_value")),
            "has_option": boolean(row.get("has_option")),
            "is_fixed_rate": boolean(row.get("is_fixed_rate")),
            "macaulay_duration": numeric(row.get("macaulay_duration")),
            "modified_duration": numeric(row.get("modified_duration")),
            "relative_yield_spread": numeric(row.get("relative_yield_spread")),
        })
    return records


def main() -> None:
    db = get_supabase()
    records = build_records()
    print(f"[bond_snapshot] {len(records)}건 업로드 시작")

    batch_size = 200
    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        db.table("bond_snapshot").upsert(batch, on_conflict="isin_code,reference_date").execute()
        print(f"[bond_snapshot] {min(start + batch_size, len(records))}/{len(records)}")

    print("[DONE]")


if __name__ == "__main__":
    main()
