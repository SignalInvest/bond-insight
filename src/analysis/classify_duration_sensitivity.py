from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOND_DURATION = PROJECT_ROOT / "data" / "processed" / "bond_duration.csv"
OUTPUT = PROJECT_ROOT / "data" / "processed" / "bond_duration_sensitivity.csv"

# modified_duration(년) 구간. data/processed/bond_duration.csv의 계산 가능 250건
# (2026-08-07 기준) 분포로 결정 - 중앙값 1.30, 평균 2.74로 오른쪽 꼬리가 긴 분포라
# 삼분위수(약 0.56 / 2.32)에 가까우면서 "금리 1%p 변화에 가격이 몇 % 움직이는지"를
# 그대로 문턱값으로 쓸 수 있는 반올림 값(0.5 / 2.5)을 채택했다.
# (0.5, 2.5) 기준 저/중/고 비율은 약 28% / 40% / 32%로 나뉜다.
DURATION_LOW_THRESHOLD = 0.5
DURATION_HIGH_THRESHOLD = 2.5

LOW_SENSITIVITY = "저민감"
MID_SENSITIVITY = "중간"
HIGH_SENSITIVITY = "고민감"

# modified_duration이 계산되지 않은 채권(bond_duration.csv의 calculation_status가
# CALCULATED/CALCULATED_HIGH_YTM이 아닌 경우)은 등급을 매기지 않고 None을 반환한다.
# 왜 계산이 안 됐는지는 원본 calculation_status(EXCLUDED_OPTION, NO_MARKET_DATA 등)를
# 그대로 함께 남겨 호출 측(AI 설명 등)이 정확한 사유를 서술할 수 있게 한다.


def classify_duration_sensitivity(modified_duration: float) -> str | None:
    """modified_duration(년)을 금리 민감도 등급으로 분류한다. 계산값이 없으면 None."""
    if pd.isna(modified_duration):
        return None
    if modified_duration <= DURATION_LOW_THRESHOLD:
        return LOW_SENSITIVITY
    if modified_duration <= DURATION_HIGH_THRESHOLD:
        return MID_SENSITIVITY
    return HIGH_SENSITIVITY


def build_duration_sensitivity(duration: pd.DataFrame) -> pd.DataFrame:
    """bond_duration.csv(전체 29,088건, isinCd/modified_duration/calculation_status 포함)로부터
    금리 민감도 등급을 추가한다.

    반환 컬럼: isinCd, modified_duration, calculation_status, duration_sensitivity
    """
    result = duration[["isinCd", "modified_duration", "calculation_status"]].copy()
    result["duration_sensitivity"] = result["modified_duration"].apply(classify_duration_sensitivity)
    return result


def main() -> None:
    duration = pd.read_csv(BOND_DURATION)
    result = build_duration_sensitivity(duration)
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"[DONE] Duration sensitivity CSV -> {OUTPUT} ({len(result)} rows)")
    print(result["duration_sensitivity"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
