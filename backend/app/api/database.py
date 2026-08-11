from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from backend.app.database import get_supabase


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


@router.get("/health")
def database_health(db: Client = Depends(get_supabase)):
    try:
        response = (
            db
            .table("health_check")
            .select("id, status")
            .limit(1)
            .execute()
        )

        return {
            "status": "ok",
            "database": "supabase",
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Supabase connection failed: {str(e)}"
        )
