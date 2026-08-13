import pandas as pd

from src.analysis.classify_duration_sensitivity import (
    DURATION_HIGH_THRESHOLD,
    DURATION_LOW_THRESHOLD,
    HIGH_SENSITIVITY,
    LOW_SENSITIVITY,
    MID_SENSITIVITY,
    build_duration_sensitivity,
    classify_duration_sensitivity,
)


def test_classifies_boundaries_inclusive_on_the_lower_side():
    assert classify_duration_sensitivity(DURATION_LOW_THRESHOLD) == LOW_SENSITIVITY
    assert classify_duration_sensitivity(DURATION_LOW_THRESHOLD + 0.01) == MID_SENSITIVITY
    assert classify_duration_sensitivity(DURATION_HIGH_THRESHOLD) == MID_SENSITIVITY
    assert classify_duration_sensitivity(DURATION_HIGH_THRESHOLD + 0.01) == HIGH_SENSITIVITY


def test_classifies_typical_values():
    assert classify_duration_sensitivity(0.02) == LOW_SENSITIVITY
    assert classify_duration_sensitivity(1.3) == MID_SENSITIVITY
    assert classify_duration_sensitivity(16.5) == HIGH_SENSITIVITY


def test_missing_duration_returns_none():
    assert classify_duration_sensitivity(float("nan")) is None


def test_builds_sensitivity_and_preserves_original_status_for_excluded_bonds():
    duration = pd.DataFrame({
        "isinCd": ["KR-low", "KR-high", "KR-excluded"],
        "modified_duration": [0.3, 5.0, float("nan")],
        "calculation_status": ["CALCULATED", "CALCULATED_HIGH_YTM", "EXCLUDED_OPTION"],
    })

    result = build_duration_sensitivity(duration).set_index("isinCd")

    assert result.loc["KR-low", "duration_sensitivity"] == LOW_SENSITIVITY
    assert result.loc["KR-high", "duration_sensitivity"] == HIGH_SENSITIVITY
    assert pd.isna(result.loc["KR-excluded", "duration_sensitivity"])
    assert result.loc["KR-excluded", "calculation_status"] == "EXCLUDED_OPTION"
