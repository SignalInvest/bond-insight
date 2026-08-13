from backend.app.schemas.diagnosis import BondDiagnosis
from backend.app.services.diagnosis_service import build_bond_diagnosis


def _metrics(ytm, credit_spread, modified_duration, duration_status="CALCULATED"):
    return {
        "ytm": ytm,
        "credit_spread": credit_spread,
        "metrics": {"modified_duration": modified_duration, "duration_status": duration_status},
    }


def test_all_three_calculated_for_a_healthy_bond():
    bond = {"coupon_rate": 3.4, "kis_rating": "AAA"}
    metrics = _metrics(ytm=3.5, credit_spread=-0.1, modified_duration=0.3)

    result = build_bond_diagnosis(bond, metrics)

    assert result["after_tax_yield_approx"]["status"] == "CALCULATED"
    assert abs(result["after_tax_yield_approx"]["value"] - 2.9764) < 0.0001

    assert result["duration_sensitivity"]["status"] == "CALCULATED"
    assert result["duration_sensitivity"]["value"] == "저민감"

    # 등급 AAA(STABLE) + 스프레드 -0.1(STABLE) + Duration 저민감(STABLE) -> 안정성 중심
    assert result["investment_priority"]["status"] == "CALCULATED"
    assert result["investment_priority"]["value"] == "안정성 중심"


def test_outlier_ytm_masks_after_tax_yield_and_credit_spread_signal():
    bond = {"coupon_rate": 6.7, "kis_rating": "BBB+"}
    metrics = _metrics(ytm=249.639, credit_spread=245.9, modified_duration=0.05)

    result = build_bond_diagnosis(bond, metrics)

    assert result["after_tax_yield_approx"]["status"] == "OUTLIER_YTM"
    assert result["after_tax_yield_approx"]["value"] is None

    # 등급(BBB+=YIELD) + Duration(저민감=STABLE) 2개 신호만 남아 합산 0 -> 균형형
    # (스프레드는 OUTLIER_YTM에서 파생돼 신호에서 제외됨)
    assert result["investment_priority"]["value"] == "균형형"


def test_duration_excluded_bond_keeps_original_reason():
    bond = {"coupon_rate": 3.0, "kis_rating": "AA-"}
    metrics = _metrics(ytm=3.2, credit_spread=0.1, modified_duration=None, duration_status="EXCLUDED_OPTION")

    result = build_bond_diagnosis(bond, metrics)

    assert result["duration_sensitivity"]["value"] is None
    assert result["duration_sensitivity"]["status"] == "EXCLUDED_OPTION"


def test_missing_metrics_yields_insufficient_data_priority():
    bond = {"coupon_rate": None, "kis_rating": None}
    result = build_bond_diagnosis(bond, metrics=None)

    assert result["after_tax_yield_approx"]["status"] == "MISSING_YTM"
    assert result["duration_sensitivity"]["status"] == "NOT_APPLICABLE"
    assert result["investment_priority"]["status"] == "INSUFFICIENT_DATA"
    assert result["investment_priority"]["available_signals"] == 0


def test_rating_priority_falls_back_kis_kbp_nice_fn():
    bond = {"coupon_rate": 3.0, "kis_rating": None, "kbp_rating": None, "nice_rating": None, "fn_rating": "A+"}
    metrics = _metrics(ytm=3.2, credit_spread=0.1, modified_duration=1.0)

    result = build_bond_diagnosis(bond, metrics)

    # A+(NEUTRAL) + spread 0.1(NEUTRAL) + duration 중간(NEUTRAL) -> 합산 0 -> 균형형
    assert result["investment_priority"]["value"] == "균형형"


def test_output_matches_bond_diagnosis_schema():
    bond = {"coupon_rate": 3.4, "kis_rating": "AAA"}
    metrics = _metrics(ytm=3.5, credit_spread=-0.1, modified_duration=0.3)

    result = build_bond_diagnosis(bond, metrics)

    BondDiagnosis.model_validate(result)
