from pydantic import BaseModel


class DiagnosisMetric(BaseModel):
    """AI 진단 데이터 계약(youngeun/ai-diagnosis/PLAN.md)의 {value, status} 형태.

    status가 "CALCULATED"가 아니면 value는 항상 None이다 - AI(또는 프론트)는
    status를 확인하지 않고 value만 사용해서는 안 된다.
    """

    value: float | str | None
    status: str


class InvestmentPriorityMetric(DiagnosisMetric):
    # 종합 판정에 실제로 쓰인 신호(등급/스프레드/Duration) 개수. 2개 미만이면
    # status="INSUFFICIENT_DATA"이고 value=None이다.
    available_signals: int


class BondDiagnosis(BaseModel):
    """backend/app/services/diagnosis_service.py의 반환 형태. ①②⑤ 3개 진단."""

    after_tax_yield_approx: DiagnosisMetric
    duration_sensitivity: DiagnosisMetric
    investment_priority: InvestmentPriorityMetric
