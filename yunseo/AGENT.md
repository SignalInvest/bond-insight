# AGENT.md — 채권 CSV 3개 만들기 작업 지시서

> **진행 상태 (2026-08-11): 1차 구현 완료.** `yunseo/scripts/`에 4개 스크립트가 있고, `yunseo/output/`에 결과 3개 CSV(`기본 데이터.csv`, `시장 흐름 데이터.csv`, `파생 데이터.csv`)와 중간 산출물 2개가 생성돼 있어요. 실행 순서는 `clean_bond_data.py` → `clean_market_data.py` → `merge_data.py` → `calculate_metrics.py`. `SKILL.md`의 예시(KR310506AFB6, 2026-08-07)로 전부 검증 완료.

> 이 문서를 보고 실제로 코드를 짜서 CSV 3개를 만드는 에이전트/작업자를 위한 지시서예요.
> "왜"는 `SKILL.md`, "어디로 흐르는가"는 `ARCHITECTURE.md`에 있으니, 막히면 그 두 문서를 먼저 참고하세요.
> 이 문서 혼자 읽고 시작해도 되게 최대한 자기완결적으로 적었습니다.

---

## 목표

`data/raw/`와 `data/processed/`에 있는 원본 데이터를 **읽기 전용으로만** 가공해서 아래 3개 CSV를 만든다.

1. `기본 데이터.csv` — 채권(isin) × 날짜 단위 기본 정보 + 시세
2. `시장 흐름 데이터.csv` — 날짜 단위 시장 전체 지표
3. `파생 데이터.csv` — 위 둘을 조합해서 계산하는 파생지표 (duration, 실질수익률 등)

> **모든 파일 생성은 `yunseo/` 안에서만 한다.** 스크립트는 `yunseo/scripts/`, 결과 CSV는 `yunseo/output/`에 만들고, 원본 프로젝트의 `data/`, `src/` 아래는 아무것도 새로 만들거나 수정하지 않는다.

---

## 확정된 값 (2026-08-11)

`SKILL.md`에 "아직 정해지지 않았다"고 적혀있던 값 3개가 확정됐어요. 아래 값을 그대로 코드에 반영하면 됩니다.

1. `short_rate_change`/`long_rate_change`의 N = **20영업일**
2. `credit_rating` 우선순위 = **KIS → FN → KBP → NICE** (앞 순서 값이 있으면 사용, 없으면 다음 순서)
3. `bond_type` 매핑 = **국채**(국채) / **지방채**(지방채·지방공사채) / **특수채**(특수채) / **금융채**(금융채) / **회사채**(일반회사채) / **유동화증권**(유동화SPC채·MBS·SLBS·유사집합투자기구채) — 6종

근거는 `SKILL.md`의 "결정된 값" 섹션과 1-1/1-2/2-2에 정리되어 있어요. 이 값들을 코드에 상수/매핑 딕셔너리로 명확히 남겨두고(하드코딩해도 되지만 한 곳에 모아서 나중에 바꾸기 쉽게), 임의로 다른 값으로 바꾸지 마세요.

---

## 작업 순서

### 1단계 — `시장 흐름 데이터.csv` (제일 쉬움, 먼저 하기)

- 입력(읽기 전용): `data/processed/market_rates_daily.csv`, `data/processed/cpi_monthly.csv`
- 출력: `yunseo/output/시장 흐름 데이터.csv`
- `base_rate`, `credit_spread`, `policy_spread`는 그대로 복사, `yield_spread`는 `yield_spread_10y_3y`로 이름만 맞추기
- `cpi_yoy`: 월별 CPI로 전년동월 대비 상승률 계산 후, 해당 월의 모든 일자에 forward-fill. **2015년 첫 12개월은 결측으로 남길 것** (전년 데이터 없음)
- `short_rate_change`/`long_rate_change`: N=20영업일로 계산
- 검증: `SKILL.md` 2-3의 예시(2026-08-07, cpi_yoy=2.79%, short_rate_change=−0.032, long_rate_change=−0.042)와 같은 결과가 나오는지 대조

### 2단계 — `기본 데이터.csv`

- 입력(읽기 전용): `data/raw/bond_info/bond_info_raw.csv`, `data/processed/bond_market.csv`
- 출력: `yunseo/output/기본 데이터.csv` (중간 산출물 `bond_info_clean.csv`도 `yunseo/output/`에)
- 두 파일을 `isin`으로 조인 (`bond_market` 기준 left join — 시세가 있는 채권만 표1에 남긴다)
- 조인 전에 `bond_info_raw`의 날짜(`YYYYMMDD`)를 `bond_market`과 같은 형식(`YYYY-MM-DD`)으로 통일
- `remaining_maturity` = `maturity_date - date`
- `interest_payment_cycle`을 "3개월" 같은 문자열에서 연간 지급횟수 숫자로 파싱하는 함수 하나 만들어두기 (표3에서 재사용)
- `bond_type`은 확정된 매핑표 적용, `credit_rating`은 확정된 fallback 순서 적용
- `has_option` (optnTcd != '0000'), `is_fixed_rate` (irtChngDcdNm에 "변동"이 없으면 True) **플래그 컬럼도 같이 만들어서 남겨두기** — 표3에서 필터링에 씀
- 검증: `SKILL.md` 1-3의 예시(KR310506AFB6, remaining_maturity=41일)와 대조
- 조인 안 되는 isin이 있으면 버리지 말고 개수와 목록을 로그로 남기기 (지금 기준 1건 있음 — 원인 확인)

### 3단계 — `파생 데이터.csv`

- 입력: `yunseo/output/기본 데이터.csv`, `yunseo/output/시장 흐름 데이터.csv` (date로 조인)
- 출력: `yunseo/output/파생 데이터.csv`
- **먼저 `is_fixed_rate == True AND has_option == False`인 행만 골라서** duration 계열(`macaulay_duration`, `modified_duration`, `short_price_sensitivity`, `long_price_sensitivity`, `expected_maturity_profit`, `expected_maturity_return`) 계산
- 나머지 행은 이 컬럼들을 결측(NaN)으로 두고, `real_yield`(`ytm - cpi_yoy`)와 `relative_yield_spread`(가장 가까운 만기의 국고채 금리와 비교)는 조건 없이 모두 계산
- `interest_payment_cycle` 문자열이 비어있는 채권(할인채로 추정, 429건)은 이표 스케줄이 아니라 "만기에 원금만 한 번에 상환"하는 방식으로 현금흐름을 잡을 것
- 검증: 위 2단계에서 검증한 예시 채권 하나를 끝까지 손으로 계산해서 코드 결과와 비교

---

## 하지 말아야 할 것

- 결측치를 임의의 값(0, 평균값 등)으로 채우지 않기 — 결측은 결측으로 남기고, 왜 결측인지 알 수 있게 플래그/로그를 남길 것
- 옵션부 채권·변동금리 채권을 "일단 고정금리인 척" 계산하지 않기 (SKILL.md 3-1)
- 위 "확정된 값" 3가지를 바꿔서 진행하려면 코드 짜기 전에 먼저 사용자에게 확인받기
- 표3을 표1·표2 없이 먼저 만들려고 하지 않기 (의존 순서: 표1·표2 → 표3)
- CSV 인코딩은 `utf-8-sig`(BOM 있는 UTF-8)로 저장 — 기존 `data/processed/*.csv`가 다 이 방식이라 통일

---

## 완료 기준

- `yunseo/output/기본 데이터.csv`, `시장 흐름 데이터.csv`, `파생 데이터.csv` 3개 파일이 생성됨
- 각 파일의 컬럼이 원래 요청한 스펙(맨 처음 표)과 1:1로 맞음
- `SKILL.md`의 예시 채권(KR310506AFB6)과 예시 날짜(2026-08-07)로 직접 검산했을 때 코드 결과와 일치
- 옵션부/변동금리 채권이 `파생 데이터.csv`에서 결측 처리된 이유가 `has_option`/`is_fixed_rate` 플래그로 추적 가능
