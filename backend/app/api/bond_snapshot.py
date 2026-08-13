from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from backend.app.database import get_supabase
from backend.app.services.bond_snapshot_service import SORT_FIELDS, list_bond_snapshots


router = APIRouter(prefix="/api/bond-snapshot", tags=["BondSnapshot"])


@router.get("")
def get_bond_snapshots(
    reference_date: str | None = None,
    bond_type: str | None = None,
    rating: str | None = None,
    search: str | None = Query(None, min_length=1, max_length=100),
    sort_by: str = "bond_name",
    sort_order: Literal["asc", "desc"] = "asc",
    db: Client = Depends(get_supabase),
):
    if sort_by not in SORT_FIELDS:
        raise HTTPException(status_code=422, detail=f"sort_by must be one of {sorted(SORT_FIELDS)}")
    try:
        data = list_bond_snapshots(
            db,
            reference_date=reference_date,
            bond_type=bond_type,
            rating=rating,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return {"count": len(data), "data": data}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail="Bond snapshot service is temporarily unavailable"
        ) from exc
