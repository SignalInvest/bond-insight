from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from backend.app.database import get_supabase
from backend.app.services.bond_service import compare_bonds


router = APIRouter(prefix="/api/bonds", tags=["Bond Compare"])


@router.get("/compare")
def compare(
    isin: list[str] = Query(..., min_length=2, max_length=5),
    db: Client = Depends(get_supabase),
):
    isin_codes = list(dict.fromkeys(code.strip() for code in isin if code.strip()))
    if not 2 <= len(isin_codes) <= 5:
        raise HTTPException(status_code=422, detail="Provide 2 to 5 unique ISIN codes")
    try:
        data = compare_bonds(db, isin_codes)
        found = {row["isin_code"] for row in data}
        return {
            "count": len(data),
            "data": data,
            "missing_isin_codes": [code for code in isin_codes if code not in found],
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Bond comparison query failed: {exc}") from exc
