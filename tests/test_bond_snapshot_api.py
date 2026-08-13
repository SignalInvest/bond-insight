from fastapi.testclient import TestClient

from backend.app.database import get_supabase
from backend.app.main import app
from tests.test_backend_api import FakeDatabase


app.dependency_overrides[get_supabase] = lambda: FakeDatabase()
client = TestClient(app)


def test_bond_snapshot_list():
    response = client.get("/api/bond-snapshot")
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_bond_snapshot_filters_by_bond_type():
    response = client.get("/api/bond-snapshot", params={"bond_type": "국채"})
    assert response.status_code == 200
    assert [row["isin_code"] for row in response.json()["data"]] == ["KR1"]


def test_bond_snapshot_search():
    response = client.get("/api/bond-snapshot", params={"search": "회사"})
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["data"][0]["isin_code"] == "KR2"


def test_bond_snapshot_rejects_bad_sort():
    response = client.get("/api/bond-snapshot", params={"sort_by": "unknown"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
