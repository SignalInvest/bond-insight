# Bond Insight 데이터 및 데이터베이스

이 폴더는 외부 API에서 수집한 원본 데이터와 분석·화면용 가공 데이터를 보관합니다. 운영 데이터베이스는 Supabase PostgreSQL을 사용합니다.

## 데이터 흐름

```text
ECOS / 채권 정보 API / 채권 시세 API
                ↓
data/raw              원본 보존
                ↓
src/processing        정제·통합
                ↓
src/analysis          파생지표 계산
                ↓
data/processed        분석 및 화면용 CSV
                ↓
src/loading           Supabase 적재
```

## 폴더 구조

```text
data/
├── raw/
│   ├── bond_info/    # 채권 기본정보 원본
│   ├── bond_market/  # 채권 시세 원본
│   └── ecos/         # 기준금리·국고채·회사채·CPI 원본
└── processed/        # 정제·통합·파생 데이터
```

## 주요 가공 파일

| 파일 | 설명 |
|---|---|
| `market_rates_daily.csv` | 날짜별 기준금리·국고채·회사채 금리와 Spread |
| `market_rates_2026-08-01_07.csv` | 현재 화면의 시장 개요용 고정 기간 데이터 |
| `bond_maturity.csv` | 잔존일수·잔존연수·만기 구간 |
| `bond_duration.csv` | Macaulay 및 Modified Duration |
| `bond_credit_spread.csv` | 개별 채권의 비교 국고채 금리와 신용스프레드 |
| `bond_after_tax_yield.csv` | 세후 예상수익률 근사값 |
| `bond_duration_sensitivity.csv` | 듀레이션 기반 금리 민감도 분류 |
| `bond_investment_priority.csv` | 안정성·균형·수익률 중심 분류 |
| `tableau_bond_dashboard.csv` | 현재 프론트엔드와 Tableau가 사용하는 통합 데이터 |

## Supabase 테이블

| 테이블 | 역할 | 주요 키 |
|---|---|---|
| `bonds` | 채권 기본정보 | `isin_code` |
| `bond_market` | 날짜별 개별 채권 가격·YTM·거래 정보 | `(isin_code, reference_date)` |
| `bond_metrics` | 잔존만기와 듀레이션 | `isin_code` |
| `market_rates` | 날짜별 기준금리·국고채·회사채 금리 | `reference_date` |
| `bond_snapshot` | 화면용 통합 채권 스냅샷 | `(isin_code, reference_date)` |

2026-08-13 정리 기준으로 `bond_snapshot`은 듀레이션 값이 있는 275행만 유지하며, `modified_duration` 누락 행은 없습니다.

상세 ERD와 컬럼 정의는 다음 문서를 참고합니다.

- `docs/database-erd.md`
- `docs/data_dictionary.md`
- `docs/sql/bond_snapshot.sql`

## Supabase 적재

루트 `.env`에 `SUPABASE_URL`과 백엔드 전용 `SUPABASE_KEY`를 설정한 뒤 프로젝트 루트에서 실행합니다.

```powershell
python -u src\loading\upload_supabase.py --table all
```

테이블별 적재:

```powershell
python -u src\loading\upload_supabase.py --table bonds
python -u src\loading\upload_supabase.py --table market_rates
python -u src\loading\upload_supabase.py --table bond_market
python -u src\loading\upload_supabase.py --table bond_metrics
python -u src\loading\upload_bond_snapshot.py
python -u src\loading\upload_cpi.py
```

적재 스크립트는 대체로 고유키 기준 `upsert` 또는 신규 기준일만 `insert`합니다. 실행 전 대상 파일과 기준일을 반드시 확인하세요.

## 정적 화면과 Supabase의 차이

- 현재 메인 웹 화면은 `tableau_bond_dashboard.csv`를 직접 읽습니다.
- Supabase `bond_snapshot`을 수정해도 현재 화면에는 자동 반영되지 않습니다.
- 화면과 DB를 동일하게 유지하려면 CSV와 Supabase를 같은 필터 기준으로 갱신해야 합니다.
- 향후 동적 화면으로 전환할 경우 기존 `/api/bond-snapshot` 경로를 사용할 수 있습니다.

## 데이터 품질 원칙

- 원본 파일은 직접 수정하지 않고 `processed` 결과를 재생성합니다.
- 옵션부채권·영구채 등 일반 듀레이션 공식을 적용하기 어려운 채권에는 숫자를 임의로 채우지 않습니다.
- 기준일, 단위, 결측 사유를 함께 관리합니다.
- CSV 저장 인코딩은 `UTF-8 with BOM`을 기본으로 사용합니다.
- API 키와 Supabase Secret/Service Role 키는 데이터 파일이나 Git에 포함하지 않습니다.

