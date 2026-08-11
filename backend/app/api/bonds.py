from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from backend.app.database import get_supabase
from backend.app.services.bond_service import SORT_FIELDS, get_bond, list_bonds


router = APIRouter(
    prefix="/api/bonds",
    tags=["Bonds"],
)


@router.get("")
def get_bonds(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, min_length=1, max_length=100),
    bond_type: str | None = None,
    rating: str | None = None,
    min_coupon: float | None = None,
    max_coupon: float | None = None,
    sort_by: str = "bond_name",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Client = Depends(get_supabase),
):
    if min_coupon is not None and max_coupon is not None and min_coupon > max_coupon:
        raise HTTPException(status_code=422, detail="min_coupon must be <= max_coupon")
    if sort_by not in SORT_FIELDS:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of {sorted(SORT_FIELDS)}")
    try:
        return list_bonds(
            db,
            page=page,
            page_size=page_size,
            search=search,
            bond_type=bond_type,
            rating=rating,
            min_coupon=min_coupon,
            max_coupon=max_coupon,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Bond data query failed: {str(e)}"
        )


@router.get("/{isin_code}")
def get_bond_detail(isin_code: str, db: Client = Depends(get_supabase)):
    try:
        bond = get_bond(db, isin_code)
        if not bond:
            raise HTTPException(
                status_code=404,
                detail="Bond not found"
            )

        return bond

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Bond data query failed: {str(e)}"
        )
