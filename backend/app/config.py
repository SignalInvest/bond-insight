import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    app_name: str = "Bond Insight API"
    app_version: str = "0.1.0"

    # 이후 실제 기능을 연결할 때 사용
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_key: str | None = os.getenv("SUPABASE_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai").lower()
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")


settings = Settings()
