import json
from typing import Any

import httpx

from backend.app.config import settings


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
INSTRUCTIONS = """당신은 Bond Insight의 채권 설명 도우미다.
반드시 제공된 JSON 데이터만 사용하고, 없는 숫자나 사실을 추정하지 않는다.
투자 권유나 매수·매도 지시를 하지 않는다. 초보자가 이해하기 쉬운 한국어로 설명한다.
YTM은 수익 지표, modified_duration은 금리 민감도, credit_spread는 국고채 대비 추가 금리로 설명한다.
누락된 값은 분석하지 말고 '데이터 없음'이라고 밝힌다."""


def build_bond_context(bond: dict[str, Any], metrics: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "bond": {
            key: bond.get(key) for key in (
                "isin_code", "bond_name", "issuer_name", "bond_type", "coupon_rate",
                "issue_date", "maturity_date", "kis_rating", "kbp_rating", "nice_rating",
            )
        },
        "metrics": metrics,
    }


def build_explain_prompt(context: dict[str, Any]) -> str:
    return "다음 채권의 특징, 수익, 금리위험, 신용위험을 설명해줘.\n" + json.dumps(
        context, ensure_ascii=False, allow_nan=False
    )


def build_compare_prompt(contexts: list[dict[str, Any]]) -> str:
    return "다음 채권들을 동일한 기준으로 비교하고 핵심 차이를 설명해줘.\n" + json.dumps(
        contexts, ensure_ascii=False, allow_nan=False
    )


def _generate_openai(prompt: str) -> dict[str, str]:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    response = httpx.post(
        OPENAI_RESPONSES_URL,
        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
        json={"model": settings.openai_model, "instructions": INSTRUCTIONS, "input": prompt},
        timeout=30.0,
    )
    response.raise_for_status()
    body = response.json()
    texts = [
        content["text"]
        for item in body.get("output", [])
        for content in item.get("content", [])
        if content.get("type") == "output_text" and content.get("text")
    ]
    if not texts:
        raise RuntimeError("OpenAI response did not contain output text")
    return {"explanation": "\n".join(texts), "model": body.get("model", settings.openai_model)}


def _generate_gemini(prompt: str) -> dict[str, str]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    response = httpx.post(
        GEMINI_API_URL.format(model=settings.gemini_model),
        headers={"x-goog-api-key": settings.gemini_api_key},
        json={
            "system_instruction": {"parts": [{"text": INSTRUCTIONS}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        },
        timeout=30.0,
    )
    response.raise_for_status()
    body = response.json()
    texts = [
        part["text"]
        for candidate in body.get("candidates", [])
        for part in candidate.get("content", {}).get("parts", [])
        if part.get("text")
    ]
    if not texts:
        raise RuntimeError("Gemini response did not contain output text")
    return {"explanation": "\n".join(texts), "model": settings.gemini_model}


def generate_explanation(prompt: str) -> dict[str, str]:
    if settings.ai_provider == "gemini":
        return _generate_gemini(prompt)
    if settings.ai_provider == "openai":
        return _generate_openai(prompt)
    raise RuntimeError(f"Unsupported AI_PROVIDER: {settings.ai_provider}")
