# Bond Screener/Overview 실데이터 연동 — 구현 계획 (2026-08-13)

> `docs/SKILL_1034.md`(BOND BRIDGE 리디자인)에서 mock으로 채워둔 Bond Screener/Bond Overview를
> 실제 Supabase 데이터로 교체하는 작업. 사용자가 Tableau에서 쓰던 `yunseo/output/통합 데이터.csv`를
> 새 Supabase 테이블로 올리고, 그걸 백엔드 API로 서빙하는 방향으로 확정함(아래 0절 참고).
> 이 문서도 SKILL_1034.md와 동일하게 **Step 단위로 하나씩 진행, 끝날 때마다 보고 후 확인받고 다음
> Step으로 넘어간다.**

---

## 0. 왜 이 경로인가 (확정된 결정)

- **후보 A(채택)**: `통합 데이터.csv`를 새 Supabase 테이블로 그대로 업로드하고, 새 API로 서빙.
- **후보 B(기각)**: 이미 올라가 있는 `bonds`/`bond_market`/`bond_metrics` 3개 테이블을 백엔드에서
  JOIN.
- **기각 이유**: `GET /api/bonds`(`backend/app/api/bonds.py` → `list_bonds()`)는 지금
  **`bonds` 테이블만 조회**해서 YTM·현재가·잔존만기·Duration이 아예 안 나옴(실제 코드 확인함,
  `backend/app/services/bond_service.py:27` `db.table("bonds").select("*")`). 이 셋을 합치려면
  백엔드 JOIN 로직을 새로 짜야 하고, `bond_metrics`(2026-08-10 기준)와 `bond_market`(2026-08-07
  기준)의 **산출 기준일이 서로 다른** 문제도 처리해야 함. 반면 `통합 데이터.csv`는 사용자가 이미
  Tableau로 검증한 값이 한 파일에 다 합쳐져 있어서 더 빠르고 신뢰도가 높음.

---

## 1. 확인된 사실 (실측, 재검증 불필요)

- `통합 데이터.csv`: **359행**(2026-08-07 기준 1일치), 다음 컬럼 보유 —
  `date, isin, bond_name, issuer, bond_type, credit_rating, issue_date, maturity_date,
  remaining_maturity, coupon_rate, interest_payment_cycle, close_price, ytm, volume,
  trading_value, payments_per_year, has_option, is_fixed_rate, macaulay_duration,
  modified_duration, short_price_sensitivity, long_price_sensitivity, real_yield,
  relative_yield_spread, expected_maturity_profit, expected_maturity_return, base_rate, cpi_yoy,
  yield_spread_10y_3y, credit_spread, policy_spread, short_rate_change, long_rate_change`
  (출처: `yunseo/scripts/merge_data.py` + `calculate_metrics.py`)
- **`remaining_maturity`는 "일" 단위**다 (`yunseo/scripts/calculate_metrics.py:85`
  `remaining_years = df["remaining_maturity"] / 365.0`). 년 단위로 쓰려면 반드시 365(.25)로
  나눠야 함 — 헷갈리지 말 것.
- **`real_yield` ≠ 우리가 쓰는 "실질수익률(세후)"**. CSV의 `real_yield`는
  `YTM − CPI YoY`(물가연동 실질금리, `calculate_metrics.py:86`)이고, Bond Overview에 쓰는
  "실질수익률(세후)"은 `YTM × (1 − 15.4%)`(세후 명목수익률)이다. **이름이 비슷해서 헷갈리기 쉬움
  — CSV의 `real_yield` 컬럼은 이번 화면에 쓰지 않는다.**
- **`relative_yield_spread`가 우리가 쓰는 "신용 스프레드"다** (`YTM − 잔존만기 보간 국고채 금리`,
  `calculate_metrics.py:87-90`). 기존 `BondInsight.tsx`(mock 이전 버전)가 CSV 폴백 경로에서 쓰던
  것과 정확히 같은 정의.
- **`bond_type` 분포**(359건): 금융채 131 · 회사채 87 · 국채 72 · 지방채 53 · 특수채 13 ·
  유동화증권 2 · 공백 1. 즉 "국채/회사채" 버튼 2개로는 **200건(약 56%)이 커버 안 됨** — 원래
  요구사항이 "전체/국채/회사채/…"였으므로 버튼 자체는 그대로 두고, 나머지 유형은 "전체"에서만
  보이게 둔다(범위 변경 아님, 그냥 실데이터 특성 기록).
- **`credit_rating` 공백 125건**(국채·일부 특수채 등 — 등급이 원래 없는 채권들, 결측 아님).
- **`has_option=True` 83건** — Duration 계산에서 제외해야 하는 옵션부 채권(기존
  `BondInsight.tsx`의 `unavailableReason` 로직과 동일 기준 재사용 가능).
- **ISIN이 Supabase `bonds` 테이블(29,088건)과 거의 다 겹침**: `docs/database-erd.md` 112행에
  따르면 `bond_market` 업로드 시 359건 중 **358건**이 `bonds` 테이블에 이미 있었고 1건
  (`KR381003GD86`)만 빠졌음. 즉 **AI Analysis(`/api/ai/explain`)가 358/359건에서 바로 정상
  동작할 것으로 예상됨** — mock ISIN 때와 달리 실제로 Supabase에 존재하는 ISIN이기 때문. Step 5
  QA에서 실측으로 확인.

---

## 2. 확정이 필요한 설계 결정 (Step 시작 전 확인)

### 2-1. 신규 테이블 스키마 — `bond_snapshot`

`bond_market` 테이블 패턴(`bigint id PK`, `unique(isin_code, reference_date)`)을 그대로 따라가서
나중에 여러 날짜가 쌓여도(2026-08-07 외 다른 날짜 CSV가 생기면) 그대로 upsert할 수 있게 함.

| 컬럼 | 타입 | 비고 |
| --- | --- | --- |
| `id` | bigint PK | |
| `isin_code` | text | FK 없음(현재 `bonds`와 별도 파이프라인이라 강제 FK는 안 걺 — 358/359만 겹침) |
| `reference_date` | date | `unique(isin_code, reference_date)` |
| `bond_name` | text | |
| `issuer` | text | |
| `bond_type` | text | |
| `credit_rating` | text, nullable | |
| `issue_date` | date, nullable | |
| `maturity_date` | date | |
| `remaining_days` | integer | CSV `remaining_maturity`(일 단위) 그대로 |
| `coupon_rate` | numeric, nullable | |
| `close_price` | numeric | |
| `ytm` | numeric | |
| `volume` | bigint, nullable | |
| `trading_value` | numeric, nullable | |
| `has_option` | boolean | |
| `is_fixed_rate` | boolean | |
| `macaulay_duration` | numeric, nullable | |
| `modified_duration` | numeric, nullable | |
| `relative_yield_spread` | numeric, nullable | = 신용 스프레드 |
| `created_at` | timestamptz default now() | |

CSV의 나머지 컬럼(`interest_payment_cycle, payments_per_year, short/long_price_sensitivity,
real_yield, expected_maturity_*, base_rate, cpi_yoy, yield_spread_10y_3y, credit_spread(시장
전체), policy_spread, short/long_rate_change`)은 **저장하지 않음** — 시장 전체 지표는
`market_rates`와 중복이고, 나머지는 지금 화면(Screener 7컬럼 + Overview 4지표)에서 안 씀.
**확인 필요**: 이 서브셋이 맞는지, 혹시 나중에 쓸 걸 대비해 전체 컬럼을 다 저장해둘지.

### 2-2. 전략 뱃지(안정성 중심/수익률 중심/거래 활발/수익률 높음) 판정 규칙

DB에는 이런 분류가 없어서(순수 mock 전용이었음) 규칙을 새로 정해야 함 — **제안**:

- **안정성 중심**: `bond_type === "국채"` 이거나 `credit_rating`이 `AA-` 이상(`AAA/AA+/AA/AA-`)
- **수익률 중심**: `credit_rating`이 `A+` 이하이거나 공백이 아니면서 `AA-` 미만인 경우
- **거래 활발**: `trading_value`가 359건 중 상위 20%
- **수익률 높음**: `ytm`이 359건 중 상위 10%
- **단기채 / 장기채**: `remaining_days / 365 <= 3` → 단기채, `>= 10` → 장기채, 그 사이는 태그 없음
  (mock 때와 동일 기준)

### 2-3. 잔존만기 드롭다운 값

`bond_metrics.maturity_bucket`에서 이미 쓰던 실제 라벨을 그대로 가져다 씀(mock 때 "10년 초과"라고
썼던 걸 실제 라벨 **"10년 이상"**으로 교정): `1년 이하 / 1~3년 / 3~5년 / 5~10년 / 10년 이상`.
영구채(만기 없음) 케이스는 이번 359건 표본엔 없었지만, 혹시 있으면 "영구채"로 별도 표시.

### 2-4. API 설계

기존 `/api/bonds`, `/api/bonds/{isin}` 계약은 안 건드림(다른 화면이 나중에 쓸 수도 있음). 새
라우터를 추가:

- `GET /api/bond-snapshot?reference_date=&bond_type=&rating=&search=&page=&page_size=` — 필터는
  최소한으로 두고(잔존만기 구간·전략 뱃지 필터는 359건이면 프론트에서 계산해도 충분하니 서버
  파라미터로는 안 만듦, 2-2/2-3 로직은 프론트에 둠), 기본은 **한 번에 다 반환**(359건은
  페이지네이션 없이 통째로 가져와도 부담 없는 크기).
- 상세 조회용 `/api/bond-snapshot/{isin}`은 **만들지 않음** — 목록 359건을 프론트가 이미 들고
  있으니 그 배열에서 선택된 `isin`으로 찾아 쓰면 충분(지금 `BondScreener`→`DashboardBody`→
  `BondInsight` 흐름과 동일).

---

## 3. Step 목록

### Step 1 — Supabase 테이블 생성 + 업로드 스크립트
- 2-1 스키마로 `bond_snapshot` 테이블 생성(Supabase 대시보드 SQL Editor, RLS 정책은 기존 테이블과
  동일하게 anon/authenticated 조회만 허용 — 사용자가 직접 실행해야 함, 코드로 자동화 불가)
- `src/loading/upload_bond_snapshot.py` 신규(`upload_supabase.py`의 `value_or_none`/`iso_date`/
  `numeric`/`integer` 헬퍼 재사용) — `yunseo/output/통합 데이터.csv` 읽어서 upsert
- `docs/database-erd.md`에 `bond_snapshot` 테이블 추가

### Step 2 — 백엔드 API
- `backend/app/services/bond_snapshot_service.py` + `backend/app/api/bond_snapshot.py` 신규
- `GET /api/bond-snapshot` 구현(2-4), `backend/app/main.py`에 라우터 등록
- 간단한 테스트 추가(`tests/test_bond_snapshot_api.py`, 기존 `tests/test_backend_api.py` 패턴 참고)

### Step 3 — 프론트: Bond Screener 실데이터 전환
- `lib/api.ts`에 `getBondSnapshots()`, `types/api.ts`에 `BondSnapshotRow` 추가
- `BondScreener.tsx`: `MOCK_BONDS` 대신 API 호출 결과로 채움(로딩/에러 상태 추가, 기존
  `useMarketSnapshot` 패턴처럼 render-time 파생으로 loading 처리)
- 전략 뱃지 계산(2-2), 잔존만기 버킷(2-3) 프론트 유틸로 구현
- `data/mockBonds.ts`는 삭제(더는 안 씀)

### Step 4 — 프론트: Bond Overview 재연결
- `BondInsight.tsx`가 `MockBond` 대신 `BondSnapshotRow` 타입을 받도록 교체
- 신용 스프레드 = `relative_yield_spread` 그대로 사용(1절의 `real_yield` 혼동 주의 재확인)
- `DashboardBody.tsx`의 `selectedBond` state 타입도 `BondSnapshotRow | null`로 교체

### Step 5 — QA
- 359건 전체 로딩, 필터 조합, 신용등급 공백(125건)·옵션부 채권(83건) 표시 확인
- **AI Analysis 실제 응답 확인**(1절에서 예상한 358/359건 정상 응답 여부 실측 — 이번엔 mock이
  아니라 진짜 ISIN이라 not-found 대신 실제 AI 설명이 나와야 정상)
- 날짜 선택(`Header`의 기준일)과의 상호작용 확인 — `bond_snapshot`도 `reference_date` 컬럼이
  있으니 Bond Market과 동일하게 "그 날짜에 데이터 없으면 빈 상태" 원칙 적용할지 결정
  (지금은 데이터가 2026-08-07 하루뿐이라 사실상 Bond Market과 동일한 제약)

---

## 4. 구현 완료 기록 (2026-08-13)

Step 1~5 전부 구현하고 실제 Supabase·Gemini까지 붙여서 검증 완료. 계획과 달라진 점만 남김.

- **Step 1**: `bond_snapshot` 테이블 생성 후 첫 업로드 시도에서 `permission denied` 발생 —
  SQL Editor로 만든 테이블은 Table Editor(UI)와 달리 `service_role`에 권한이 자동으로 안 붙는
  경우가 있음을 확인. `docs/sql/bond_snapshot.sql`에 명시적 `GRANT`를 추가해서 해결(파일에
  기록해둠 — 다음에 비슷한 테이블 만들 때 같은 문제 반복될 수 있으니 참고). 358건 업로드 성공
  (고아 ISIN `KR381003GD86` 1건 제외, 예상대로).
- **Step 2**: 계획대로 `/api/bonds`는 안 건드리고 `/api/bond-snapshot` 신규 라우터로 분리.
  실제 라이브 서버에 필터+정렬 호출까지 검증(예: `bond_type=국채&sort_by=ytm&sort_order=desc` →
  정확히 72건).
- **Step 3+4 통합 진행**: 원래 계획은 Step 3(Screener)과 Step 4(Overview)를 분리했지만,
  `DashboardBody`의 `selectedBond` state 타입이 두 컴포넌트에 동시에 걸려 있어서 어설픈 임시
  어댑터를 쓰는 대신 두 Step을 한 번에 처리함(문서상 계획 구조는 유지, 실행 순서만 합침).
- **예상 밖 발견 — 영구채가 실제로 많음**: 1절/2-3에서 "이번 표본엔 영구채가 없었다"고 적었는데,
  실제로 붙여보니 **31건**이 `remaining_days: null`(영구채, 대부분 은행 신종/조건부자본증권)이었음.
  `lib/bondSnapshot.ts`의 "영구채" 처리 로직이 정확히 이 케이스를 잡아냄 — 계획에서 대비해둔 게
  실제로 필요했던 경우.
- **부수 정리**: Screener/Overview가 더는 Tableau 이름 매칭 브릿지를 안 써서
  `frontend/src/app/api/bond-insight/route.ts`와 `frontend/src/data/*.csv` 2개가 완전히 죽은
  코드가 됨 — 확인 후 삭제함(계획엔 없었지만 자연스러운 후속 정리).
- **Bond Overview의 뱃지(안정성 중심 등) 표시는 뺌**: mock 버전엔 선택된 채권 밑에 전략 뱃지를
  보여줬는데, 실데이터에서는 그 뱃지가 전체 358건 기준 백분위로 계산돼서 Overview 컴포넌트
  혼자서는 다시 계산할 수 없음(전체 목록이 없어서). 큰 기능은 아니라 이번엔 생략 — 필요하면
  `DashboardBody`가 태그를 같이 들고 있다가 내려주는 방식으로 나중에 추가 가능.
- **AI Analysis 실측**: `KR6138931D93`(BNK금융 조건부(상)10)로 직접 확인 — 200 응답, 4.4초,
  `gemini-3.1-flash-lite`가 실제 채권 데이터(발행사·쿠폰·신용등급·YTM·Duration 결측 사유·신용
  스프레드)를 정확히 반영한 한국어 설명을 생성함. mock 때와 달리 not-found가 전혀 안 뜸 — 1절
  예상(358/359건 정상)이 맞았음.
- **QA 결과**: 날짜를 2026-08-10으로 바꾸면 Bond Market·Bond Screener 둘 다 정확히 빈 상태로
  전환됨(결정 3-2/신규 항목 그대로 적용). 다만 이미 선택돼 있던 Bond Overview 패널은 날짜를
  바꿔도 이전 선택을 그대로 유지함(의도적으로 지우지 않음 — 날짜를 되돌리면 다시 맞는 상태가
  됨). 콘솔 에러 없음, 프론트 전체 typecheck/lint 통과, 백엔드 테스트 18/18 통과.

### 다음에 할 일 (이번 범위 밖)
- Bond Overview 선택 시 전략 뱃지 표시(위 "부수 정리" 항목 참고)
- 다른 날짜의 CSV가 생기면 `upload_bond_snapshot.py`를 그 날짜용으로 일반화(지금은 파일 경로가
  2026-08-07 CSV에 고정)
- 선택 채권 가격 추이 차트(여전히 placeholder — 여러 날짜 데이터가 쌓여야 의미 있음)
