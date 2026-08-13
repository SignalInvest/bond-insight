"""cpi_monthly.csv에서 전년동월 대비 상승률(cpi_yoy)을 계산해 market_rates.cpi_yoy에 채운다.

사전 조건: Supabase market_rates 테이블에 cpi_yoy 컬럼이 이미 추가되어 있어야 한다.
    ALTER TABLE market_rates ADD COLUMN cpi_yoy numeric;

계산 방식은 yunseo/SKILL.md 2-1과 동일:
- cpi_yoy = (이번 달 CPI - 작년 같은 달 CPI) / 작년 같은 달 CPI * 100
- 첫 12개월(2015-01~2015-12)은 전년 데이터가 없어 계산하지 않음 (값 없이 그대로 둠)
- 월별 값을 그 달의 모든 일자에 그대로 적용 (실제 발표일 반영 안 함 — 알려진 단순화, SKILL.md 2-1 참고)
"""

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import get_supabase  # noqa: E402


CPI_CSV = PROJECT_ROOT / "data/processed/cpi_monthly.csv"


def build_monthly_cpi_yoy() -> pd.DataFrame:
    cpi = pd.read_csv(CPI_CSV, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    cpi["cpi_yoy"] = cpi["cpi"].pct_change(periods=12) * 100
    cpi["year_month"] = cpi["date"].dt.to_period("M")
    return cpi.dropna(subset=["cpi_yoy"])[["year_month", "cpi_yoy"]]


def main() -> None:
    db = get_supabase()
    monthly = build_monthly_cpi_yoy()
    print(f"[cpi] {len(monthly)}개월치 cpi_yoy 계산 완료 — market_rates에 반영 시작")

    updated_months = 0
    for _, row in monthly.iterrows():
        period = row["year_month"]
        start = period.start_time.date().isoformat()
        end = (period + 1).start_time.date().isoformat()
        value = round(float(row["cpi_yoy"]), 4)

        result = (
            db.table("market_rates")
            .update({"cpi_yoy": value})
            .gte("reference_date", start)
            .lt("reference_date", end)
            .execute()
        )
        affected = len(result.data)
        if affected:
            updated_months += 1
        print(f"[cpi] {start[:7]}: cpi_yoy={value} -> {affected}건 갱신")

    print(f"[DONE] {updated_months}/{len(monthly)}개월 반영 완료")

    # cpi_monthly.csv에 아직 없는 최신 달(예: 이번 달, 발표 전)은 위 루프에서 채워지지 않는다.
    # 실무에서도 그 시점엔 "가장 최근 발표된 값"을 쓰므로, 마지막으로 계산된 달의 cpi_yoy를
    # 그 이후의 아직 비어있는 날짜에 그대로 이월한다.
    last_period = monthly["year_month"].max()
    last_value = round(float(monthly.loc[monthly["year_month"] == last_period, "cpi_yoy"].iloc[0]), 4)
    carry_from = (last_period + 1).start_time.date().isoformat()
    carried = (
        db.table("market_rates")
        .update({"cpi_yoy": last_value})
        .gte("reference_date", carry_from)
        .is_("cpi_yoy", "null")
        .execute()
    )
    print(f"[cpi] {carry_from} 이후 발표 전 구간에 {last_period} 값({last_value}) 이월 -> {len(carried.data)}건")


if __name__ == "__main__":
    main()
