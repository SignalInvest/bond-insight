# 📊 Bond Dashboard

채권 투자 경험이 부족한 개인 투자자가 **채권시장과 개별 채권의 수익·위험 정보를 쉽게 탐색하고 비교할 수 있도록 지원하는 Tableau 기반 채권 분석 대시보드**입니다.

## 🎯 Project Goal

채권 초보자는 기준금리, YTM, 신용등급, 듀레이션, 채권 가격 등 여러 금융지표를 함께 이해해야 하며 관련 데이터도 여러 기관에 분산되어 있습니다.

본 프로젝트는 데이터를 통합·분석하여 다음 흐름을 제공합니다.

**시장 이해 → 채권 탐색 → 채권 비교 → 위험 이해 → 투자 판단**

## 👤 Target User

**20대 후반 ~ 40대 채권 투자 초보자**

- 주식·ETF·예적금 등의 투자 경험이 있음
- 개별 채권 투자 경험은 부족함
- YTM, Duration, Credit Spread 등의 활용에는 익숙하지 않음
- 채권의 수익성과 위험을 한눈에 비교하고 싶어 함

## 🏗 Architecture

```text
금융위원회 API
      +
한국은행 ECOS
      +
채권시장 데이터
      ↓
Python / Pandas
      ↓
데이터 정제 / 병합
      ↓
금융 파생지표 계산
      ↓
Tableau Dataset
      ↓
Tableau Dashboard
```

## 📊 Data

### Market Data
- 기준금리
- 국고채 3Y / 5Y / 10Y
- 회사채 AA- 3Y
- CPI

### Bond Data
- ISIN / 채권명
- 발행기관 / 채권 종류
- 발행일 / 만기일
- 표면금리 / 이자지급주기
- 신용등급
- 종가 / 시가 / 고가 / 저가
- 종가수익률
- 거래량 / 거래대금

### Derived Metrics
- Remaining Maturity
- Duration
- Yield Spread
- Credit Spread
- Policy Spread

> `clprBnfRt`(종가수익률)의 YTM 활용 가능 여부는 공식 데이터 정의 검증 후 확정합니다.

## 📈 Dashboard

1. **Market Overview** — 기준금리, 국고채 금리, Yield Curve 등 시장 환경
2. **Bond Explorer** — 신용등급, 만기, 발행기관, 수익률 기반 채권 탐색
3. **Bond Comparison** — 여러 채권의 수익성과 위험 비교
4. **Bond Detail** — 선택 채권의 가격, 수익률, 신용등급, 만기 등 상세 분석

## 🛠 Tech Stack

- Python
- Pandas
- 금융위원회 Open API
- 한국은행 ECOS
- CSV
- Tableau

## 🚀 Development Status

### Phase 0 — Planning
- [x] 주제 선정
- [x] 문제 정의
- [x] 페르소나
- [x] 사용자 흐름
- [x] Tableau 활용 결정

### Phase 1 — Data Collection
- [x] ECOS 시장금리
- [x] 개별 채권 가격/거래 데이터
- [x] 채권 기본정보
- [x] 신용등급
- [ ] 종가수익률 정의 검증

### Phase 2 — Data Processing
- [ ] Raw Data 정리
- [ ] Column 표준화
- [ ] Data Merge
- [ ] 파생변수 계산
- [ ] Tableau Dataset 생성

### Phase 3 — Tableau
- [ ] Market Overview
- [ ] Bond Explorer
- [ ] Bond Comparison
- [ ] Bond Detail

## 📁 Project Structure

```text
Bond-Dashboard/
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── src/
├── docs/
│   └── project-plan.md
├── .gitignore
└── README.md
```

## 📌 Project Focus

**데이터 수집 → 데이터 전처리 → 금융 데이터 분석 → Tableau 시각화 → 사용자 중심 Dashboard 설계**
