import pandas as pd

from src.processing.enrich_tableau_dashboard import enrich_tableau_dashboard


def _info_row(isin, coupon, issue, kis=None, kbp=None, nice=None, fn=None):
    return {
        "isinCd": isin, "bondSrfcInrt": coupon, "bondIssuDt": issue,
        "kisScrsItmsKcdNm": kis, "kbpScrsItmsKcdNm": kbp, "niceScrsItmsKcdNm": nice, "fnScrsItmsKcdNm": fn,
    }


def test_joins_coupon_issue_date_and_rating_by_isin():
    dashboard = pd.DataFrame({"isin_code": ["KR1", "KR2"], "close_yield": [3.5, 4.5]})
    info = pd.DataFrame([
        _info_row("KR1", "3.4", "20240315", kis="AAA"),
        _info_row("KR2", "4.1", "20250404", kis="AA-"),
    ])

    result = enrich_tableau_dashboard(dashboard, info).set_index("isin_code")

    assert result.loc["KR1", "coupon_rate"] == 3.4
    assert result.loc["KR1", "issue_date"] == "2024-03-15"
    assert result.loc["KR1", "credit_rating"] == "AAA"
    assert result.loc["KR2", "credit_rating"] == "AA-"


def test_rating_priority_falls_back_kis_kbp_nice_fn():
    dashboard = pd.DataFrame({"isin_code": ["KR1"], "close_yield": [3.5]})
    info = pd.DataFrame([_info_row("KR1", "3.4", "20240315", kis=None, kbp=None, nice=None, fn="A+")])

    result = enrich_tableau_dashboard(dashboard, info).set_index("isin_code")

    assert result.loc["KR1", "credit_rating"] == "A+"


def test_ungraded_bond_stays_null_not_defaulted():
    """국채/지방채처럼 등급 자체가 없는 채권은 결측으로 남아야 한다 - "국채니까 AAA"로
    임의 추정하면 안 된다(classify_investment_priority.py의 설계 원칙과 동일)."""
    dashboard = pd.DataFrame({"isin_code": ["KR-gov"], "close_yield": [3.5]})
    info = pd.DataFrame([_info_row("KR-gov", "1.0", "20240315")])

    result = enrich_tableau_dashboard(dashboard, info).set_index("isin_code")

    assert pd.isna(result.loc["KR-gov", "credit_rating"])


def test_missing_bond_info_yields_null_fields():
    dashboard = pd.DataFrame({"isin_code": ["KR1", "KR-unknown"], "close_yield": [3.5, 4.5]})
    info = pd.DataFrame([_info_row("KR1", "3.4", "20240315", kis="AAA")])

    result = enrich_tableau_dashboard(dashboard, info).set_index("isin_code")

    assert pd.isna(result.loc["KR-unknown", "coupon_rate"])
    assert pd.isna(result.loc["KR-unknown", "credit_rating"])


def test_preserves_row_count():
    dashboard = pd.DataFrame({"isin_code": ["KR1", "KR1", "KR2"], "close_yield": [3.5, 3.5, 4.5]})
    info = pd.DataFrame([
        _info_row("KR1", "3.4", "20240315", kis="AAA"),
        _info_row("KR2", "4.1", "20250404", kis="AA-"),
    ])

    result = enrich_tableau_dashboard(dashboard, info)

    assert len(result) == len(dashboard)


def test_rerun_is_idempotent():
    dashboard = pd.DataFrame({
        "isin_code": ["KR1"], "close_yield": [3.5],
        "coupon_rate": [999.0], "issue_date": ["1999-01-01"], "credit_rating": ["ZZZ"],
    })
    info = pd.DataFrame([_info_row("KR1", "3.4", "20240315", kis="AAA")])

    result = enrich_tableau_dashboard(dashboard, info)

    assert list(result.columns).count("coupon_rate") == 1
    assert result.loc[0, "coupon_rate"] == 3.4
    assert result.loc[0, "credit_rating"] == "AAA"
