import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    app_name: str = "Bond Insight API"
    app_version: str = "0.1.0"

    # 이후 실제 기능을 연결할 때 사용
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_key: str | None = os.getenv("SUPABASE_KEY")


settings = Settings()