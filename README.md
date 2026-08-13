# Bond Insight

채권 초보 투자자가 시장 상황을 이해하고, 채권을 탐색·비교하며, 수익과 위험을 해석할 수 있도록 돕는 채권 분석 대시보드입니다.

## 주요 기능

- 기준금리, 국고채 금리, 장단기 금리차, CPI 기반 시장 개요
- 채권 종류·신용등급·잔존만기·채권명 검색 및 필터
- YTM, 표면금리, 잔존만기, Modified Duration 비교
- 세후 예상수익률, 금리 민감도, 투자 성향 파생지표
- 선택한 채권의 상세 분석 및 AI 설명
- Supabase 기반 채권·시장금리·분석 API

## 시스템 구성

```text
외부 금융 API
  ├── 한국은행 ECOS
  └── 채권 정보·시세 API
          ↓
Python 수집·정제·분석
          ↓
Raw / Processed CSV
      ├──────────────→ Tableau
      ├──────────────→ 현재 Next.js 정적 화면
      └──────────────→ Supabase PostgreSQL
                              ↓
                           FastAPI
                              ↓
                     동적 조회 API / AI 설명
```

현재 메인 웹 화면은 정적 CSV를 읽습니다. Supabase와 FastAPI 기반 동적 조회 코드도 구현되어 있지만 메인 페이지에는 아직 연결하지 않았습니다. 따라서 CSV 변경사항은 프론트엔드를 다시 빌드하고 배포해야 반영됩니다.

## 기술 스택

| 영역 | 기술 |
|---|---|
| 데이터 수집·처리 | Python, Pandas, Requests |
| 분석 | 잔존만기, Duration, Spread, 세후수익률, 민감도·성향 분류 |
| 데이터베이스 | Supabase PostgreSQL |
| 백엔드 | FastAPI, Uvicorn, Supabase Python Client |
| 프론트엔드 | Next.js 16, React, TypeScript, Tailwind CSS 4 |
| AI | Gemini 또는 OpenAI |
| 배포 | Vercel, Render |

## 프로젝트 구조

```text
Bond-Dashboard/
├── backend/       # FastAPI API와 서비스 로직
├── data/          # 원본 및 가공 CSV, 데이터베이스 안내
├── docs/          # 아키텍처, API, ERD, 데이터 사전
├── frontend/      # Next.js 대시보드
├── src/
│   ├── collection/  # 외부 API 수집
│   ├── processing/  # 정제·통합
│   ├── analysis/    # 금융 파생지표 계산
│   └── loading/     # Supabase 적재
├── tableau/       # Tableau 관련 자료
├── tests/         # Python 테스트
├── .env.example
└── render.yaml
```

## 빠른 시작

### 1. 저장소 및 Python 환경

```powershell
git clone https://github.com/SignalInvest/bond-insight.git
cd bond-insight
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`.env`에 필요한 API 키와 Supabase 연결값을 설정합니다. 실제 키는 Git에 커밋하지 않습니다.

### 2. 백엔드 실행

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 3. 프론트엔드 실행

```powershell
cd frontend
npm install
npm run dev
```

Chrome에서 `http://127.0.0.1:3000`을 엽니다.

## 환경변수

| 변수 | 용도 |
|---|---|
| `ECOS_API_KEY` | 한국은행 ECOS 데이터 수집 |
| `BOND_INFO_API_KEY` | 채권 기본정보 수집 |
| `FSC_API_KEY` | 금융 공공데이터 수집 |
| `KIS_APP_KEY`, `KIS_APP_SECRET` | 한국투자증권 API |
| `SUPABASE_URL`, `SUPABASE_KEY` | 백엔드의 Supabase 연결 |
| `AI_PROVIDER` | `gemini` 또는 `openai` |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Gemini 설정 |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | OpenAI 설정 |
| `ALLOWED_ORIGINS` | FastAPI CORS 허용 도메인 |
| `NEXT_PUBLIC_API_URL` | 프론트엔드에서 사용할 FastAPI URL |

## 데이터 파이프라인

대표 실행 흐름은 다음과 같습니다.

```powershell
python -u src\collection\collect_ecos.py
python -u src\analysis\calculate_metrics.py
python -u src\analysis\calculate_duration.py
python -u src\analysis\calculate_credit_spread.py
python -u src\analysis\calculate_after_tax_yield.py
```

Supabase 적재:

```powershell
python -u src\loading\upload_supabase.py --table all
python -u src\loading\upload_bond_snapshot.py
```

스크립트를 실행하기 전에 입력 파일, 기준일, 환경변수를 확인하세요. 상세한 데이터 흐름과 테이블 구조는 `data/README.md`를 참고합니다.

## 테스트와 빌드

백엔드 및 데이터 로직:

```powershell
python -m pytest -q
```

프론트엔드:

```powershell
cd frontend
npm run lint
npm run typecheck
npm run build
```

## 배포

- 프론트엔드: Vercel
- 백엔드: Render (`render.yaml`)
- 데이터베이스: Supabase PostgreSQL

Vercel Git 자동 배포가 설정되어 있지 않은 환경에서는 GitHub push 또는 PR merge만으로 운영 사이트가 갱신되지 않습니다. Preview를 먼저 확인한 뒤 Production 배포를 실행하세요.

```powershell
cd frontend
npx vercel deploy
npx vercel deploy --prod
```

## 상세 문서

- [백엔드 안내](backend/README.md)
- [프론트엔드 안내](frontend/README.md)
- [데이터 및 데이터베이스 안내](data/README.md)
- [문서 목록](docs/README.md)
- [API 명세](docs/api_spec.md)
- [데이터베이스 ERD](docs/database-erd.md)
- [데이터 사전](docs/data_dictionary.md)

## 보안 원칙

- `.env`와 실제 API 키는 Git에 포함하지 않습니다.
- Supabase Secret/Service Role 키를 프론트엔드에 노출하지 않습니다.
- 외부에 공개되는 `NEXT_PUBLIC_` 환경변수에는 비밀값을 저장하지 않습니다.
- 운영 CORS는 필요한 프론트엔드 도메인만 허용합니다.

## 면책

이 프로젝트가 제공하는 분석과 AI 설명은 학습 및 정보 제공 목적이며, 특정 채권의 매수·매도를 권유하는 투자 자문이 아닙니다.
