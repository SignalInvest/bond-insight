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


def test_bond_snapshot_includes_after_tax_yield_approx():
    response = client.get("/api/bond-snapshot")
    assert response.status_code == 200
    rows = {row["isin_code"]: row for row in response.json()["data"]}

    # KR1: ytm=3.5, coupon_rate=3.4 -> 3.5 - 3.4*0.154 = 2.9764
    assert rows["KR1"]["after_tax_yield_status"] == "CALCULATED"
    assert abs(rows["KR1"]["after_tax_yield_approx"] - 2.9764) < 0.0001

    # KR2: ytm=4.5, coupon_rate=4.1 -> 4.5 - 4.1*0.154 = 3.8686
    assert rows["KR2"]["after_tax_yield_status"] == "CALCULATED"
    assert abs(rows["KR2"]["after_tax_yield_approx"] - 3.8686) < 0.0001
