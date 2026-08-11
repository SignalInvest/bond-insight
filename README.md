# 📊 Bond Insight

> 금융 데이터를 직접 수집·가공하여 채권 시장과 개별 채권을 분석하고, 사용자가 채권의 수익과 위험을 쉽게 비교할 수 있도록 지원하는 채권 분석 플랫폼

---

## 1. Project Overview

채권 투자 초보자는 채권 정보를 찾을 수는 있지만 기준금리, 채권 수익률, 만기, 신용등급, 스프레드 등 여러 금융지표를 함께 이해해야 합니다.

또한 시장금리와 개별 채권 정보가 여러 기관에 분산되어 있어 데이터를 직접 비교하기 어렵습니다.

Bond Insight는 금융 데이터를 직접 수집하고 분석하여 다음과 같은 사용자 흐름을 제공하는 것을 목표로 합니다.

**시장 이해 → 채권 탐색 → 채권 상세 분석 → 채권 비교 → 위험 분석 → AI 설명 → 투자 판단 지원**

특정 채권의 매수·매도를 직접 추천하기보다는 사용자가 금융 데이터를 이해하고 스스로 판단할 수 있도록 지원하는 것을 목표로 합니다.

---

## 2. Target User

### 채권 투자 초보자

- 주식, ETF, 예·적금 등의 투자 경험이 있는 사용자
- 경제와 투자에 관심이 있는 사용자
- 개별 채권 투자 경험은 부족한 사용자
- 채권의 수익과 위험을 쉽게 비교하고 싶은 사용자
- YTM, Duration, Credit Spread 등의 금융지표가 익숙하지 않은 사용자

### 핵심 사용자 니즈

> 어떤 채권의 수익률이 높은지만 보는 것이 아니라, 왜 높은지와 그만큼 어떤 위험이 존재하는지도 쉽게 이해하고 싶다.

---

## 3. Core Features

### 📈 Market Overview

채권 투자 판단에 필요한 시장 환경을 제공합니다.

- 한국은행 기준금리
- 국고채 금리
- 회사채 금리
- CPI
- Yield Curve
- Yield Spread
- Credit Spread
- Policy Spread

### 🔍 Bond Explorer

수집한 개별 채권 데이터를 기반으로 조건별 채권 탐색 기능을 제공합니다.

### 📄 Bond Detail

선택한 채권의 발행정보와 시장정보를 한 화면에서 확인할 수 있도록 구성합니다.

### ⚖️ Bond Comparison

여러 채권의 수익률, 만기, 금리 및 위험 관련 지표를 비교할 수 있도록 구성합니다.

### 📊 Risk & Return Analysis

채권의 수익률만 보여주는 것이 아니라 수익과 위험의 관계를 분석합니다.

### 🤖 AI Explanation

최종적으로 계산된 금융 데이터를 AI가 사용자가 이해하기 쉬운 형태로 설명하도록 구현할 예정입니다.

AI가 금융지표를 직접 계산하는 것이 아니라,

**Python / Backend → 금융지표 계산**

**AI → 계산 결과 설명**

구조로 구현합니다.

---

## 4. Data Sources

### 한국은행 ECOS

시장금리 및 거시경제 데이터 수집에 사용합니다.

현재 수집 데이터:

- 한국은행 기준금리
- 국고채 3년
- 국고채 5년
- 국고채 10년
- 회사채 AA- 3년
- 소비자물가지수(CPI)

### 금융위원회 / 공공데이터포털

개별 채권 데이터를 직접 수집하는 데 사용합니다.

현재 채권 기본정보 및 시장정보 API를 활용하고 있습니다.

### 한국투자증권 Open API

API Key를 확보했으며, 기존 데이터에서 필요한 정보를 확보하지 못할 경우 보완 데이터 Source로 활용할 예정입니다.

---

## 5. Dataset

본 프로젝트에서는 외부 금융 API에서 데이터를 직접 수집하고,
수집한 Raw Data를 Python/Pandas를 이용하여 정제 및 분석합니다.

### 현재 생성된 주요 데이터

| 파일 | 구분 | 내용 |
|---|---|---|
| `bond_info_raw.csv` | 직접 수집 | 금융위원회 API에서 직접 수집한 개별 채권 기본정보 |
| `bond_market_raw.csv` | 직접 수집 | 금융위원회 API에서 직접 수집한 개별 채권 시장정보 |
| `base_rate_daily.csv` | 직접 수집 | 한국은행 ECOS에서 직접 수집한 일별 기준금리 |
| `market_rates_daily.csv` | 직접 수집 + 파생 | ECOS 시장금리 데이터를 수집하고 시장 분석용 Spread를 계산한 데이터 |
| `cpi_monthly.csv` | 직접 수집 | 한국은행 ECOS에서 직접 수집한 월별 소비자물가지수 |


---

## 6. Currently Derived Indicators

현재 실제로 생성한 파생지표만 기록합니다.

| 파생지표 | 계산 | 의미 |
|---|---|---|
| Yield Spread | 국고채 10년 - 국고채 3년 | 장단기 금리 차이 |
| Credit Spread | 회사채 AA- 3년 - 국고채 3년 | 국채 대비 회사채의 추가 금리 |
| Policy Spread | 국고채 3년 - 한국은행 기준금리 | 정책금리 대비 국고채 시장금리 차이 |

### 단위

- 원본 금리: `%`
- 금리 간 차이: `%p (percentage point)`

### 참고

`Policy Spread`는 표준화된 단일 시장지표를 그대로 가져온 것이 아니라,
본 프로젝트에서 정책금리와 국고채 3년 금리의 차이를 분석하기 위해 정의한 파생변수입니다.

---

## 7. Planned Derived Indicators

아래 지표들은 아직 최종 생성하지 않았으며,
데이터 정제 및 통합 이후 실제 확보된 컬럼을 기준으로 계산합니다.

| 파생지표 | 계획 |
|---|---|
| Remaining Maturity | 기준일과 만기일을 이용하여 잔존만기 계산 |
| Maturity Bucket | 잔존만기를 기준으로 단기·중기·장기 분류 |
| Duration | 필요한 채권 현금흐름 및 수익률 데이터 확보 후 계산 여부 결정 |
| Individual Credit Spread | 개별 회사채 수익률과 비교 가능한 국고채 금리를 이용하여 계산 검토 |
| Risk / Return Indicator | 최종 데이터셋을 기반으로 분석 방법 결정 |

아직 계산하지 않은 지표는 구현 완료 후 README에 추가합니다.

---

## 8. Data Pipeline

```text
Financial APIs
      │
      ├── 한국은행 ECOS
      ├── 금융위원회 / 공공데이터포털
      └── 한국투자증권 Open API
      │
      ▼
Python Data Collection
      │
      ▼
Raw CSV
      │
      ▼
Data Cleaning
      │
      ▼
Data Integration
      │
      ▼
Derived Indicators
      │
      ▼
Final Dataset
      │
      ▼
Database
      │
      ▼
FastAPI
      │
      ├─────────────┐
      ▼             ▼
  Frontend      AI Explanation

      +

   Tableau
Data Analysis / Visualization
```

---

## 9. Project Structure

```text
Bond-Dashboard/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── collection/
│   ├── processing/
│   └── analysis/
│
├── notebooks/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       └── ai/
│
├── frontend/
│
├── tableau/
│
├── tests/
│
├── docs/
│   ├── project-plan.md
│   ├── architecture.md
│   ├── data_dictionary.md
│   └── api_spec.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 10. Tech Stack

### Data Collection / Processing

- Python
- Pandas
- Requests

### Data Analysis

- Pandas
- NumPy
- Matplotlib
- Jupyter Notebook
- Tableau

### Backend

- FastAPI
- Pydantic
- SQLAlchemy

### Database

- PostgreSQL / Supabase 검토

### Frontend

- React / Next.js 검토

### AI

- LLM API
- FastAPI
- Structured Financial Data

---

## 11. MVP Goal

최종적으로 다음 사용자 흐름을 구현하는 것을 목표로 합니다.

```text
시장 상황 확인
      ↓
채권 탐색
      ↓
채권 상세 분석
      ↓
채권 비교
      ↓
위험·수익 분석
      ↓
AI 설명
      ↓
투자 판단 지원
```

---

## 12. Project Direction

Bond Insight는 단순히 금융 API 데이터를 시각화하는 Dashboard가 아니라,

**Financial Data → Data Engineering → Financial Analytics → Backend → Web Service → AI Explanation**

과정을 연결하는 End-to-End 금융 데이터 프로젝트를 목표로 합니다.