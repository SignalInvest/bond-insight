from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from backend.app.database import get_supabase
from backend.app.services.market_service import get_market_rates


router = APIRouter(prefix="/api/market", tags=["Market"])


@router.get("")
def market_overview(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Client = Depends(get_supabase),
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be <= end_date")
    try:
        data = get_market_rates(db, start_date=start_date, end_date=end_date, limit=limit)
        return {"count": len(data), "latest": data[0] if data else None, "data": data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Market data service is temporarily unavailable") from exc
