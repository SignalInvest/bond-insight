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

### 1-5. 각 섹션의 데이터는 지금 단계에서 실데이터 연동 없이 목업 값 사용

- **결정**: Section 1(Market Overview)과 Section 3(Bond Insight)은 목업 이미지에 적힌 숫자를 그대로 코드에 넣는다. 실제 `/api/market`, `/api/analysis` 연동은 이번 범위에 포함하지 않는다.
- **왜**: 목업 이미지 자체에 "Section 1은 현재 임의 데이터"라고 적혀 있었고, 이번 작업의 목표는 "화면 골격을 목업대로 만드는 것"이라 데이터 연동은 다음 단계로 미룸.

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

| 지표 | 계산 방법 |
| --- | --- |
| 오늘 거래량 (유동성) | 오늘 하루 실제 거래된 수량·금액 |
| 실질수익률 (세후) | 세전 YTM × (1 − 15.4%) |
| 신용 스프레드 | 이 채권 YTM − 만기가 비슷한 국고채 금리 |
| Duration (금리 민감도) | 금리 1%p 변동 시 가격 변동폭 ≈ −Duration% |

값은 목업/예시 데이터이며, 실제 연동 전이라는 문구를 화면에 남겨서 오해를 방지함.

---

## 3. 컴포넌트 구조

```text
frontend/src/
├── app/
│   ├── globals.css        Tailwind + 커스텀 색상 토큰(@theme)
│   ├── layout.tsx          기존 유지
│   └── page.tsx             3개 섹션 조립
└── components/
    ├── Header.tsx           BOND LEDGER 로고, 날짜, 아이콘
    ├── MarketOverview.tsx   Section 1 — KPI 카드 5개
    ├── BondScreener.tsx     Section 2 — Tableau 임베드 컨테이너
    ├── TableauEmbed.tsx     Tableau Embedding API v3 로더 (재사용 가능)
    └── BondInsight.tsx      Section 3 — 파생지표 카드 4개
```

`TableauEmbed.tsx`는 `<tableau-viz>` 커스텀 엘리먼트를 스크립트 로드 후 DOM에 직접 붙이는 방식(React 19의 커스텀 엘리먼트 타입 이슈를 피하기 위해 `useRef` + `createElement` 사용).

---

## 4. 다음에 다시 정할 것들 (지금은 보류)

- Section 1 / Section 3을 실제 `/api/market`, `/api/analysis` 데이터에 연결하는 작업
- 채권 상세·비교 화면이 필요해지면, 그때 페이지 분리 여부를 다시 논의 (1-1의 "일단 뺐다"는 결정은 최종이 아니라 이번 범위 한정)
- GitHub 이슈(#11~#19)를 이 구현 결과에 맞게 다시 정리할지, 아니면 완전히 새 이슈로 대체할지
