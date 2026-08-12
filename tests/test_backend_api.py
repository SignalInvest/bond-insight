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
            or needle in row.get("issuer_name", "").lower()
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
            {"isin_code": "KR1", "bond_name": "국민주택채권", "issuer_name": "정부", "bond_type": "국채", "coupon_rate": 3.4, "ytm": 3.5, "remaining_years": 2.0, "maturity_date": "2028-08-11"},
            {"isin_code": "KR2", "bond_name": "회사채", "issuer_name": "우리은행", "bond_type": "회사채", "coupon_rate": 4.1, "ytm": 4.5, "remaining_years": 5.0, "maturity_date": "2031-08-11"},
        ],
        "market_rates": [
            {"reference_date": "2026-08-08", "treasury_3y": 2.8},
            {"reference_date": "2026-08-11", "treasury_3y": 2.9},
        ],
        "bond_market": [
            {"isin_code": "KR1", "reference_date": "2026-08-07", "close_price": 10000, "ytm": 3.5, "volume": 10, "trading_value": 100000, "benchmark_treasury_rate": 3.0, "credit_spread": 0.5},
            {"isin_code": "KR2", "reference_date": "2026-08-07", "close_price": 9900, "ytm": 4.5, "volume": 20, "trading_value": 198000, "benchmark_treasury_rate": 3.5, "credit_spread": 1.0},
        ],
        "bond_metrics": [
            {"isin_code": "KR1", "reference_date": "2026-08-07", "remaining_days": 730, "remaining_years": 2.0, "maturity_status": "NORMAL", "maturity_bucket": "1~3년", "macaulay_duration": 1.9, "modified_duration": 1.8, "duration_status": "CALCULATED", "schedule_estimated": False, "stub_period": False},
            {"isin_code": "KR2", "reference_date": "2026-08-07", "remaining_days": 1826, "remaining_years": 5.0, "maturity_status": "NORMAL", "maturity_bucket": "3~5년", "macaulay_duration": 4.5, "modified_duration": 4.3, "duration_status": "CALCULATED", "schedule_estimated": False, "stub_period": False},
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


def test_post_compare_keeps_requested_order():
    response = client.post("/api/compare", json={"isins": ["KR2", "KR1"]})
    assert response.status_code == 200
    assert [row["isin_code"] for row in response.json()["data"]] == ["KR2", "KR1"]


def test_analysis_and_risk_return_api():
    analysis = client.get("/api/analysis?limit=2")
    assert analysis.status_code == 200
    assert analysis.json()["count"] == 2
    risk_return = client.get("/api/analysis/risk-return?limit=2")
    assert risk_return.status_code == 200
    assert risk_return.json()["axes"]["return"] == "ytm"
    assert risk_return.json()["count"] == 2


def test_rejects_unsafe_sort_field():
    response = client.get("/api/bonds", params={"sort_by": "unknown"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


def test_bond_issuer_and_maturity_filters():
    response = client.get("/api/bonds", params={
        "issuer": "우리은행", "maturity_from": "2030-01-01", "size": 1,
    })
    assert response.status_code == 200
    assert [row["isin_code"] for row in response.json()["items"]] == ["KR2"]
    assert response.json()["pagination"]["page_size"] == 1


def test_rejects_inverted_filter_ranges():
    assert client.get("/api/bonds?min_coupon=5&max_coupon=3").status_code == 422
    assert client.get("/api/bonds?maturity_from=2030-01-01&maturity_to=2029-01-01").status_code == 422


def test_validation_errors_have_common_shape():
    response = client.get("/api/bonds?page=0")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["field"] == "page"
