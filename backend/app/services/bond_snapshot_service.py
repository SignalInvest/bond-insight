from typing import Any

from supabase import Client


SORT_FIELDS = {"bond_name", "issuer", "ytm", "close_price", "remaining_days", "coupon_rate"}


def list_bond_snapshots(
    db: Client,
    *,
    reference_date: str | None = None,
    bond_type: str | None = None,
    rating: str | None = None,
    search: str | None = None,
    sort_by: str = "bond_name",
    sort_order: str = "asc",
) -> list[dict[str, Any]]:
    query = db.table("bond_snapshot").select("*")

    if reference_date:
        query = query.eq("reference_date", reference_date)
    if bond_type:
        query = query.eq("bond_type", bond_type)
    if rating:
        query = query.eq("credit_rating", rating)
    if search:
        safe_search = search.replace(",", " ").strip()
        query = query.or_(
            f"bond_name.ilike.%{safe_search}%,issuer.ilike.%{safe_search}%,isin_code.ilike.%{safe_search}%"
        )

    response = query.order(sort_by, desc=sort_order == "desc").execute()
    return response.data
