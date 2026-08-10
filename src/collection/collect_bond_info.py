import os
from pathlib import Path
from urllib.parse import unquote

import pandas as pd
import requests
from dotenv import load_dotenv


# =========================================================
# 1. 프로젝트 경로
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_PATH = PROJECT_ROOT / ".env"

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "bond_info"

RAW_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# 2. .env 불러오기
# =========================================================

# 기존 환경변수보다 .env 값을 우선 사용
load_dotenv(
    ENV_PATH,
    override=True
)

raw_api_key = os.getenv("BOND_INFO_API_KEY")

if not raw_api_key:
    raise ValueError(
        "BOND_INFO_API_KEY가 없습니다. "
        ".env 파일을 확인해주세요."
    )


# =========================================================
# 3. 인증키 디코딩
# =========================================================
#
# Encoding 키를 .env에 넣었더라도
# 코드에서 Decoding 형태로 변환
#

API_KEY = raw_api_key.strip()

for _ in range(3):

    decoded = unquote(API_KEY)

    if decoded == API_KEY:
        break

    API_KEY = decoded


print("=" * 60)
print("채권 기본정보 Collector")
print("=" * 60)

print("API KEY 로드 성공 ✅")

# 실제 키는 출력하지 않음
print(
    "키 길이:",
    len(API_KEY)
)


# =========================================================
# 4. API URL
# =========================================================

BASE_URL = (
    "https://apis.data.go.kr/"
    "1160100/"
    "GetBondIssuInfoService_V2/"
    "getBondBasiInfo_V2"
)


# =========================================================
# 5. API 요청
# =========================================================

def request_bond_info(
    page_no=1,
    num_rows=100
):

    params = {
        "serviceKey": API_KEY,
        "resultType": "json",
        "pageNo": page_no,
        "numOfRows": num_rows,

        # basDt를 입력하지 않으면
        # API에서 가장 최근 기준일자를 사용
    }

    print(
        f"\npage={page_no} 요청 중..."
    )

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=60
    )

    print(
        "HTTP 상태코드:",
        response.status_code
    )

    # -----------------------------------------------------
    # 오류일 경우 응답 내용 출력
    # -----------------------------------------------------

    if response.status_code != 200:

        print("\n===== API 오류 응답 =====")

        print(
            response.text[:3000]
        )

        print("========================")

        response.raise_for_status()

    return response.json()


# =========================================================
# 6. items 추출
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
# 7. 전체 데이터 수집
# =========================================================

def collect_all():

    print("\n" + "=" * 60)
    print("채권 기본정보 API 수집 시작")
    print("=" * 60)

    # -----------------------------------------------------
    # 첫 번째 요청
    # -----------------------------------------------------

    first = request_bond_info(
        page_no=1,
        num_rows=100
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
        f"\n총 데이터 수: {total_count:,}"
    )

    first_items = extract_items(
        first
    )

    if not first_items:

        print(
            "⚠ 첫 페이지 데이터가 없습니다."
        )

        return pd.DataFrame()

    all_items = list(
        first_items
    )

    # -----------------------------------------------------
    # 전체 페이지 계산
    # -----------------------------------------------------

    num_rows = 100

    total_pages = (
        total_count
        + num_rows
        - 1
    ) // num_rows

    print(
        f"총 페이지 수: {total_pages:,}"
    )

    # -----------------------------------------------------
    # 나머지 페이지 수집
    # -----------------------------------------------------

    for page in range(
        2,
        total_pages + 1
    ):

        data = request_bond_info(
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
# 8. CSV 저장
# =========================================================

def save_csv(df):

    if df.empty:

        print(
            "⚠ 저장할 데이터가 없습니다."
        )

        return

    output_path = (
        RAW_DIR
        / "bond_info_raw.csv"
    )

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n" + "=" * 60)

    print(
        "✅ bond_info_raw.csv 생성 완료"
    )

    print("=" * 60)

    print(
        "저장 위치:"
    )

    print(
        output_path
    )

    print(
        f"\n데이터 수: {len(df):,}"
    )

    print("\n컬럼:")

    print(
        df.columns.tolist()
    )

    print("\n앞 5개:")

    print(
        df.head()
    )


# =========================================================
# 9. MAIN
# =========================================================

def main():

    df = collect_all()

    save_csv(df)


if __name__ == "__main__":
    main()