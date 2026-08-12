# Bond Insight — System Architecture

## 1. Architecture Overview

Bond Insight는 금융 데이터를 직접 수집하고 정제한 뒤,
분석 결과를 Database에 저장하고 FastAPI를 통해 웹서비스에 제공하는 구조로 개발한다.

Tableau는 금융 데이터 시각화를 담당하며 Next.js 웹사이트 내부에 Embed한다.

AI는 금융지표를 직접 계산하지 않고,
Backend에서 검증된 데이터를 전달받아 설명하는 역할을 담당한다.

---

## 2. Overall Architecture
'''

                    External Data Sources
                             │
                ┌────────────┴────────────┐
                │                         │
          한국은행 ECOS          금융위원회 / 공공데이터
                │                         │
                └────────────┬────────────┘
                             │
                             ▼
                    Data Collection
                  Python + Requests
                             │
                             ▼
                         Raw Data
                             │
                             ▼
                    Data Processing
                       Pandas
                             │
                ┌────────────┴────────────┐
                │                         │
           Data Cleaning           Data Integration
                │                         │
                └────────────┬────────────┘
                             ▼
                    Financial Analysis
                             │
                             ▼
                       Final Dataset
                             │
                 ┌───────────┴───────────┐
                 │                       │
                 ▼                       ▼
        Supabase PostgreSQL          Tableau
                 │                  Dashboard
                 │                       │
                 ▼                       │
              FastAPI                    │
                 │                       │
                 ├───────────────────────┘
                 │
                 ▼
          Next.js + React
                 │
       ┌─────────┼─────────┐
       │         │         │
       ▼         ▼         ▼
    탐색/상세    비교     AI 설명
                           │
                           ▼
                          LLM
'''

---

## 3. Data Collection Layer

### 역할

외부 금융기관 API에서 프로젝트에 필요한 데이터를 직접 수집한다.

### Data Sources

#### 한국은행 ECOS

수집 대상:

- 한국은행 기준금리
- 국고채 시장금리
- 회사채 시장금리
- CPI

#### 금융위원회 / 공공데이터포털

수집 대상:

- 채권 기본정보
- 채권 발행정보
- 채권 시장정보
- 채권 거래정보

#### 한국투자증권 Open API

기존 데이터 Source에서 필요한 데이터를 확보하지 못한 경우
보완 Source로 활용한다.

### 기술

- Python
- Requests

### 코드 위치

```text
src/
└── collection/
```

### 데이터 저장

수집된 원본 데이터는:

```text
data/
└── raw/
```

에 저장한다.

---

## 4. Data Processing Layer

### 역할

Raw Data를 분석 및 서비스에서 사용할 수 있는 형태로 변환한다.

### 처리 과정

```text
Raw Data
    ↓
필요 컬럼 선정
    ↓
컬럼명 통일
    ↓
Data Type 변환
    ↓
결측값 확인
    ↓
중복 확인
    ↓
이상값 확인
    ↓
Dataset 통합
```

### 기술

- Python
- Pandas

### 코드 위치

```text
src/
└── processing/
```

### 처리 데이터 저장

```text
data/
└── processed/
```

---

## 5. Data Integration

개별 채권 데이터는 가능한 경우 ISIN을 핵심 식별자로 사용한다.

기본 구조:

```text
bond_info
     │
     │ ISIN
     │
     ▼
bond_market
     │
     ▼
Integrated Bond Dataset
```

JOIN 이후 다음 항목을 검증한다.

- 전체 채권 수
- JOIN 성공 건수
- JOIN 실패 건수
- 중복 ISIN
- 결측값
- 데이터 타입

단순히 JOIN이 실행됐다는 이유만으로 데이터 통합이 성공했다고 판단하지 않는다.

---

## 6. Financial Analysis Layer

### 역할

정제된 금융 데이터에서 서비스와 Tableau에서 사용할 분석지표를 생성한다.

### 현재 생성된 파생지표

```text
Yield Spread
= 국고채 10년 - 국고채 3년

Credit Spread
= 회사채 AA- 3년 - 국고채 3년

Policy Spread
= 국고채 3년 - 한국은행 기준금리
```

### 향후 생성 예정

- Remaining Maturity
- Maturity Bucket
- Duration
- Individual Credit Spread
- Risk / Return Indicator

아직 계산하지 않은 지표는 실제 데이터 검증 후 구현한다.

### 코드 위치

```text
src/
└── analysis/
```

---

## 7. Database Layer

### Database

**Supabase PostgreSQL**

최종 테이블 구조와 Mermaid ERD는 [`docs/database-erd.md`](database-erd.md)를 기준으로 한다.

정제 및 분석이 완료된 서비스용 데이터를 저장한다.

Raw Data 전체를 Database에 저장하는 것을 기본 원칙으로 하지 않는다.

```text
data/raw
   ↓
Python / Pandas
   ↓
data/processed
   ↓
Supabase PostgreSQL
```

### 예상 테이블

```text
bonds
bond_market
market_rates
macro_indicators
bond_metrics
```

실제 Schema는 데이터 정제 완료 후 확정한다.

### 기본 관계

```text
bonds
  │
  │ ISIN
  │
  ├──────── bond_market
  │
  └──────── bond_metrics


market_rates
     │
     └── 시장금리 / Spread


macro_indicators
     │
     └── 기준금리 / CPI
```

---

## 8. Backend Layer

### Framework

**FastAPI**

Backend는 Database와 Frontend 사이의 Service Layer 역할을 담당한다.

### 구조

```text
Supabase PostgreSQL
        ↓
     FastAPI
        ↓
     REST API
        ↓
      Next.js
```

### 주요 역할

- Database 조회
- 채권 검색
- 채권 필터링
- 개별 채권 조회
- 채권 비교
- 시장정보 제공
- 분석지표 제공
- AI Context 생성
- 입력값 검증
- 오류 처리

### 예상 Endpoint

```text
GET  /api/market

GET  /api/bonds

GET  /api/bonds/{isin}

GET  /api/bonds/compare

GET  /api/analysis

POST /api/ai/explain
```

Endpoint의 상세 Request / Response 구조는
`docs/api_spec.md`에서 정의한다.

### 코드 위치

```text
backend/
└── app/
    ├── api/
    ├── models/
    ├── schemas/
    ├── services/
    └── ai/
```

---

## 9. Frontend Layer

### Framework

**Next.js + React**

전체 사용자 Interface를 담당한다.

### 주요 화면

```text
Home
│
├── Market Overview
├── Bond Explorer
├── Bond Detail
├── Bond Comparison
└── AI Explanation
```

### 데이터 연결

일반적인 서비스 데이터는 FastAPI를 통해 가져온다.

```text
Next.js
    ↕
FastAPI
    ↕
Supabase PostgreSQL
```

Frontend에서 Database를 직접 조회하는 구조보다
FastAPI를 Service Layer로 사용하는 것을 기본 구조로 한다.

---

## 10. Tableau Architecture

Tableau는 금융 분석 Dashboard를 담당한다.

### 역할

- 금리 추이
- Yield Curve
- Yield Spread
- Credit Spread
- Policy Spread
- Risk / Return 분석

### Web Integration

Tableau Dashboard를 Next.js 내부에 Embed한다.

```text
Processed Financial Data
          ↓
       Tableau
          ↓
      Dashboard
          ↓
Tableau Embedding API
          ↓
       Next.js
```

따라서 사용자는 Bond Insight 웹사이트를 벗어나지 않고
Tableau 시각화를 확인할 수 있도록 구성한다.

---

## 11. AI Architecture

AI의 역할은 **계산이 아니라 설명**이다.

### 데이터 Flow

```text
Supabase
    ↓
FastAPI
    ↓
Financial Data
    +
Calculated Indicators
    ↓
Structured AI Context
    ↓
LLM
    ↓
AI Explanation
    ↓
FastAPI
    ↓
Next.js
```

### 원칙

AI에게 Raw Data 전체를 그대로 전달하지 않는다.

Backend에서 필요한 데이터만 구조화하여 전달한다.

예:

```text
채권명
수익률
표면금리
잔존만기
신용등급
Credit Spread
Duration
시장금리
```

AI는 전달된 데이터를 기반으로:

- 채권 특징
- 수익 구조
- 주요 위험
- 비교 결과
- 금융용어

등을 설명한다.

---

## 12. Tableau MCP

Tableau MCP는 MVP Architecture에 포함하지 않는다.

현재 기본 구조는:

```text
Tableau
    ↓
Embedding API
    ↓
Next.js
```

으로 구성한다.

개발 완료 후 추가적인 AI 분석 기능이 필요할 경우:

```text
Tableau
    ↕
Tableau MCP
    ↕
AI
```

구조를 확장 기능으로 검토한다.

---

## 13. Security

API Key 및 Secret은 Source Code에 직접 작성하지 않는다.

```text
.env
```

파일에서 관리한다.

GitHub에는 실제 Secret을 업로드하지 않고:

```text
.env.example
```

파일에 필요한 환경변수 이름만 기록한다.

예:

```env
ECOS_API_KEY=
DATA_GO_KR_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
LLM_API_KEY=
```

`.env`는 `.gitignore`를 통해 Git 추적에서 제외한다.

---

## 14. Development Architecture

팀 개발 시 데이터 파이프라인이 먼저 확정된 후
각 영역을 병렬로 개발한다.

```text
                 Final Dataset
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
      Database      Tableau       Analysis
         │
         ▼
      FastAPI
         │
    ┌────┴─────┐
    ▼          ▼
Frontend       AI
```

### 개발 의존 관계

```text
Data Collection
      ↓
Data Processing
      ↓
Final Dataset
      ↓
Database Schema
      ↓
FastAPI
      ↓
Frontend
```

Tableau 분석은 Processed Data가 확보되면
Backend 개발과 병렬로 진행할 수 있다.

AI 기능은 FastAPI에서 제공할 데이터 구조가 확정된 이후 연결한다.

---

## 15. Architecture Principles

### 1. Raw Data 보존

API에서 수집한 원본과 정제 데이터를 분리한다.

### 2. 계산과 AI 분리

금융지표는 Python 또는 Backend에서 계산하고,
AI는 계산 결과를 설명한다.

### 3. Frontend와 Database 분리

Frontend가 Database에 직접 의존하지 않고
FastAPI를 통해 서비스 데이터를 제공받는다.

### 4. Tableau 역할 분리

Tableau는 금융 데이터 분석 및 시각화를 담당하고,
웹서비스 UI와 사용자 기능은 Next.js가 담당한다.

### 5. 재현 가능한 Data Pipeline

```text
API
→ Raw
→ Processing
→ Analysis
→ Final Dataset
→ Database
```

흐름을 코드로 관리하여 동일한 데이터 처리 과정을 다시 실행할 수 있도록 한다.
