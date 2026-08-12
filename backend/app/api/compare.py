from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from backend.app.database import get_supabase
from backend.app.services.bond_service import compare_bonds
from backend.app.schemas.compare import BondCompareRequest
from backend.app.services.analysis_service import get_analysis


router = APIRouter(prefix="/api/bonds", tags=["Bond Compare"])
post_router = APIRouter(prefix="/api/compare", tags=["Bond Compare"])


def _comparison_response(db: Client, isin_codes: list[str]):
    data = compare_bonds(db, isin_codes)
    metrics = {row["isin_code"]: row for row in get_analysis(db, limit=5, isin_codes=isin_codes)}
    enriched = [row | {"analysis": metrics.get(row["isin_code"])} for row in data]
    found = {row["isin_code"] for row in data}
    return {
        "count": len(enriched),
        "data": enriched,
        "missing_isin_codes": [code for code in isin_codes if code not in found],
    }


@router.get("/compare")
def compare(
    isin: list[str] = Query(..., min_length=2, max_length=5),
    db: Client = Depends(get_supabase),
):
    isin_codes = list(dict.fromkeys(code.strip() for code in isin if code.strip()))
    if not 2 <= len(isin_codes) <= 5:
        raise HTTPException(status_code=422, detail="Provide 2 to 5 unique ISIN codes")
    try:
        return _comparison_response(db, isin_codes)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Bond comparison service is temporarily unavailable") from exc


@post_router.post("")
def compare_post(payload: BondCompareRequest, db: Client = Depends(get_supabase)):
    isin_codes = list(dict.fromkeys(code.strip() for code in payload.isins if code.strip()))
    if not 2 <= len(isin_codes) <= 5:
        raise HTTPException(status_code=422, detail="Provide 2 to 5 unique ISIN codes")
    try:
        return _comparison_response(db, isin_codes)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Bond comparison service is temporarily unavailable") from exc
