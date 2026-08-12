from typing import Any

from supabase import Client


METRIC_COLUMNS = (
    "isin_code,reference_date,remaining_days,remaining_years,maturity_status,"
    "maturity_bucket,macaulay_duration,modified_duration,duration_status,"
    "schedule_estimated,stub_period"
)
MARKET_COLUMNS = (
    "isin_code,reference_date,close_price,ytm,volume,trading_value,"
    "benchmark_treasury_rate,credit_spread"
)


def _ordered(rows: list[dict[str, Any]], isin_codes: list[str]) -> list[dict[str, Any]]:
    by_isin = {row["isin_code"]: row for row in rows}
    return [by_isin[code] for code in isin_codes if code in by_isin]


def get_analysis(
    db: Client, *, limit: int = 100, isin_codes: list[str] | None = None
) -> list[dict[str, Any]]:
    market_query = db.table("bond_market").select(MARKET_COLUMNS)
    if isin_codes:
        market_query = market_query.in_("isin_code", isin_codes)
    market_rows = market_query.limit(limit).execute().data
    codes = isin_codes or [row["isin_code"] for row in market_rows]
    if not codes:
        return []
    metric_rows = (
        db.table("bond_metrics").select(METRIC_COLUMNS).in_("isin_code", codes).execute().data
    )
    metrics = {row["isin_code"]: row for row in metric_rows}
    combined = [row | {"metrics": metrics.get(row["isin_code"])} for row in market_rows]
    return _ordered(combined, isin_codes) if isin_codes else combined


def get_risk_return(db: Client, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = get_analysis(db, limit=limit)
    result = []
    for row in rows:
        metric = row.get("metrics") or {}
        if row.get("ytm") is None or row.get("credit_spread") is None or metric.get("modified_duration") is None:
            continue
        result.append({
            "isin_code": row["isin_code"],
            "ytm": row["ytm"],
            "modified_duration": metric["modified_duration"],
            "credit_spread": row["credit_spread"],
            "remaining_years": metric.get("remaining_years"),
        })
    return result
