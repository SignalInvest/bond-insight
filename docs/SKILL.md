# Bond Ledger 프론트엔드 대시보드 — 계획 정리

> 목업 이미지(`BOND LEDGER` 대시보드)를 실제 프론트엔드로 옮기면서, 대화 중에 확정한 결정들과
> 그 이유를 정리한 문서예요. 나중에 다시 보거나 다른 사람(에이전트 포함)이 이어서 작업할 때
> "왜 이렇게 했는지"를 다시 설명 안 해도 되게 적었습니다.

---

## 0. 지금 상태, 한눈에 보기

| 영역 | 상태 |
| --- | --- |
| Backend (FastAPI) | `/api/market`, `/api/bonds`, `/api/compare`, `/api/analysis`, `/api/ai` 라우터까지 이미 구현되어 있음 |
| Database | Supabase 연결 정보(`SUPABASE_URL`, `SUPABASE_KEY`)와 `GEMINI_API_KEY`까지 `.env`에 이미 채워져 있음 |
| Frontend (Next.js) | `chore(frontend): scaffold Next.js application`(#10)까지만 완료된 뼈대 상태 — 페이지, 스타일, 컴포넌트 전부 없음. `npm install` 전이라 `node_modules`도 없었음 |
| GitHub Issues (#11~#19) | 원래 "공통 레이아웃 → 화면별 페이지(Market/Explorer/Detail/Comparison/Risk-Return) → AI → Tableau → QA" 순서로 잘게 쪼개져 있었지만, **이 작업에서는 의도적으로 무시하기로 함** (1-4 참고) |

즉 지금 만들 것은 **이슈 번호와 상관없이, 아래 목업 이미지 하나를 그대로 구현하는 것**이 목표예요.

---

## 1. 확정된 결정과 이유

### 1-1. 페이지 구조 — 진짜 단일 페이지 (라우팅 없음)

- **결정**: `/` 한 페이지 안에 섹션 3개(Market Overview / Bond Screener / Bond Insight)를 세로로 쌓는다. 채권 상세·비교용 별도 페이지는 만들지 않는다.
- **왜**: 원래는 "테이블 행 클릭 → 상세 페이지, 여러 개 선택 → 비교 페이지" 구조도 검토했지만(URL 공유, 화면 밀도 측면에서 장점 있음), 최종적으로 **상세/비교 기능 자체를 이번 범위에서 뺐기 때문에** 페이지 분리가 필요 없어짐. Next.js 라우팅 개념 없이 "페이지 하나 + 컴포넌트 3개"만 이해하면 되게 최대한 단순화.

### 1-2. GitHub 이슈(#11~#19)는 이번 작업과 매핑하지 않는다

- **결정**: 지금 만드는 화면을 특정 이슈를 닫는 작업으로 연결하지 않는다.
- **왜**: 원래 이슈들은 "공통 레이아웃 → Market Overview → Bond Explorer → Bond Detail → Bond Comparison → Risk/Return → AI → Tableau → QA" 순서의 멀티페이지 설계를 전제로 쪼개져 있는데, 목업 기반 단일 페이지 설계는 그 구조와 안 맞음. 이슈 재정리는 나중에 별도로 판단하기로 하고, 지금은 화면 구현에만 집중.

### 1-3. 스타일링 — Tailwind CSS

- **결정**: `tailwindcss` + `@tailwindcss/postcss` 설치, `globals.css`에 `@theme`로 커스텀 색상 토큰(네이비/골드/크림) 정의.
- **왜**: 기존 코드엔 스타일링 도구가 전혀 없어서(순수 `globals.css`), 목업처럼 카드·배지·그리드가 많은 대시보드는 클래스 이름만으로 빠르게 조립하는 게 유리함.

### 1-4. Bond Screener 섹션 = Tableau 뷰가 통째로 대체

- **결정**: 목업의 필터 버튼(High Yield / Stability / Short-term 등)과 채권 테이블을 직접 구현하지 않고, 이 섹션 전체를 Tableau Public 임베드로 채운다.
- **Tableau URL**: `https://public.tableau.com/app/profile/yunseo.lee6797/viz/yunseo_3h48m/1`
- **왜**: Tableau 뷰(`yunseo_3h48m`) 자체가 이미 필터·테이블 기능을 갖추고 있다고 보고, 같은 기능을 React로 중복 구현하지 않기로 함.
- **주의**: 목업 이미지에는 Tableau 임베드 placeholder가 **Section 3(Bond Insight)** 쪽에 그려져 있지만, 실제로는 **Section 2(Bond Screener)** 자리에 넣기로 확정함. 이미지와 실제 배치가 다르니 헷갈리지 말 것.

### 1-5. (초기 결정, 이후 뒤집힘) 처음엔 목업 값만 쓰기로 했었음

- 처음엔 Section 1·3을 목업 숫자로 하드코딩하고 실데이터 연동은 미루기로 했었는데, 2절의 실데이터 연동 이후로는 더 이상 유효하지 않은 결정. 기록만 남겨둠.

### 1-6. Tableau 행 선택 → Bond Insight 연동 (2026-08-12)

- **결정**: Tableau `MarkSelectionChanged` 이벤트를 `viz` 엘리먼트에 직접 리스닝(워크시트 단위 아님), `TableauEventType`은 `window.tableau`가 아니라 스크립트를 ES 모듈로 `import`해서 사용. 공식 예제(tableau/embedding-api-v3-samples)로 검증한 패턴.
- **왜**: 처음엔 워크시트별 리스너 + `window.tableau` 참조로 짰다가 "workbook을 찾지 못함" 버그가 남. 공식 샘플 코드로 정확한 이벤트 부착 위치를 재확인해서 고침.
- **Tableau 실제 컬럼명** (2026-08-12 확인): 채권명 / 발행사 / 유형 / 신용등급 / 잔존만기 / YTM(수익률) / 현재가. Duration·거래량 컬럼은 Tableau에 없음 — 있을 거라 기대하지 말 것.

### 1-7. Duration 등 파생지표는 client-side 근사 대신 실제 계산값 사용 (2026-08-12)

- **결정**: Section 3(Bond Insight)의 Duration·신용스프레드는 브라우저에서 대충 근사하지 않고, `tests/test_calculate_duration.py` / `tests/test_calculate_credit_spread.py`가 검증하는 `src/analysis/` 공식 계산값을 가져와 쓴다.
- **왜**: Duration은 쿠폰·이자지급주기·차기이자지급일까지 있어야 계산 가능한 값이라, Tableau가 주는 필드(YTM·잔존만기)만으로는 원천적으로 근사가 불가능함. `yunseo/AGENT.md`의 "결측치를 임의값으로 채우지 않는다" 원칙과도 맞음.
- **중요한 발견**: **Supabase에 이미 전체 채권(29,089건)이 업로드되어 있었음** (`created_at` 기준 2026-08-12, `src/loading/upload_supabase.py` 실행 완료 상태). 즉 "Supabase 업로드"는 할 일이 아니라 이미 끝난 일 — 착각하지 말 것. `/api/bonds/{isin}`을 부르면 `metrics.modified_duration`, `market.credit_spread` 등이 바로 나온다.
- **연결 방식**: Tableau가 보여주는 채권명(`국고01875-5103(21-2)`)과 Supabase `bonds.bond_name`(`국고채권 01875-5103(21-2)`)의 표기가 달라서 이름으로 직접 백엔드를 조회할 수 없음. 그래서 `frontend/src/app/api/bond-insight/route.ts`가 다리 역할을 함:
  1. Tableau 채권명으로 `yunseo/output/기본 데이터.csv`에서 ISIN을 찾는다 (이 CSV의 bond_name은 시세 파일 기준이라 Tableau와 표기가 같음).
  2. 그 ISIN으로 `${NEXT_PUBLIC_API_URL}/api/bonds/{isin}` (FastAPI, 기본값 `http://127.0.0.1:8000`)을 호출한다.
  3. 백엔드가 응답하면 그 값(Supabase 공식 계산값)을 최우선으로 쓰고, 백엔드가 꺼져 있으면 `yunseo/output/파생 데이터.csv`의 로컬 계산값으로, 그마저 없으면 Tableau의 YTM만으로 계산 가능한 값(실질수익률)만 보여준다. 3단계 fallback 모두 "데이터 없음"을 정직하게 표시하지 임의값을 채우지 않는다.
- **알아둘 것**: 이 프론트엔드 기능을 쓰려면 **FastAPI 백엔드(`uvicorn backend.app.main:app --port 8000`)가 같이 떠 있어야** Supabase 공식 값이 나온다. 안 떠 있으면 자동으로 로컬 CSV 값으로 대체되긴 하지만, 로컬 계산값(yunseo 1차 구현)과 공식값(`src/analysis`)은 계산 방식이 미세하게 달라 숫자가 살짝 다를 수 있음 (기준일이 다르기도 함).

### 1-8. Market Overview(Section 1)도 실제 `/api/market`에 연결 (2026-08-12)

- **결정**: KPI 5개(Base Rate/Gov 3Y/Gov 10Y/Yield Spread/CPI) 전부 `/api/market`(Supabase `market_rates` 테이블)에서 값과 전일 대비 증감을 계산. Bond Insight가 2026-08-07 하루치 스냅샷뿐이라, Market Overview도 최신값(당시 2026-08-11) 대신 **2026-08-07로 고정**해서 대시보드 전체 기준일을 통일함 (`MarketOverview.tsx`의 `DASHBOARD_REFERENCE_DATE`).
- **연결 방식**: `MarketOverview.tsx`가 "use client"로 바뀌어서 `lib/api.ts`의 `getMarketRates()`로 FastAPI를 직접 호출 (bond-insight처럼 브리지 라우트 안 거침 — 이름 매칭 문제가 없어서 바로 호출 가능).
- **CPI 추가 (2026-08-12)**: 처음엔 `market_rates`에 CPI 컬럼 자체가 없어서 목업으로 남겨뒀었는데, 로컬 `data/processed/cpi_monthly.csv`(월별 CPI 지수, 2015-01~2026-07)에서 전년동월 대비 상승률(cpi_yoy)을 계산해 채워넣음.
  - **스키마 변경이 필요했음**: `market_rates`는 REST API(Supabase 클라이언트)로만 다뤄서 `ALTER TABLE`을 코드로 직접 못 함 — Supabase 대시보드 SQL Editor에서 `ALTER TABLE market_rates ADD COLUMN cpi_yoy numeric;`을 사용자가 직접 실행.
  - **적재**: `src/loading/upload_cpi.py` (신규) — 월별로 계산해서 그 달에 속한 모든 `reference_date` 행에 같은 값을 채움. 시장금리 데이터(일별)와 달리 CPI는 월 1회 발표라 어쩔 수 없이 그 달 전체가 같은 값.
  - **아직 발표 안 된 달(예: 2026-08) 처리**: `cpi_monthly.csv`에 해당 월 데이터가 없으면 계산 자체가 불가능. 실무에서도 이 경우 "가장 최근 발표된 값"을 쓰므로, 마지막으로 계산된 달(2026-07, cpi_yoy=2.7892%)을 그 이후 날짜에 이월(carry-forward)하도록 스크립트에 넣음. 값을 지어낸 게 아니라 마지막 실측값을 그대로 늘린 것.

### 1-9. Bond Screener는 여전히 우리 백엔드와 연결 안 됨 (의도적)

- Section 2는 Tableau Public 뷰가 통째로 대체하고 있어서(1-4), 애초에 FastAPI/Supabase를 거치지 않음. Tableau 자체가 yunseo님이 별도로 발행한 독립적인 데이터 경로. "언제 백엔드랑 연결하냐"는 질문이 나올 수 있는데, **연결할 계획 자체가 없다는 게 정답** — 스크리너 자체를 자체 구현으로 바꾸지 않는 한.

---

## 2. 화면 구성 3개 섹션

### Section 1 — Bond Market Overview Index

KPI 카드 5개. 값은 목업 이미지 그대로 하드코딩.

| 라벨 | 값 | 증감 | 방향 |
| --- | --- | --- | --- |
| Base Rate (한국은행) | 3.50% | 0.00%p | 보합 |
| Gov 3Y (국고채 3년) | 3.25% | -0.03%p | 하락 |
| Gov 10Y (국고채 10년) | 3.38% | -0.05%p | 하락 |
| Yield Spread (국고 10Y-3Y) | 13bp | +2bp | 상승 |
| CPI (소비자물가지수) | 2.8% | -0.1%p | 하락 |

### Section 2 — Bond Screener

Tableau 임베드(`yunseo_3h48m`)로 전체 대체. 자체 필터 버튼·테이블 없음 (1-4 참고).

### Section 3 — Bond Insight

초보 투자자에게 도움이 되는 파생지표 4종을 예시 채권 1개(회사채, 예: `현대차321-2`) 기준으로 카드로 보여줌. 국고채는 신용 스프레드가 의미 없어서(스스로가 기준이라) 예시로 회사채를 씀.

| 지표 | 계산 방법 | 데이터 소스 (2026-08-12 기준) |
| --- | --- | --- |
| 오늘 거래량 (유동성) | 거래대금·거래량 | Supabase `bond_market` (백엔드 켜짐) → 없으면 yunseo CSV → 없으면 "데이터 없음" |
| 실질수익률 (세후) | 세전 YTM × (1 − 15.4%) | 위와 동일한 우선순위, Tableau의 YTM만으로도 계산 가능 |
| 신용 스프레드 | YTM − 잔존만기 보간 국고채 금리 | Supabase `bond_market.credit_spread` → yunseo CSV `relative_yield_spread` |
| Duration (금리 민감도) | Modified Duration | Supabase `bond_metrics.modified_duration` → yunseo CSV → 없으면 "데이터 없음" (client-side 근사 절대 안 함, 1-7 참고) |

Tableau 행 선택 → `/api/bond-insight` 브리지 → (가능하면) 진짜 백엔드까지 이어지는 구조. 1-6, 1-7 참고.

---

## 3. 컴포넌트 구조

```text
frontend/src/
├── app/
│   ├── globals.css        Tailwind + 커스텀 색상 토큰(@theme)
│   ├── layout.tsx          기존 유지
│   ├── page.tsx             Header + DashboardBody 조립
│   └── api/
│       └── bond-insight/route.ts   Tableau 채권명 → ISIN → 진짜 백엔드 조회 브리지 (1-7 참고)
└── components/
    ├── Header.tsx           BOND LEDGER 로고, 날짜, 아이콘
    ├── DashboardBody.tsx    선택된 채권 state를 들고 있는 클라이언트 컴포넌트 (Screener ↔ Insight 연결)
    ├── MarketOverview.tsx   Section 1 — KPI 카드 5개, /api/market 실데이터 (1-8)
    ├── BondScreener.tsx     Section 2 — Tableau 임베드 컨테이너
    ├── TableauEmbed.tsx     Tableau Embedding API v3 로더 + MarkSelectionChanged 리스너
    └── BondInsight.tsx      Section 3 — 파생지표 카드 4개, 백엔드/CSV/Tableau 3단계 fallback
```

`TableauEmbed.tsx`는 `<tableau-viz>` 커스텀 엘리먼트를 스크립트 로드 후 DOM에 직접 붙이는 방식(React 19의 커스텀 엘리먼트 타입 이슈를 피하기 위해 `useRef` + `createElement` 사용). 스크립트는 `<script>` 태그가 아니라 `new Function('specifier','return import(specifier)')`로 동적 `import()`해서 `TableauEventType` named export를 가져온다 (1-6 참고 — `window.tableau` 방식은 안 됨).

---

## 4. 다음에 다시 정할 것들 (지금은 보류)

- **로컬 개발 시 FastAPI 백엔드를 매번 켜야 하는 번거로움** — `uvicorn backend.app.main:app --port 8000`을 수동으로 켜야 Bond Insight/Market Overview가 진짜 값을 보여줌. 스크립트나 `concurrently` 같은 걸로 프론트+백엔드 동시 실행을 편하게 만들지 검토
- ~~`frontend/src/app/api/bond-insight/route.ts`가 `yunseo/output` 로컬 CSV를 읽는 부분~~ → 5절 배포 준비하면서 `frontend/src/data/`로 CSV를 복사해오는 방식으로 해결함. **yunseo가 CSV를 다시 만들면 `frontend/src/data/`의 사본도 같이 다시 복사해야 함** (자동 동기화 안 됨 — 잊기 쉬우니 주의)
- 채권 상세·비교 화면이 필요해지면, 그때 페이지 분리 여부를 다시 논의 (1-1의 "일단 뺐다"는 결정은 최종이 아니라 이번 범위 한정)
- GitHub 이슈(#11~#19)를 이 구현 결과에 맞게 다시 정리할지, 아니면 완전히 새 이슈로 대체할지
- Bond Screener를 계속 Tableau 임베드로 둘지, 아니면 자체 React 구현으로 바꿔서 우리 백엔드와 연결할지 (1-9 참고, 지금은 연결 안 하기로 확정)

---

## 5. 배포 (2026-08-12)

| 구성요소 | 플랫폼 | URL | 배포 브랜치 |
| --- | --- | --- | --- |
| Backend (FastAPI) | Render | `https://bond-insight-backend.onrender.com` | `feature/yunseo` (main 아님, PR 시도했으나 organization 접근 문제로 보류) |
| Frontend (Next.js) | Vercel | `https://frontend-sigma-gold-68.vercel.app` | `feature/yunseo` |

### 5-1. 배포 전 반드시 고쳐야 했던 것들

- **CORS**: `backend/app/main.py`가 `localhost`만 하드코딩되어 있어서, `ALLOWED_ORIGINS` 환경변수(콤마 구분)로 뺌 (`backend/app/config.py`). Render 환경변수에 실제 Vercel 도메인을 넣어야 브라우저에서 `/api/market` 같은 걸 직접 호출하는 Market Overview가 안 막힘. **주의**: Render Blueprint(`render.yaml`)로 배포했는데도 `ALLOWED_ORIGINS`가 자동으로 안 채워져서 수동으로 추가해야 했음 — Render 콘솔에서 `sync: false` 환경변수가 항상 자동으로 프롬프트되는 건 아닌 듯.
- **`/api/bond-insight`의 로컬 파일 의존**: 원래 `yunseo/output/*.csv`(레포 루트, `frontend/` 밖)를 읽었는데, Vercel은 `frontend/` 디렉터리만 배포 대상으로 삼아서 그 경로가 배포 환경엔 없었음. CSV 2개(`기본 데이터.csv`, `파생 데이터.csv`)를 `frontend/src/data/`로 복사해오고, `route.ts`가 `process.cwd()/src/data/`를 읽도록 수정. `next start`(프로덕션 빌드)로 로컬에서 먼저 검증 후 배포함.
- **Vercel 프로젝트의 Output Directory 오설정**: 기존에 연결된 Vercel 프로젝트(`yunseo5/frontend`)의 Output Directory가 `dist`로 잡혀 있어서(다른 프레임워크로 설정됐던 흔적으로 추정) 첫 배포가 실패함. `frontend/vercel.json`에 `"framework": "nextjs"`, `"outputDirectory": ".next"`를 명시해서 해결.
- **`NEXT_PUBLIC_API_URL`**: Vercel 프로젝트 환경변수(Production)에 Render 백엔드 URL을 설정. `NEXT_PUBLIC_` 접두사라 빌드 타임에 클라이언트 번들에 박히므로, 이 값을 바꾸면 재배포해야 반영됨.

### 5-2. 배포 방법 (재배포 시 참고)

- **Backend**: Render가 GitHub 연결된 브랜치에 push될 때마다 자동 재배포함 (Render 프로젝트 설정에서 Auto-Deploy 켜져 있는 경우). 수동 배포는 Render 대시보드에서 Manual Deploy.
- **Frontend**: `cd frontend && vercel --prod --yes` (CLI로 로그인된 상태에서). Git 연동 auto-deploy는 별도로 설정 안 했음 — 지금은 커맨드라인으로 수동 배포하는 방식.

### 5-3. 아직 안 된 것 (다음에 할 일)

- main 브랜치로 옮기기 (organization 권한 이슈로 `feature/yunseo`에서 바로 배포한 상태)
- Vercel Git 연동으로 push 시 자동 배포 설정 (지금은 수동 `vercel --prod`)
- Render 무료 플랜은 15분 무활동 시 슬립 → 첫 요청 30~50초 지연 (콜드 스타트), 실사용 트래픽 생기면 유료 플랜 검토
