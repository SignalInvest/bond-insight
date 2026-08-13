from typing import Any

from supabase import Client

from src.analysis.calculate_after_tax_yield import (
    CALCULATED,
    calculate_after_tax_yield_approx,
    classify_after_tax_yield_status,
)


SORT_FIELDS = {"bond_name", "issuer", "ytm", "close_price", "remaining_days", "coupon_rate"}


def _with_after_tax_yield(row: dict[str, Any]) -> dict[str, Any]:
    """bond_snapshot 행(ytm/coupon_rate 포함)에 세후 예상수익률(근사값)을 계산해 붙인다.

    src/analysis/calculate_after_tax_yield.py와 동일한 공식·가드를 그대로 재사용한다 -
    계산 로직이 두 곳에서 따로 관리되지 않도록. status가 CALCULATED가 아니면
    after_tax_yield_approx는 항상 None이다(호출 측이 status 확인 없이 값만 써서
    이상치를 노출하는 사고를 막기 위함).
    """
    ytm = row.get("ytm")
    coupon_rate = row.get("coupon_rate")
    status = classify_after_tax_yield_status(ytm, coupon_rate)
    value = calculate_after_tax_yield_approx(ytm, coupon_rate) if status == CALCULATED else None
    return row | {"after_tax_yield_approx": value, "after_tax_yield_status": status}


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
    return [_with_after_tax_yield(row) for row in response.data]
