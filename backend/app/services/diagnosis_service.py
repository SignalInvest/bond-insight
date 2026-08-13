from typing import Any

from src.analysis.calculate_after_tax_yield import (
    CALCULATED as AFTER_TAX_CALCULATED,
    OUTLIER_YTM as AFTER_TAX_OUTLIER_YTM,
    calculate_after_tax_yield_approx,
    classify_after_tax_yield_status,
)
from src.analysis.classify_duration_sensitivity import classify_duration_sensitivity
from src.analysis.classify_investment_priority import (
    PRIORITY_INSUFFICIENT,
    classify_duration_signal,
    classify_investment_priority,
    classify_rating_signal,
    classify_spread_signal,
)


def _resolve_credit_rating(bond: dict[str, Any]) -> str | None:
    """kis > kbp > nice > fn 우선순위로 첫 값을 채택한다 (bond_info_raw.csv 조인 로직과 동일)."""
    return bond.get("kis_rating") or bond.get("kbp_rating") or bond.get("nice_rating") or bond.get("fn_rating")


def build_bond_diagnosis(bond: dict[str, Any], metrics: dict[str, Any] | None) -> dict[str, Any]:
    """AI 설명(explanation_service)에 넘길 3개 진단을 계산한다.

    ① 세후 예상수익률(근사) - src/analysis/calculate_after_tax_yield.py
    ② Duration 민감도 등급   - src/analysis/classify_duration_sensitivity.py
    ⑤ 종합 성향 매칭         - src/analysis/classify_investment_priority.py

    세 함수 모두 src/analysis/의 순수 함수를 그대로 재사용한다 - 계산 로직이 여러 곳에서
    따로 관리되지 않도록 하기 위함(bond_snapshot_service.py의 after-tax yield 연동과
    동일 원칙). 반환값은 전부 {value, status} 형태(AI 진단 데이터 계약,
    youngeun/ai-diagnosis/PLAN.md) - status가 CALCULATED가 아니면 value는 항상 None이며,
    호출 측(AI 프롬프트)은 status를 반드시 함께 취급해야 한다.

    metrics는 backend.app.services.analysis_service.get_analysis()가 반환하는 행 하나
    (ytm, credit_spread, metrics: {modified_duration, duration_status, ...} 포함)이고,
    bond는 backend.app.services.bond_service.get_bond()가 반환하는 채권 마스터 행이다.
    """
    metrics = metrics or {}
    nested_metrics = metrics.get("metrics") or {}

    ytm = metrics.get("ytm")
    coupon_rate = bond.get("coupon_rate")
    modified_duration = nested_metrics.get("modified_duration")
    credit_spread = metrics.get("credit_spread")
    credit_rating = _resolve_credit_rating(bond)

    # ① 세후 예상수익률(근사)
    after_tax_status = classify_after_tax_yield_status(ytm, coupon_rate)
    after_tax_value = (
        calculate_after_tax_yield_approx(ytm, coupon_rate)
        if after_tax_status == AFTER_TAX_CALCULATED
        else None
    )

    # ② Duration 민감도 등급. 계산 제외 사유는 bond_metrics.duration_status(원본)를 그대로 노출.
    duration_sensitivity = classify_duration_sensitivity(modified_duration)
    duration_status = (
        "CALCULATED" if duration_sensitivity is not None else (nested_metrics.get("duration_status") or "NOT_APPLICABLE")
    )

    # ⑤ 종합 성향 매칭. ①이 OUTLIER_YTM이면 같은 YTM에서 파생된 신용스프레드도 신호에서 제외
    # (src/analysis/classify_investment_priority.py의 build_investment_priority와 동일 가드).
    spread_for_signal = None if after_tax_status == AFTER_TAX_OUTLIER_YTM else credit_spread
    rating_signal = classify_rating_signal(credit_rating)
    spread_signal = classify_spread_signal(spread_for_signal)
    duration_signal = classify_duration_signal(duration_sensitivity)
    priority, _score, available_signals = classify_investment_priority(
        rating_signal, spread_signal, duration_signal
    )

    return {
        "after_tax_yield_approx": {"value": after_tax_value, "status": after_tax_status},
        "duration_sensitivity": {"value": duration_sensitivity, "status": duration_status},
        "investment_priority": {
            "value": None if priority == PRIORITY_INSUFFICIENT else priority,
            "status": priority if priority == PRIORITY_INSUFFICIENT else "CALCULATED",
            "available_signals": available_signals,
        },
    }
