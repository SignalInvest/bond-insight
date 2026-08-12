from typing import Any

from supabase import Client


SORT_FIELDS = {
    "bond_name", "issuer_name", "coupon_rate", "issue_date", "maturity_date", "created_at"
}


def list_bonds(
    db: Client,
    *,
    page: int,
    page_size: int,
    search: str | None = None,
    issuer: str | None = None,
    bond_type: str | None = None,
    rating: str | None = None,
    min_coupon: float | None = None,
    max_coupon: float | None = None,
    maturity_from: str | None = None,
    maturity_to: str | None = None,
    sort_by: str = "bond_name",
    sort_order: str = "asc",
) -> dict[str, Any]:
    query = db.table("bonds").select("*", count="exact")

    if search:
        safe_search = search.replace(",", " ").strip()
        query = query.or_(
            f"bond_name.ilike.%{safe_search}%,issuer_name.ilike.%{safe_search}%,isin_code.ilike.%{safe_search}%"
        )
    if issuer:
        query = query.eq("issuer_name", issuer)
    if bond_type:
        query = query.eq("bond_type", bond_type)
    if rating:
        query = query.eq("kis_rating", rating)
    if min_coupon is not None:
        query = query.gte("coupon_rate", min_coupon)
    if max_coupon is not None:
        query = query.lte("coupon_rate", max_coupon)
    if maturity_from is not None:
        query = query.gte("maturity_date", maturity_from)
    if maturity_to is not None:
        query = query.lte("maturity_date", maturity_to)

    start = (page - 1) * page_size
    response = (
        query.order(sort_by, desc=sort_order == "desc")
        .range(start, start + page_size - 1)
        .execute()
    )
    total = response.count if response.count is not None else len(response.data)
    return {
        "items": response.data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }


def get_bond(db: Client, isin_code: str) -> dict[str, Any] | None:
    response = (
        db.table("bonds")
        .select("*")
        .eq("isin_code", isin_code)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    bond = response.data[0]
    market = (
        db.table("bond_market").select("*").eq("isin_code", isin_code)
        .order("reference_date", desc=True).limit(1).execute().data
    )
    metrics = (
        db.table("bond_metrics").select("*").eq("isin_code", isin_code).limit(1).execute().data
    )
    return bond | {
        "market": market[0] if market else None,
        "metrics": metrics[0] if metrics else None,
    }


def compare_bonds(db: Client, isin_codes: list[str]) -> list[dict[str, Any]]:
    response = db.table("bonds").select("*").in_("isin_code", isin_codes).execute()
    by_isin = {row["isin_code"]: row for row in response.data}
    return [by_isin[code] for code in isin_codes if code in by_isin]
