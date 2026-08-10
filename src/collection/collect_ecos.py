import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv


# =========================================================
# 1. 프로젝트 경로
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_PATH = PROJECT_ROOT / ".env"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "ecos"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. ECOS API KEY
# =========================================================

load_dotenv(ENV_PATH)

ECOS_API_KEY = os.getenv("ECOS_API_KEY")

if not ECOS_API_KEY:
    raise ValueError(
        "ECOS_API_KEY를 찾을 수 없습니다.\n"
        "프로젝트 최상단 .env 파일을 확인해주세요."
    )


# =========================================================
# 3. 기본 설정
# =========================================================

BASE_URL = "https://ecos.bok.or.kr/api"

DAILY_START = "20150101"
DAILY_END = datetime.now().strftime("%Y%m%d")

MONTHLY_START = "201501"
MONTHLY_END = datetime.now().strftime("%Y%m")


# =========================================================
# 4. ECOS 데이터 수집 함수
# =========================================================

def collect_ecos_series(
    stat_code,
    item_code,
    cycle,
    start_date,
    end_date,
    column_name,
    raw_file_name,
):

    url = (
        f"{BASE_URL}/StatisticSearch/"
        f"{ECOS_API_KEY}/json/kr/"
        f"1/10000/"
        f"{stat_code}/"
        f"{cycle}/"
        f"{start_date}/"
        f"{end_date}/"
        f"{item_code}"
    )

    print("\n" + "=" * 60)
    print(f"{column_name} 수집 시작")
    print("=" * 60)

    response = requests.get(
        url,
        timeout=60
    )

    print("HTTP 상태코드:", response.status_code)

    response.raise_for_status()

    data = response.json()

    # -----------------------------------------------------
    # ECOS API 오류 확인
    # -----------------------------------------------------

    if "RESULT" in data:

        result = data["RESULT"]

        raise RuntimeError(
            f"ECOS API 오류\n"
            f"CODE: {result.get('CODE')}\n"
            f"MESSAGE: {result.get('MESSAGE')}"
        )

    rows = (
        data
        .get("StatisticSearch", {})
        .get("row", [])
    )

    if not rows:
        raise RuntimeError(
            f"{column_name} 데이터를 가져오지 못했습니다."
        )

    # -----------------------------------------------------
    # Raw 저장
    # -----------------------------------------------------

    raw_df = pd.DataFrame(rows)

    raw_path = RAW_DIR / raw_file_name

    raw_df.to_csv(
        raw_path,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"✅ RAW 저장 완료: {raw_path}")
    print(f"✅ 수집 건수: {len(raw_df):,}건")

    # -----------------------------------------------------
    # 필요한 컬럼만 정제
    # -----------------------------------------------------

    df = raw_df[
        [
            "TIME",
            "DATA_VALUE"
        ]
    ].copy()

    df = df.rename(
        columns={
            "TIME": "date",
            "DATA_VALUE": column_name
        }
    )

    # 날짜 처리
    if cycle == "D":

        df["date"] = pd.to_datetime(
            df["date"],
            format="%Y%m%d",
            errors="coerce"
        )

    elif cycle == "M":

        df["date"] = pd.to_datetime(
            df["date"],
            format="%Y%m",
            errors="coerce"
        )

    # 숫자 처리
    df[column_name] = pd.to_numeric(
        df[column_name],
        errors="coerce"
    )

    # 결측 제거
    df = df.dropna(
        subset=[
            "date",
            column_name
        ]
    )

    # 중복 제거
    df = df.drop_duplicates(
        subset=["date"]
    )

    # 날짜 정렬
    df = df.sort_values("date")

    return df


# =========================================================
# 5. 실행
# =========================================================

def main():

    print("\n" + "=" * 60)
    print("Bond Dashboard - ECOS DATA COLLECTION")
    print("=" * 60)

    print("\nECOS API KEY 로드 성공 ✅")


    # =====================================================
    # 6. 기준금리
    # =====================================================

    base_rate = collect_ecos_series(
        stat_code="722Y001",
        item_code="0101000",
        cycle="D",
        start_date=DAILY_START,
        end_date=DAILY_END,
        column_name="base_rate",
        raw_file_name="base_rate_raw.csv"
    )


    # =====================================================
    # 7. 국고채 3년
    # =====================================================

    treasury_3y = collect_ecos_series(
        stat_code="817Y002",
        item_code="010200000",
        cycle="D",
        start_date=DAILY_START,
        end_date=DAILY_END,
        column_name="treasury_3y",
        raw_file_name="treasury_3y_raw.csv"
    )


    # =====================================================
    # 8. 국고채 5년
    # =====================================================

    treasury_5y = collect_ecos_series(
        stat_code="817Y002",
        item_code="010200001",
        cycle="D",
        start_date=DAILY_START,
        end_date=DAILY_END,
        column_name="treasury_5y",
        raw_file_name="treasury_5y_raw.csv"
    )


    # =====================================================
    # 9. 국고채 10년
    # =====================================================

    treasury_10y = collect_ecos_series(
        stat_code="817Y002",
        item_code="010210000",
        cycle="D",
        start_date=DAILY_START,
        end_date=DAILY_END,
        column_name="treasury_10y",
        raw_file_name="treasury_10y_raw.csv"
    )


    # =====================================================
    # 10. 회사채 AA- 3년
    # =====================================================

    corporate_aa_3y = collect_ecos_series(
        stat_code="817Y002",
        item_code="010300000",
        cycle="D",
        start_date=DAILY_START,
        end_date=DAILY_END,
        column_name="corporate_aa_3y",
        raw_file_name="corporate_aa_3y_raw.csv"
    )


    # =====================================================
    # 11. CPI 총지수
    # STAT_CODE = 901Y009
    # ITEM_CODE = 0
    # CYCLE = M
    # =====================================================

    cpi = collect_ecos_series(
        stat_code="901Y009",
        item_code="0",
        cycle="M",
        start_date=MONTHLY_START,
        end_date=MONTHLY_END,
        column_name="cpi",
        raw_file_name="cpi_raw.csv"
    )


    # =====================================================
    # 12. 시장금리 데이터 병합
    # =====================================================

    print("\n" + "=" * 60)
    print("시장금리 데이터 병합")
    print("=" * 60)

    market_df = treasury_3y.merge(
        treasury_5y,
        on="date",
        how="outer"
    )

    market_df = market_df.merge(
        treasury_10y,
        on="date",
        how="outer"
    )

    market_df = market_df.merge(
        corporate_aa_3y,
        on="date",
        how="outer"
    )

    market_df = market_df.merge(
        base_rate,
        on="date",
        how="outer"
    )

    market_df = market_df.sort_values("date")


    # =====================================================
    # 13. 기준금리 보간
    # =====================================================

    # 기준금리는 변경 전까지 유지
    market_df["base_rate"] = (
        market_df["base_rate"]
        .ffill()
    )


    # =====================================================
    # 14. Spread 계산
    # =====================================================

    # Yield Spread
    market_df["yield_spread"] = (
        market_df["treasury_10y"]
        -
        market_df["treasury_3y"]
    )

    # Credit Spread
    market_df["credit_spread"] = (
        market_df["corporate_aa_3y"]
        -
        market_df["treasury_3y"]
    )

    # Policy Spread
    market_df["policy_spread"] = (
        market_df["treasury_3y"]
        -
        market_df["base_rate"]
    )


    # =====================================================
    # 15. 불필요한 빈 행 제거
    # =====================================================

    market_df = market_df.dropna(
        subset=[
            "treasury_3y",
            "treasury_5y",
            "treasury_10y",
            "corporate_aa_3y"
        ],
        how="all"
    )


    # =====================================================
    # 16. Processed 시장금리 CSV 저장
    # =====================================================

    market_output = (
        PROCESSED_DIR
        / "market_rates_daily.csv"
    )

    market_df.to_csv(
        market_output,
        index=False,
        encoding="utf-8-sig"
    )


    # =====================================================
    # 17. Processed CPI CSV 저장
    # =====================================================

    cpi_output = (
        PROCESSED_DIR
        / "cpi_monthly.csv"
    )

    cpi.to_csv(
        cpi_output,
        index=False,
        encoding="utf-8-sig"
    )


    # =====================================================
    # 18. 결과 출력
    # =====================================================

    print("\n" + "=" * 60)
    print("✅ ECOS 데이터 수집 및 정제 완료")
    print("=" * 60)

    print("\nRAW 파일")

    print(
        """
data/raw/ecos/
├── base_rate_raw.csv
├── treasury_3y_raw.csv
├── treasury_5y_raw.csv
├── treasury_10y_raw.csv
├── corporate_aa_3y_raw.csv
└── cpi_raw.csv
"""
    )

    print("Processed 파일")

    print(
        """
data/processed/
├── market_rates_daily.csv
└── cpi_monthly.csv
"""
    )

    print("시장금리 최종 컬럼:")

    print(
        market_df.columns.tolist()
    )

    print("\n시장금리 데이터 수:")

    print(
        f"{len(market_df):,}건"
    )

    print("\nCPI 데이터 수:")

    print(
        f"{len(cpi):,}건"
    )

    print("\n시장금리 앞 5개:")

    print(
        market_df.head()
    )

    print("\nCPI 앞 5개:")

    print(
        cpi.head()
    )

    print("\n시장금리 결측값:")

    print(
        market_df.isna().sum()
    )

    print("\nCPI 결측값:")

    print(
        cpi.isna().sum()
    )


# =========================================================
# 19. 프로그램 실행
# =========================================================

if __name__ == "__main__":
    main()