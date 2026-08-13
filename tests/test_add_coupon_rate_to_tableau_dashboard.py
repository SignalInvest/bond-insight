import pandas as pd

from src.processing.add_coupon_rate_to_tableau_dashboard import add_coupon_rate_and_issue_date


def test_joins_coupon_rate_and_issue_date_by_isin():
    dashboard = pd.DataFrame({"isin_code": ["KR1", "KR2"], "close_yield": [3.5, 4.5]})
    info = pd.DataFrame({
        "isinCd": ["KR1", "KR2"],
        "bondSrfcInrt": ["3.4", "4.1"],
        "bondIssuDt": ["20240315", "20250404"],
    })

    result = add_coupon_rate_and_issue_date(dashboard, info).set_index("isin_code")

    assert result.loc["KR1", "coupon_rate"] == 3.4
    assert result.loc["KR1", "issue_date"] == "2024-03-15"
    assert result.loc["KR2", "coupon_rate"] == 4.1
    assert result.loc["KR2", "issue_date"] == "2025-04-04"


def test_missing_bond_info_yields_null_fields():
    dashboard = pd.DataFrame({"isin_code": ["KR1", "KR-unknown"], "close_yield": [3.5, 4.5]})
    info = pd.DataFrame({"isinCd": ["KR1"], "bondSrfcInrt": ["3.4"], "bondIssuDt": ["20240315"]})

    result = add_coupon_rate_and_issue_date(dashboard, info).set_index("isin_code")

    assert result.loc["KR1", "coupon_rate"] == 3.4
    assert pd.isna(result.loc["KR-unknown", "coupon_rate"])
    assert pd.isna(result.loc["KR-unknown", "issue_date"])


def test_preserves_row_count():
    dashboard = pd.DataFrame({"isin_code": ["KR1", "KR1", "KR2"], "close_yield": [3.5, 3.5, 4.5]})
    info = pd.DataFrame({
        "isinCd": ["KR1", "KR2"], "bondSrfcInrt": ["3.4", "4.1"], "bondIssuDt": ["20240315", "20250404"],
    })

    result = add_coupon_rate_and_issue_date(dashboard, info)

    assert len(result) == len(dashboard)


def test_rerun_is_idempotent():
    """이미 coupon_rate/issue_date가 있는 dashboard(재실행 상황)에 다시 조인해도
    컬럼이 coupon_rate_x/coupon_rate_y처럼 중복되지 않아야 한다."""
    dashboard = pd.DataFrame({
        "isin_code": ["KR1"], "close_yield": [3.5], "coupon_rate": [999.0], "issue_date": ["1999-01-01"],
    })
    info = pd.DataFrame({"isinCd": ["KR1"], "bondSrfcInrt": ["3.4"], "bondIssuDt": ["20240315"]})

    result = add_coupon_rate_and_issue_date(dashboard, info)

    assert list(result.columns).count("coupon_rate") == 1
    assert result.loc[0, "coupon_rate"] == 3.4
    assert result.loc[0, "issue_date"] == "2024-03-15"
