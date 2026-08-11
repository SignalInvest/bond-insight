from functools import lru_cache

from supabase import Client, create_client

from backend.app.config import settings


@lru_cache
def get_supabase() -> Client:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL이 설정되지 않았습니다.")

    if not settings.supabase_key:
        raise RuntimeError("SUPABASE_KEY가 설정되지 않았습니다.")

    return create_client(
        settings.supabase_url,
        settings.supabase_key,
    )
