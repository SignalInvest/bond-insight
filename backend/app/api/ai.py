from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from backend.app.ai.explanation_service import (
    build_bond_context,
    build_compare_prompt,
    build_explain_prompt,
    generate_explanation,
)
from backend.app.database import get_supabase
from backend.app.schemas.ai import BondAICompareRequest, BondExplainRequest
from backend.app.services.analysis_service import get_analysis
from backend.app.services.bond_service import compare_bonds, get_bond


router = APIRouter(prefix="/api/ai", tags=["AI"])


def _metrics_by_isin(db: Client, isins: list[str]):
    return {row["isin_code"]: row for row in get_analysis(db, limit=5, isin_codes=isins)}


@router.post("/explain")
def explain(payload: BondExplainRequest, db: Client = Depends(get_supabase)):
    bond = get_bond(db, payload.isin.strip())
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
    context = build_bond_context(bond, _metrics_by_isin(db, [bond["isin_code"]]).get(bond["isin_code"]))
    try:
        result = generate_explanation(build_explain_prompt(context))
        return result | {"context": context}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI explanation service is temporarily unavailable") from exc


@router.post("/compare")
def compare(payload: BondAICompareRequest, db: Client = Depends(get_supabase)):
    isins = list(dict.fromkeys(code.strip() for code in payload.isins if code.strip()))
    if not 2 <= len(isins) <= 5:
        raise HTTPException(status_code=422, detail="Provide 2 to 5 unique ISIN codes")
    bonds = compare_bonds(db, isins)
    found = {row["isin_code"] for row in bonds}
    missing = [code for code in isins if code not in found]
    if missing:
        raise HTTPException(status_code=404, detail={"message": "Bond not found", "isins": missing})
    metrics = _metrics_by_isin(db, isins)
    contexts = [build_bond_context(bond, metrics.get(bond["isin_code"])) for bond in bonds]
    try:
        result = generate_explanation(build_compare_prompt(contexts))
        return result | {"context": contexts}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI comparison service is temporarily unavailable") from exc
