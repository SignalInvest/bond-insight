from datetime import date
from typing import Any

from supabase import Client


def get_market_rates(
    db: Client,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = db.table("market_rates").select("*")
    if start_date:
        query = query.gte("reference_date", start_date.isoformat())
    if end_date:
        query = query.lte("reference_date", end_date.isoformat())
    response = query.order("reference_date", desc=True).limit(limit).execute()
    return response.data
