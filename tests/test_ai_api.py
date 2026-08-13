from fastapi.testclient import TestClient

from backend.app.api import ai
from backend.app.ai import explanation_service
from backend.app.database import get_supabase
from backend.app.main import app
from tests.test_backend_api import FakeDatabase


app.dependency_overrides[get_supabase] = lambda: FakeDatabase()
client = TestClient(app)


def fake_generate(prompt: str):
    assert "JSON" not in prompt or prompt
    return {"explanation": "검증된 데이터 기반 설명", "model": "test-model"}


def test_ai_explain(monkeypatch):
    monkeypatch.setattr(ai, "generate_explanation", fake_generate)
    response = client.post("/api/ai/explain", json={"isin": "KR1"})
    assert response.status_code == 200
    assert response.json()["model"] == "test-model"
    assert response.json()["context"]["bond"]["isin_code"] == "KR1"


def test_ai_compare(monkeypatch):
    monkeypatch.setattr(ai, "generate_explanation", fake_generate)
    response = client.post("/api/ai/compare", json={"isins": ["KR2", "KR1"]})
    assert response.status_code == 200
    assert [item["bond"]["isin_code"] for item in response.json()["context"]] == ["KR2", "KR1"]


def test_ai_missing_bond():
    response = client.post("/api/ai/explain", json={"isin": "UNKNOWN"})
    assert response.status_code == 404


def test_ai_explain_includes_diagnosis(monkeypatch):
    monkeypatch.setattr(ai, "generate_explanation", fake_generate)
    response = client.post("/api/ai/explain", json={"isin": "KR1"})
    diagnosis = response.json()["context"]["diagnosis"]

    # KR1: ytm=3.5, coupon_rate=3.4 -> after_tax_yield_approx = 3.5 - 3.4*0.154 = 2.9764
    assert diagnosis["after_tax_yield_approx"]["status"] == "CALCULATED"
    assert abs(diagnosis["after_tax_yield_approx"]["value"] - 2.9764) < 0.0001

    # modified_duration=1.8 -> "중간" 등급 (0.5 < 1.8 <= 2.5)
    assert diagnosis["duration_sensitivity"] == {"value": "중간", "status": "CALCULATED"}

    # 등급 없음(신호 제외) + 스프레드 0.5(NEUTRAL) + Duration 중간(NEUTRAL) -> 균형형
    assert diagnosis["investment_priority"]["value"] == "균형형"


def test_provider_dispatches_to_gemini(monkeypatch):
    monkeypatch.setattr(explanation_service.settings, "ai_provider", "gemini")
    monkeypatch.setattr(
        explanation_service,
        "_generate_gemini",
        lambda prompt: {"explanation": "gemini", "model": "test-gemini"},
    )
    assert explanation_service.generate_explanation("test")["model"] == "test-gemini"
