from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from backend.app.database import get_supabase
from backend.app.services.analysis_service import get_analysis, get_risk_return


router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


@router.get("")
def analysis_overview(limit: int = Query(100, ge=1, le=1000), db: Client = Depends(get_supabase)):
    try:
        data = get_analysis(db, limit=limit)
        return {"count": len(data), "data": data}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Analysis service is temporarily unavailable") from exc


@router.get("/risk-return")
def risk_return(limit: int = Query(100, ge=1, le=1000), db: Client = Depends(get_supabase)):
    try:
        data = get_risk_return(db, limit=limit)
        return {
            "count": len(data),
            "axes": {
                "return": "ytm",
                "interest_rate_risk": "modified_duration",
                "credit_risk": "credit_spread",
            },
            "data": data,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Analysis service is temporarily unavailable") from exc
