import os
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv


# =========================================================
# 1. 프로젝트 경로
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_PATH = PROJECT_ROOT / ".env"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "bond_market"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. API KEY
# =========================================================

load_dotenv(ENV_PATH, override=True)

raw_api_key = os.getenv("FSC_API_KEY")

if not raw_api_key:
    raise ValueError(
        "FSC_API_KEY가 없습니다.\n"
        ".env 파일을 확인해주세요."
    )


# 공공데이터포털 Encoding Key를 넣었더라도 자동 디코딩
API_KEY = raw_api_key.strip()

for _ in range(3):
    decoded = unquote(API_KEY)

    if decoded == API_KEY:
        break

    API_KEY = decoded


# =========================================================
# 3. API 설정
# =========================================================

BASE_URL = (
    "https://apis.data.go.kr/"
    "1160100/service/"
    "GetBondSecuritiesInfoService/"
    "getBondPriceInfo"
)


# =========================================================
# 4. 최근 영업일 후보 만들기
# =========================================================

def get_date_candidates(days=10):

    today = datetime.now()

    candidates = []

    for i in range(days):

        dt = today - timedelta(days=i)

        # 토/일 제외
        if dt.weekday() < 5:
            candidates.append(
                dt.strftime("%Y%m%d")
            )

    return candidates


# =========================================================
# 5. API 요청
# =========================================================

def request_market_data(
    bas_dt,
    page_no=1,
    num_rows=1000
):

    params = {
        "serviceKey": API_KEY,
        "resultType": "json",
        "pageNo": page_no,
        "numOfRows": num_rows,
        "basDt": bas_dt,
    }

    print(
        f"기준일={bas_dt} / "
        f"page={page_no}"
    )

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=60
    )

    print(
        "HTTP:",
        response.status_code
    )

    if response.status_code != 200:

        print("\n===== API 오류 응답 =====")
        print(response.text[:2000])
        print("========================")

        response.raise_for_status()

    return response.json()


# =========================================================
# 6. ITEM 추출
# =========================================================

def extract_items(data):

    response = data.get(
        "response",
        {}
    )

    header = response.get(
        "header",
        {}
    )

    body = response.get(
        "body",
        {}
    )

    print(
        "resultCode:",
        header.get("resultCode")
    )

    print(
        "resultMsg:",
        header.get("resultMsg")
    )

    items = body.get(
        "items",
        {}
    )

    if isinstance(items, dict):
        items = items.get(
            "item",
            []
        )

    if items is None:
        return []

    if isinstance(items, dict):
        return [items]

    return items


# =========================================================
# 7. 실제 데이터가 있는 최근 기준일 찾기
# =========================================================

def find_latest_available_date():

    print("\n" + "=" * 60)
    print("최근 채권시세 기준일 탐색")
    print("=" * 60)

    for bas_dt in get_date_candidates(10):

        try:

            data = request_market_data(
                bas_dt=bas_dt,
                page_no=1,
                num_rows=10
            )

            items = extract_items(
                data
            )

            if items:

                print(
                    f"✅ 데이터 존재 기준일: {bas_dt}"
                )

                return bas_dt

        except Exception as e:

            print(
                f"⚠ {bas_dt} 조회 실패: {e}"
            )

    raise RuntimeError(
        "최근 10일 내 채권시세 데이터를 찾지 못했습니다."
    )


# =========================================================
# 8. 전체 페이지 수집
# =========================================================

def collect_all_market_data(
    bas_dt
):

    print("\n" + "=" * 60)
    print("채권 시세 전체 수집")
    print("=" * 60)

    num_rows = 1000

    first = request_market_data(
        bas_dt=bas_dt,
        page_no=1,
        num_rows=num_rows
    )

    response = first.get(
        "response",
        {}
    )

    body = response.get(
        "body",
        {}
    )

    total_count = int(
        body.get(
            "totalCount",
            0
        )
    )

    print(
        f"총 데이터 수: {total_count:,}"
    )

    first_items = extract_items(
        first
    )

    if not first_items:

        raise RuntimeError(
            "첫 페이지에 데이터가 없습니다."
        )

    all_items = list(
        first_items
    )

    total_pages = (
        total_count
        + num_rows
        - 1
    ) // num_rows

    print(
        f"총 페이지 수: {total_pages}"
    )

    for page in range(
        2,
        total_pages + 1
    ):

        data = request_market_data(
            bas_dt=bas_dt,
            page_no=page,
            num_rows=num_rows
        )

        items = extract_items(
            data
        )

        all_items.extend(
            items
        )

    return pd.DataFrame(
        all_items
    )


# =========================================================
# 9. RAW 저장
# =========================================================

def save_raw(df):

    raw_path = (
        RAW_DIR
        / "bond_market_raw.csv"
    )

    df.to_csv(
        raw_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n✅ RAW 저장 완료")
    print(raw_path)

    print(
        f"RAW 행 수: {len(df):,}"
    )


# =========================================================
# 10. 정제
# =========================================================

def clean_market_data(df):

    print("\n" + "=" * 60)
    print("채권 시세 정제")
    print("=" * 60)

    # 우리가 현재 대시보드에서 사용할 컬럼
    wanted_columns = {

        "basDt": "date",
        "srtnCd": "short_code",
        "isinCd": "isin_code",
        "itmsNm": "bond_name",
        "mrktCtg": "market_type",

        "clprPrc": "close_price",
        "clprVs": "close_change",
        "clprBnfRt": "close_yield",

        "mkpPrc": "open_price",
        "mkpBnfRt": "open_yield",

        "hiprPrc": "high_price",
        "hiprBnfRt": "high_yield",

        "loprPrc": "low_price",
        "loprBnfRt": "low_yield",

        "trqu": "volume",
        "trPrc": "trading_value",
    }

    available = {
        old: new
        for old, new
        in wanted_columns.items()
        if old in df.columns
    }

    clean_df = (
        df[list(available.keys())]
        .copy()
        .rename(columns=available)
    )

    # -----------------------------------------------------
    # 날짜
    # -----------------------------------------------------

    if "date" in clean_df.columns:

        clean_df["date"] = pd.to_datetime(
            clean_df["date"],
            format="%Y%m%d",
            errors="coerce"
        )


    # -----------------------------------------------------
    # 숫자형
    # -----------------------------------------------------

    numeric_columns = [
        "close_price",
        "close_change",
        "close_yield",
        "open_price",
        "open_yield",
        "high_price",
        "high_yield",
        "low_price",
        "low_yield",
        "volume",
        "trading_value",
    ]

    for col in numeric_columns:

        if col in clean_df.columns:

            clean_df[col] = pd.to_numeric(
                clean_df[col],
                errors="coerce"
            )


    # -----------------------------------------------------
    # 문자열 공백 제거
    # -----------------------------------------------------

    text_columns = [
        "short_code",
        "isin_code",
        "bond_name",
        "market_type",
    ]

    for col in text_columns:

        if col in clean_df.columns:

            clean_df[col] = (
                clean_df[col]
                .astype(str)
                .str.strip()
            )


    # -----------------------------------------------------
    # 중복 제거
    # -----------------------------------------------------

    duplicate_keys = [
        col
        for col in [
            "date",
            "isin_code",
            "market_type"
        ]
        if col in clean_df.columns
    ]

    if duplicate_keys:

        clean_df = clean_df.drop_duplicates(
            subset=duplicate_keys
        )


    # -----------------------------------------------------
    # ISIN 없는 행 제거
    # -----------------------------------------------------

    if "isin_code" in clean_df.columns:

        clean_df = clean_df[
            clean_df["isin_code"].notna()
            &
            (clean_df["isin_code"] != "")
            &
            (clean_df["isin_code"] != "nan")
        ]


    # -----------------------------------------------------
    # 정렬
    # -----------------------------------------------------

    sort_columns = [
        col
        for col in [
            "date",
            "isin_code"
        ]
        if col in clean_df.columns
    ]

    if sort_columns:

        clean_df = clean_df.sort_values(
            sort_columns
        )

    return clean_df


# =========================================================
# 11. Processed 저장
# =========================================================

def save_processed(df):

    output_path = (
        PROCESSED_DIR
        / "bond_market.csv"
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n✅ 정제 CSV 저장 완료")
    print(output_path)

    print(
        f"정제 데이터 수: {len(df):,}"
    )


# =========================================================
# 12. 품질 확인
# =========================================================

def check_quality(df):

    print("\n" + "=" * 60)
    print("데이터 품질 확인")
    print("=" * 60)

    print(
        "\n컬럼:"
    )

    print(
        df.columns.tolist()
    )

    print(
        "\n결측값:"
    )

    print(
        df.isna().sum()
    )

    print(
        "\n중복 행:"
    )

    print(
        df.duplicated().sum()
    )

    print(
        "\n앞 5개:"
    )

    print(
        df.head()
    )


# =========================================================
# 13. MAIN
# =========================================================

def main():

    print("\n" + "=" * 60)
    print("Bond Dashboard - Bond Market Collector")
    print("=" * 60)

    print(
        "API KEY 로드 성공 ✅"
    )

    # 1. 최근 데이터 날짜 검색
    bas_dt = find_latest_available_date()

    # 2. 전체 데이터 수집
    raw_df = collect_all_market_data(
        bas_dt
    )

    # 3. RAW 저장
    save_raw(
        raw_df
    )

    # 4. 정제
    clean_df = clean_market_data(
        raw_df
    )

    # 5. 정제본 저장
    save_processed(
        clean_df
    )

    # 6. 품질 확인
    check_quality(
        clean_df
    )

    print("\n" + "=" * 60)
    print("✅ 채권 시세 데이터 수집 + 정제 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()