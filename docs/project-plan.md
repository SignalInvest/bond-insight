# Bond Insight — Project Plan

## 1. 프로젝트 목표

Bond Insight는 채권 투자 경험이 부족한 사용자가 시장 상황을 확인하고,
개별 채권의 수익성과 위험을 탐색·비교할 수 있도록 지원하는 채권 분석 플랫폼이다.

단순한 금융 데이터 시각화에서 끝나는 것이 아니라,

**데이터 수집 → 데이터 정제 → 금융 분석 → 데이터베이스 → Backend → Frontend → AI 설명**

까지 연결하는 End-to-End 금융 데이터 서비스를 목표로 한다.

---

# 2. 문제 정의

채권 투자자는 하나의 채권을 판단하기 위해 여러 정보를 함께 확인해야 한다.

- 기준금리
- 국고채 금리
- 회사채 금리
- 채권 가격
- 수익률
- 만기
- 신용등급
- 거래정보
- 금리위험
- 신용위험

하지만 이러한 정보는 여러 기관과 데이터에 분산되어 있으며,
채권 초보자가 각 지표의 의미와 관계를 이해하기 어렵다.

### 핵심 문제

> 채권 투자 초보자가 분산된 금융 데이터를 직접 찾아 비교하고,
> 채권의 수익과 위험을 함께 이해하기 어렵다.

---

# 3. Target User

## 채권 투자 초보자

### 특징

- 투자와 경제에 관심이 있음
- 주식, ETF, 예·적금 등의 투자 경험이 있음
- 개별 채권 투자 경험은 부족함
- 기준금리 등 기본적인 금융 개념은 알고 있음
- YTM, Duration, Credit Spread 등의 활용에는 익숙하지 않음

### 사용자 니즈

> 어떤 채권의 수익률이 높은지만 보는 것이 아니라,
> 왜 높은지와 어떤 위험이 존재하는지도 쉽게 이해하고 싶다.

---

# 4. 사용자 Flow

```text
시장 상황 확인
      ↓
채권 탐색
      ↓
채권 상세 확인
      ↓
채권 비교
      ↓
수익 / 위험 분석
      ↓
AI 설명
      ↓
투자 판단 지원
```

서비스는 특정 채권의 직접적인 매수·매도를 추천하기보다
사용자가 데이터를 이해하고 스스로 판단할 수 있도록 지원한다.

---

# 5. 핵심 기능

## 5.1 Market Overview

현재 채권시장의 금리 환경을 확인한다.

주요 데이터:

- 한국은행 기준금리
- 국고채 3년
- 국고채 5년
- 국고채 10년
- 회사채 AA- 3년
- CPI
- Yield Spread
- Credit Spread
- Policy Spread

---

## 5.2 Bond Explorer

수집된 개별 채권을 조건별로 탐색한다.

예상 필터:

- 채권 종류
- 발행기관
- 만기
- 잔존만기
- 표면금리
- 수익률
- 신용등급

실제 제공 가능한 필터는 데이터 정제 후 최종 컬럼을 기준으로 확정한다.

---

## 5.3 Bond Detail

선택한 개별 채권의 기본정보와 시장정보를 제공한다.

예상 정보:

- 채권명
- ISIN
- 발행기관
- 채권 종류
- 발행일
- 만기일
- 잔존만기
- 표면금리
- 시장가격
- 수익률
- 신용등급
- 거래정보

실제 API에서 확보 가능한 데이터 기준으로 최종 제공 항목을 결정한다.

---

## 5.4 Bond Comparison

사용자가 선택한 채권들을 동일한 기준으로 비교한다.

예상 비교 항목:

- 수익률
- 표면금리
- 잔존만기
- 신용등급
- 가격
- 거래량
- Credit Spread
- Duration

Duration과 개별 Credit Spread는 필요한 데이터가 확보된 경우에 구현한다.

---

## 5.5 Risk & Return Analysis

단순히 높은 수익률을 보여주는 것이 아니라,
수익률이 높은 이유와 함께 존재하는 위험을 분석한다.

분석 후보:

- 수익률 vs 잔존만기
- 수익률 vs 신용등급
- 수익률 vs Duration
- 신용등급별 수익률
- 만기별 수익률
- Credit Spread

실제 데이터 분포를 확인한 후 최종 분석 방법을 결정한다.

---

## 5.6 AI Explanation

AI는 계산된 금융 데이터를 사용자가 이해하기 쉬운 형태로 설명한다.

### 원칙

```text
Raw Data
    ↓
Python / Backend
    ↓
금융지표 계산
    ↓
AI
    ↓
자연어 설명
```

AI가 임의로 금융지표를 계산하거나 데이터를 생성하지 않는다.

AI 활용 예:

- 선택한 채권의 특징 설명
- 수익률이 높은 이유 설명
- 주요 위험요인 설명
- 두 채권의 차이 설명
- 금융용어 설명

직접적인 매수·매도 추천 기능은 MVP 범위에서 제외한다.

---

# 6. Data

## 6.1 데이터 Source

### 한국은행 ECOS

시장 환경 분석에 사용한다.

현재 확보:

- 기준금리
- 국고채 3년
- 국고채 5년
- 국고채 10년
- 회사채 AA- 3년
- CPI

### 금융위원회 / 공공데이터포털

개별 채권 분석에 사용한다.

현재 확보 또는 수집 중:

- 채권 기본정보
- 채권 시장정보
- 채권 발행정보
- 채권 거래정보

### 한국투자증권 Open API

현재 데이터에서 필요한 정보가 부족한 경우 보완적으로 사용한다.

추가 API는 필요한 데이터가 기존 Source에서 확보되지 않을 때만 사용한다.

---

# 7. Data Processing

수집한 Raw Data를 바로 서비스에서 사용하지 않고 정제 과정을 거친다.

## 기본 정제

- 필요한 컬럼 선정
- 컬럼명 통일
- 데이터 타입 변환
- 날짜 형식 통일
- 숫자형 변환
- 결측값 확인
- 중복 데이터 확인
- 이상값 확인

## 데이터 통합

개별 채권 데이터는 가능한 경우

`ISIN`

을 핵심 식별자로 사용하여 연결한다.

```text
bond_info
      +
bond_market
      ↓
ISIN JOIN
      ↓
Final Bond Dataset
```

JOIN 이후 연결되지 않은 데이터도 별도로 확인한다.

---

# 8. Derived Data

## 현재 생성 완료

| 지표 | 계산 |
|---|---|
| Yield Spread | 국고채 10년 - 국고채 3년 |
| Credit Spread | 회사채 AA- 3년 - 국고채 3년 |
| Policy Spread | 국고채 3년 - 한국은행 기준금리 |

## 데이터 정제 후 생성 예정

| 지표 | 계획 |
|---|---|
| Remaining Maturity | 만기일과 기준일을 이용하여 계산 |
| Maturity Bucket | 잔존만기를 구간화 |
| Duration | 필요한 입력 데이터 확보 여부 확인 후 계산 |
| Individual Credit Spread | 개별 채권 수익률과 비교 국고채 금리를 이용해 계산 검토 |
| Risk / Return Indicator | EDA 결과를 기반으로 결정 |

아직 계산하지 않은 지표는 실제 구현 완료 후 확정한다.

---

# 9. Tableau 활용

Tableau는 웹서비스 자체를 대체하는 Frontend가 아니라
금융 데이터 분석 및 시각화를 위한 도구로 활용한다.

분석 후보:

- 기준금리 추이
- 국고채 금리 추이
- Yield Curve
- Yield Spread
- Credit Spread
- 신용등급별 수익률
- 만기별 수익률
- Risk vs Return

Tableau 분석을 통해 최종 웹서비스에서 보여줄 핵심 지표와 시각화를 선정한다.

---

# 10. System Architecture

```text
Financial APIs
      ↓
Data Collection
      ↓
Raw Data
      ↓
Data Processing
      ↓
Financial Analysis
      ↓
Processed Data
      ↓
Database
      ↓
FastAPI
      ↓
Frontend
      ↓
User

Financial Analysis / Database
      ↓
AI
      ↓
AI Explanation

Processed Data
      ↓
Tableau
      ↓
EDA / Visualization
```

---
# 11. Tech Stack

Bond Insight는 금융 데이터 수집부터 분석, 시각화, 웹서비스, AI 설명까지 연결하는 End-to-End 구조로 개발한다.

---

## 11.1 Data Collection / Processing

### Python + Pandas + Requests

금융기관 API에서 데이터를 직접 수집하고 서비스에서 사용할 수 있도록 정제한다.

**주요 역할**

- 한국은행 ECOS API 데이터 수집
- 금융위원회 / 공공데이터포털 API 데이터 수집
- Raw Data 저장
- 필요한 컬럼 선정
- 데이터 타입 변환
- 결측값 및 중복 데이터 처리
- 데이터 통합
- 금융 파생지표 계산

**사용 기술**

- Python
- Pandas
- Requests
- Jupyter Notebook

---

## 11.2 Data Analysis

### Pandas + NumPy + Matplotlib

정제된 금융 데이터를 이용하여 채권시장 및 개별 채권을 분석한다.

**주요 분석**

- 기준금리 추이
- 국고채 금리 추이
- 회사채 금리 추이
- Yield Curve
- Yield Spread
- Credit Spread
- Policy Spread
- 만기별 분석
- Risk / Return 분석

**사용 기술**

- Pandas
- NumPy
- Matplotlib
- Jupyter Notebook

---

## 11.3 Visualization

### Tableau

금융시장과 채권 분석 결과를 Dashboard 형태로 시각화한다.

**주요 시각화**

- 기준금리 추이
- 국고채 금리 추이
- Yield Curve
- Yield Spread
- Credit Spread
- Policy Spread
- 만기별 채권 분석
- Risk / Return

Tableau는 전체 웹사이트를 제작하는 Frontend가 아니라
Bond Insight 내부의 금융 데이터 분석 및 시각화 영역을 담당한다.

### Tableau 웹 연동

완성된 Tableau Dashboard를 웹사이트 내부에 Embed하여 제공한다.

구조:

```text
Tableau Dashboard
        ↓
Tableau Embedding API
        ↓
Next.js
        ↓
Bond Insight Web
```

포트폴리오 MVP에서는 공개 가능한 데이터만 Tableau에 게시하여 활용한다.

---

## 11.4 Database

### Supabase (PostgreSQL)

Bond Insight의 서비스 Database로 Supabase를 사용한다.

Supabase는 PostgreSQL 기반 관리형 플랫폼으로,
Python에서 정제한 채권 및 금융시장 데이터를 저장한다.

**예상 저장 데이터**

- 채권 기본정보
- 채권 시장정보
- 시장금리
- 거시경제 데이터
- 계산된 금융지표

**예상 주요 테이블**

```text
bonds
bond_market
market_rates
macro_indicators
bond_metrics
```

실제 테이블 구조는 데이터 정제가 완료된 후 최종 Dataset을 기준으로 확정한다.

### 선택 이유

- PostgreSQL 기반 관계형 Database
- SQL 및 PK/FK 관계 설계 가능
- FastAPI와 연동 가능
- 별도의 PostgreSQL 서버 구축 부담 감소
- 팀원들이 동일한 Database에서 협업 가능
- 웹 기반 관리 기능 제공
- 향후 사용자 기능 확장 가능
- Auth / Storage / Realtime 기능을 필요할 경우 추가 활용 가능

### 데이터 저장 원칙

모든 Raw Data를 Database에 저장하지 않는다.

```text
API
 ↓
Raw CSV
(data/raw)
 ↓
Python / Pandas
 ↓
정제 및 분석
 ↓
Processed Data
 ↓
Supabase PostgreSQL
```

Raw Data는 재현성과 데이터 처리 과정 보존을 위해 별도로 관리하고,
서비스에 필요한 정제 데이터 중심으로 Database에 저장한다.

---

## 11.5 Backend

### FastAPI

FastAPI를 Bond Insight의 Backend API Server로 사용한다.

Database의 금융 데이터를 조회하고 분석 결과를 Frontend에 전달한다.

**주요 역할**

- 시장 데이터 조회
- 채권 목록 조회
- 개별 채권 조회
- 채권 검색
- 채권 필터링
- 채권 비교
- 금융 분석 결과 제공
- AI 기능 연결

### 기본 구조

```text
Supabase PostgreSQL
        ↓
     FastAPI
        ↓
      Next.js
```

### 예상 API

```text
/api/market
/api/bonds
/api/bonds/{isin}
/api/bonds/compare
/api/analysis
/api/ai
```

실제 Endpoint는 `docs/api_spec.md`에서 별도로 정의한다.

---

## 11.6 Frontend

### Next.js + React

Bond Insight의 전체 웹서비스 UI를 담당한다.

Next.js를 기반으로 서비스를 구성하고 React Component를 이용하여 화면을 개발한다.

**주요 화면**

```text
Home
│
├── Market Overview
│
├── Bond Explorer
│
├── Bond Detail
│
├── Bond Comparison
│
└── AI Explanation
```

### Market Overview

시장 분석 영역에서는 Tableau Dashboard를 웹사이트 내부에 Embed한다.

```text
Next.js

┌─────────────────────────────┐
│       Market Overview       │
│                             │
│     Tableau Dashboard       │
│                             │
│ Yield Curve                 │
│ Interest Rate               │
│ Spread Analysis             │
└─────────────────────────────┘
```

### 서비스 기능

채권 검색, 상세조회, 비교, AI 기능 등 사용자와 상호작용하는 기능은
Next.js에서 구현하고 FastAPI와 통신한다.

```text
Next.js
   ↕
FastAPI
   ↕
Supabase
```

---

## 11.7 AI

### LLM + FastAPI

AI는 채권 데이터를 직접 생성하거나 금융지표를 임의로 계산하지 않는다.

Python 및 Backend에서 계산된 데이터를 기반으로
사용자가 이해하기 쉬운 설명을 생성하는 역할을 담당한다.

### 구조

```text
Financial Data
       ↓
Python / Backend
       ↓
Calculated Financial Indicators
       ↓
Structured Data
       ↓
LLM
       ↓
AI Explanation
       ↓
Frontend
```

### 주요 기능

- 개별 채권 특징 설명
- 수익률 의미 설명
- 채권 위험요인 설명
- 금융지표 설명
- 두 채권의 차이 설명
- 시장 상황 설명

### 기본 원칙

```text
계산 = Python / Backend

설명 = AI
```

이를 통해 AI의 임의 계산이나 금융 데이터 왜곡 가능성을 줄인다.

---

## 11.8 Tableau MCP

### 선택적 확장 기능

Tableau MCP는 MVP 필수 기능으로 사용하지 않는다.

MVP에서는 Tableau Dashboard를 웹사이트에 Embed하는 것을 우선한다.

```text
MVP

Tableau
   ↓
Embedding API
   ↓
Next.js
```

프로젝트 개발에 여유가 있을 경우
AI가 Tableau의 데이터 및 분석 Context를 활용할 수 있도록 MCP 연동을 추가로 검토한다.

```text
확장

Tableau
   ↕
Tableau MCP
   ↕
AI
```

따라서 Tableau MCP는 핵심 서비스 구현 이후 추가하는 확장 기능으로 분류한다.

---

# 11.9 Final Technology Architecture

```text
                   Data Sources

            ┌──────────┴──────────┐
            │                     │
      한국은행 ECOS       금융위원회 / 공공데이터
            │                     │
            └──────────┬──────────┘
                       ↓
               Python + Requests
                       ↓
                   Raw Data
                       ↓
                Pandas Processing
                       ↓
               Financial Analysis
                       ↓
                 Final Dataset
                       │
             ┌─────────┴─────────┐
             │                   │
             ↓                   ↓
       Supabase              Tableau
      PostgreSQL             Dashboard
             │                   │
             ↓                   │
          FastAPI                │
             │                   │
             ├───────────────────┘
             │
             ↓
          Next.js
          + React
             │
      ┌──────┼───────┐
      │      │       │
      ↓      ↓       ↓
   탐색     비교    AI 설명
                     │
                     ↓
                    LLM
```

---

# 11.10 Technology Summary

| 영역 | 기술 | 역할 | 상태 |
|---|---|---|---|
| Data Collection | Python + Requests | 금융 API 수집 | ✅ 확정 |
| Data Processing | Pandas | 정제·통합·파생변수 | ✅ 확정 |
| Data Analysis | Pandas + NumPy | 금융 데이터 분석 | ✅ 확정 |
| Analysis Visualization | Matplotlib | 개발/EDA 시각화 | ✅ 확정 |
| Dashboard | Tableau | 금융 분석 Dashboard | ✅ 확정 |
| Tableau Web Integration | Tableau Embedding API | 웹사이트 Dashboard 삽입 | ✅ 확정 |
| Database | Supabase (PostgreSQL) | 서비스 데이터 저장 | ✅ 확정 |
| Backend | FastAPI | REST API 및 서비스 로직 | ✅ 확정 |
| Frontend | Next.js + React | 웹서비스 UI | ✅ 확정 |
| AI | LLM + FastAPI | 금융 데이터 설명 | ✅ 방향 확정 |
| Tableau MCP | Tableau MCP | AI-Tableau 연동 | ➕ 선택적 확장 |

---

# 11.전체 서비스 데이터 흐름


① 데이터 수집

ECOS / 금융위원회 API
        ↓
Python Requests
        ↓
Raw CSV


② 데이터 처리

Raw CSV
   ↓
Pandas
   ↓
Cleaning
   ↓
JOIN
   ↓
Derived Indicators
   ↓
Final Dataset


③ 데이터 저장

Final Dataset
      ↓
Supabase PostgreSQL


④ Backend

Supabase
   ↓
FastAPI
   ↓
REST API


⑤ Frontend

FastAPI ──────────────→ Next.js
                          ↑
Tableau ── Embedding ─────┘


⑥ AI

Supabase / FastAPI
        ↓
Structured Financial Data
        ↓
LLM
        ↓
AI Explanation
        ↓
Next.js


---

# 12. 개발 단계

## Phase 1 — Data

```text
데이터 수집
↓
데이터 정제
↓
ISIN 기반 데이터 통합
↓
파생변수 생성
↓
데이터 검증
↓
Final Dataset
```

---

## Phase 2 — Analysis

```text
EDA
↓
채권시장 분석
↓
Yield Curve
↓
Spread 분석
↓
Risk / Return 분석
↓
서비스에 사용할 지표 선정
```

---

## Phase 3 — Service Development

데이터 구조가 확정되면 병렬 개발한다.

```text
             Final Dataset
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
     Backend     Tableau     Analysis
        ↓
     Database
        ↓
      API
        ↓
     Frontend
        ↓
        AI
```

팀원별 역할에 따라 Backend / Frontend / Analysis / Tableau / AI 작업을 분담한다.

---

## Phase 4 — Integration

- Database ↔ Backend
- Backend ↔ Frontend
- Backend ↔ AI
- 데이터 ↔ Tableau

전체 사용자 Flow를 연결한다.

---

## Phase 5 — QA & Deployment

- 데이터 검증
- API 테스트
- UI 테스트
- AI 응답 검증
- 오류 처리
- Frontend 배포
- Backend 배포
- Database 배포
- README 및 개발 문서 정리

---

# 13. MVP Scope

## MVP 포함

- 시장금리 현황
- 채권 탐색
- 개별 채권 상세정보
- 채권 비교
- 기본 Risk / Return 분석
- AI 채권 설명
- AI 채권 비교

## MVP 이후 확장

- 금리 변화 Simulation
- Portfolio
- Watchlist
- 사용자 계정
- 개인화 분석
- 알림 기능

MVP가 완성되기 전에는 확장 기능보다 핵심 사용자 Flow 구현을 우선한다.

---

# 14. 완료 기준

사용자가 웹서비스에서 다음 Flow를 정상적으로 사용할 수 있으면
1차 MVP를 완료한 것으로 판단한다.

```text
시장 확인
↓
채권 탐색
↓
채권 선택
↓
상세정보 확인
↓
채권 비교
↓
수익 / 위험 확인
↓
AI 설명 확인
```

최종 목표는 단순한 채권 데이터 시각화가 아니라,

**데이터 수집 → 금융 분석 → 서비스 → AI 설명**

전체 과정을 하나의 프로젝트에서 구현하는 것이다.
