from dataclasses import dataclass

from fastapi.testclient import TestClient

from backend.app.database import get_supabase
from backend.app.main import app


@dataclass
class FakeResponse:
    data: list[dict]
    count: int | None = None


class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)
        self.exact_count = False

    def select(self, *args, **kwargs):
        self.exact_count = kwargs.get("count") == "exact"
        return self

    def eq(self, column, value):
        self.rows = [row for row in self.rows if row.get(column) == value]
        return self

    def gte(self, column, value):
        self.rows = [row for row in self.rows if row.get(column) >= value]
        return self

    def lte(self, column, value):
        self.rows = [row for row in self.rows if row.get(column) <= value]
        return self

    def in_(self, column, values):
        self.rows = [row for row in self.rows if row.get(column) in values]
        return self

    def or_(self, expression):
        needle = expression.split("%", 2)[1].lower()
        self.rows = [
            row for row in self.rows
            if needle in row.get("bond_name", "").lower()
            or needle in row.get("isin_code", "").lower()
        ]
        return self

    def order(self, column, desc=False):
        self.rows.sort(key=lambda row: row.get(column), reverse=desc)
        return self

    def range(self, start, end):
        self.rows = self.rows[start:end + 1]
        return self

    def limit(self, limit):
        self.rows = self.rows[:limit]
        return self

    def execute(self):
        return FakeResponse(self.rows, len(self.rows) if self.exact_count else None)


class FakeDatabase:
    tables = {
        "bonds": [
            {"isin_code": "KR1", "bond_name": "국민주택채권", "bond_type": "국채", "coupon_rate": 3.4},
            {"isin_code": "KR2", "bond_name": "회사채", "bond_type": "회사채", "coupon_rate": 4.1},
        ],
        "market_rates": [
            {"reference_date": "2026-08-08", "treasury_3y": 2.8},
            {"reference_date": "2026-08-11", "treasury_3y": 2.9},
        ],
        "health_check": [{"id": 1, "status": "ok"}],
    }

    def table(self, name):
        return FakeQuery(self.tables[name])


app.dependency_overrides[get_supabase] = lambda: FakeDatabase()
client = TestClient(app)


def test_bond_search_and_pagination():
    response = client.get("/api/bonds", params={"search": "국민", "page_size": 10})
    assert response.status_code == 200
    assert response.json()["items"][0]["isin_code"] == "KR1"
    assert response.json()["pagination"]["total"] == 1


def test_bond_detail_and_not_found():
    assert client.get("/api/bonds/KR2").status_code == 200
    assert client.get("/api/bonds/UNKNOWN").status_code == 404


def test_market_latest_and_date_validation():
    response = client.get("/api/market")
    assert response.status_code == 200
    assert response.json()["latest"]["reference_date"] == "2026-08-11"
    invalid = client.get("/api/market?start_date=2026-08-11&end_date=2026-08-01")
    assert invalid.status_code == 422


def test_compare_keeps_requested_order():
    response = client.get("/api/bonds/compare", params=[("isin", "KR2"), ("isin", "KR1")])
    assert response.status_code == 200
    assert [row["isin_code"] for row in response.json()["data"]] == ["KR2", "KR1"]


def test_rejects_unsafe_sort_field():
    response = client.get("/api/bonds", params={"sort_by": "unknown"})
    assert response.status_code == 422
