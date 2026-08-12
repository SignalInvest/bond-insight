import argparse
import math
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import get_supabase  # noqa: E402


def value_or_none(value):
    if pd.isna(value) or value == "":
        return None
    return value.item() if hasattr(value, "item") else value


def iso_date(value: str, *, perpetual_to_none: bool = False):
    value = str(value).strip()
    if not value or value.lower() == "nan" or (perpetual_to_none and value == "99991231"):
        return None
    parsed = pd.to_datetime(value, format="%Y%m%d", errors="coerce")
    return None if pd.isna(parsed) else parsed.date().isoformat()


def numeric(value):
    parsed = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(parsed) else float(parsed)


def integer(value):
    parsed = pd.to_numeric(value, errors="coerce")
    return None if pd.isna(parsed) else int(parsed)


def build_bonds() -> list[dict]:
    frame = pd.read_csv(PROJECT_ROOT / "data/raw/bond_info/bond_info_raw.csv", dtype=str)
    records = []
    for row in frame.to_dict(orient="records"):
        records.append({
            "isin_code": row["isinCd"],
            "bond_name": value_or_none(row.get("isinCdNm")),
            "issuer_name": value_or_none(row.get("bondIsurNm")),
            "bond_type": value_or_none(row.get("scrsItmsKcdNm")),
            "issue_date": iso_date(row.get("bondIssuDt", "")),
            "maturity_date": iso_date(row.get("bondExprDt", ""), perpetual_to_none=True),
            "coupon_rate": numeric(row.get("bondSrfcInrt")),
            "issue_amount": numeric(row.get("bondIssuAmt")),
            "outstanding_amount": numeric(row.get("bondBal")),
            "seniority": value_or_none(row.get("bondRnknDcdNm")),
            "guarantee_type": value_or_none(row.get("grnDcdNm")),
            "offering_type": value_or_none(row.get("bondOffrMcdNm")),
            "kis_rating": value_or_none(row.get("kisScrsItmsKcdNm")),
            "kbp_rating": value_or_none(row.get("kbpScrsItmsKcdNm")),
            "nice_rating": value_or_none(row.get("niceScrsItmsKcdNm")),
            "fn_rating": value_or_none(row.get("fnScrsItmsKcdNm")),
        })
    return records


def build_market_rates() -> list[dict]:
    frame = pd.read_csv(PROJECT_ROOT / "data/processed/market_rates_daily.csv")
    rename = {"date": "reference_date"}
    return [
        {key: value_or_none(value) for key, value in row.items()}
        for row in frame.rename(columns=rename).to_dict(orient="records")
    ]


def build_bond_market() -> list[dict]:
    market = pd.read_csv(PROJECT_ROOT / "yunseo/output/bond_market_clean.csv")
    valid_isins = set(
        pd.read_csv(
            PROJECT_ROOT / "data/raw/bond_info/bond_info_raw.csv",
            dtype=str,
            usecols=["isinCd"],
        )["isinCd"]
    )
    orphan_isins = sorted(set(market["isin_code"]) - valid_isins)
    if orphan_isins:
        print(f"[bond_market] skipped orphan ISINs: {orphan_isins}")
        market = market[market["isin_code"].isin(valid_isins)]
    credit = pd.read_csv(PROJECT_ROOT / "data/processed/bond_credit_spread.csv").rename(
        columns={"isinCd": "isin_code"}
    )
    frame = market.merge(
        credit[["isin_code", "benchmark_treasury_rate", "credit_spread"]],
        on="isin_code",
        how="left",
    )
    records = []
    for row in frame.to_dict(orient="records"):
        records.append({
            "isin_code": row["isin_code"],
            "reference_date": value_or_none(row["date"]),
            "close_price": value_or_none(row["close_price"]),
            "ytm": value_or_none(row["close_yield"]),
            "volume": value_or_none(row["volume"]),
            "trading_value": value_or_none(row["trading_value"]),
            "benchmark_treasury_rate": value_or_none(row["benchmark_treasury_rate"]),
            "credit_spread": value_or_none(row["credit_spread"]),
        })
    return records


def build_bond_metrics() -> list[dict]:
    maturity = pd.read_csv(PROJECT_ROOT / "data/processed/bond_maturity.csv").rename(
        columns={"isinCd": "isin_code"}
    )
    duration = pd.read_csv(PROJECT_ROOT / "data/processed/bond_duration.csv").rename(
        columns={"isinCd": "isin_code", "calculation_status": "duration_status"}
    )
    frame = maturity.merge(duration, on="isin_code", how="left")
    columns = [
        "isin_code", "reference_date", "remaining_days", "remaining_years",
        "maturity_status", "maturity_bucket", "macaulay_duration",
        "modified_duration", "duration_status", "schedule_estimated", "stub_period",
    ]
    records = []
    for row in frame[columns].to_dict(orient="records"):
        record = {key: value_or_none(value) for key, value in row.items()}
        record["remaining_days"] = integer(row["remaining_days"])
        records.append(record)
    return records


def upload(table: str, records: list[dict], conflict_column: str, batch_size: int, offset: int = 0):
    db = get_supabase()
    records = records[offset:]
    total_batches = math.ceil(len(records) / batch_size)
    for index, start in enumerate(range(0, len(records), batch_size), start=1):
        batch = records[start:start + batch_size]
        db.table(table).upsert(batch, on_conflict=conflict_column).execute()
        if index == 1 or index % 10 == 0 or index == total_batches:
            print(f"[{table}] batch {index}/{total_batches} ({min(start + batch_size, len(records))}/{len(records)})")


def insert_missing_market_rates(records: list[dict], batch_size: int):
    db = get_supabase()
    existing_dates = set()
    page_size = 1000
    for start in range(0, 100_000, page_size):
        data = (
            db.table("market_rates").select("reference_date")
            .range(start, start + page_size - 1).execute().data
        )
        existing_dates.update(row["reference_date"] for row in data)
        if len(data) < page_size:
            break
    missing = [row for row in records if row["reference_date"] not in existing_dates]
    total_batches = math.ceil(len(missing) / batch_size)
    for index, start in enumerate(range(0, len(missing), batch_size), start=1):
        batch = missing[start:start + batch_size]
        db.table("market_rates").insert(batch).execute()
        print(f"[market_rates] batch {index}/{total_batches} ({min(start + batch_size, len(missing))}/{len(missing)})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--table",
        choices=["bonds", "market_rates", "bond_market", "bond_metrics", "all"],
        default="all",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--bond-offset", type=int, default=0)
    args = parser.parse_args()

    if args.table in {"bonds", "all"}:
        upload("bonds", build_bonds(), "isin_code", args.batch_size, args.bond_offset)
    if args.table in {"market_rates", "all"}:
        insert_missing_market_rates(build_market_rates(), args.batch_size)
    if args.table in {"bond_market", "all"}:
        upload("bond_market", build_bond_market(), "isin_code,reference_date", args.batch_size)
    if args.table in {"bond_metrics", "all"}:
        upload("bond_metrics", build_bond_metrics(), "isin_code", args.batch_size)


if __name__ == "__main__":
    main()
