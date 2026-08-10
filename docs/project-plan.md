# Bond Dashboard — Project Plan

## 1. 프로젝트 주제

> 투자 경험은 있지만 채권 투자 경험이 부족한 개인 투자자가 채권시장과 개별 채권의 수익·위험 정보를 쉽게 이해할 수 있도록 지원하는 Tableau 기반 채권 분석 대시보드

핵심 사용자 흐름:

**시장 이해 → 채권 탐색 → 채권 비교 → 위험 이해 → 투자 판단**

## 2. 문제 정의

채권 투자 초보자는 표면금리, 시장금리, 만기, YTM, 신용등급, 듀레이션, 채권 가격 등 여러 지표를 동시에 이해해야 하며 관련 데이터도 여러 기관에 분산되어 있다.

> 채권 관련 데이터의 분산과 금융지표 해석의 어려움 때문에 초보 투자자가 여러 채권의 수익성과 위험을 비교하기 어렵다.

## 3. 페르소나

### 채권 투자 초보자
- 연령: 20대 후반 ~ 40대
- 주식, ETF, 예·적금 등의 투자 경험 보유
- 개별 채권 투자 경험은 부족
- 기본적인 경제·금리 개념은 알고 있음
- YTM, Duration, Credit Spread 등의 활용에는 익숙하지 않음

핵심 니즈:

> 어떤 채권의 수익성이 높고, 그만큼 어떤 위험이 있는지 한눈에 비교하고 싶다.

## 4. 데이터

### 시장 데이터
- 기준금리
- 국고채 3년 / 5년 / 10년
- 회사채 AA- 3년
- CPI

### 개별 채권 데이터
- ISIN
- 채권명
- 발행기관
- 채권 종류
- 발행일 / 만기일
- 표면금리
- 이자지급주기
- 신용등급
- 종가 / 시가 / 고가 / 저가
- 종가수익률
- 거래량 / 거래대금

### 파생지표
- 잔존만기
- Duration
- Yield Spread = 국고채 10Y - 국고채 3Y
- Credit Spread = 회사채 AA- 3Y - 국고채 3Y
- Policy Spread = 국고채 3Y - 기준금리

## 5. 데이터 처리

```text
외부 API / ECOS
      ↓
Python / Pandas
      ↓
컬럼 및 날짜 표준화
      ↓
결측·중복 검증
      ↓
데이터 병합
      ↓
파생지표 계산
      ↓
Tableau용 Dataset
```

개별 채권 데이터는 가능한 경우 `ISIN`을 핵심 결합 Key로 사용한다.

## 6. Dashboard

### Market Overview
- 기준금리
- 국고채 금리
- Yield Curve
- Spread
- CPI

### Bond Explorer
- 채권 종류
- 발행기관
- 신용등급
- 만기
- 수익률 필터

### Bond Comparison
- YTM/시장수익률
- 표면금리
- 신용등급
- 잔존만기
- Duration
- Credit Spread

### Bond Detail
- 채권 기본정보
- 가격 및 수익률
- 신용등급
- Duration
- 거래정보

## 7. 개발 Phase

### Phase 0 — 기획
- [x] 주제 선정
- [x] 문제 정의
- [x] 페르소나
- [x] 사용자 흐름
- [x] Tableau 활용 결정

### Phase 1 — 데이터 설계/수집
- [x] ECOS 시장 데이터
- [x] 개별 채권 가격 및 거래 데이터
- [x] 채권 기본정보
- [x] 신용등급
- [ ] `clprBnfRt` 종가수익률 정의 검증

### Phase 2 — 데이터 전처리
- [ ] Raw Data 정리
- [ ] Column 통일
- [ ] 날짜 형식 통일
- [ ] Data Merge
- [ ] 파생변수 계산
- [ ] Tableau Dataset 생성

### Phase 3 — Tableau 설계/개발
- [ ] KPI / Worksheet 설계
- [ ] Filter / Parameter 설계
- [ ] Market Overview
- [ ] Bond Explorer
- [ ] Bond Comparison
- [ ] Bond Detail

### Phase 4 — 검증/배포
- [ ] 금융지표 검증
- [ ] 사용자 관점 테스트
- [ ] Dashboard UX 개선
- [ ] Tableau 배포
- [ ] GitHub README 최종 업데이트
