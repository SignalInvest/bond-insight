# Bond Insight Backend

Bond Insight의 FastAPI 백엔드입니다. Supabase PostgreSQL에서 채권·시장금리·분석 데이터를 조회하고, 비교 및 AI 설명 API를 제공합니다.

## 기술 구성

- Python 3.13
- FastAPI / Uvicorn
- Supabase Python Client
- Pandas
- Gemini 또는 OpenAI 기반 AI 설명
- Render 배포

## 폴더 구조

```text
backend/
├── app/
│   ├── ai/          # AI 프롬프트 및 응답 생성
│   ├── api/         # FastAPI 라우터
│   ├── schemas/     # 요청·응답 스키마
│   ├── services/    # 데이터 조회 및 분석 로직
│   ├── config.py    # 환경변수 설정
│   ├── database.py  # Supabase 클라이언트
│   └── main.py      # 애플리케이션 진입점
└── requirements.txt
```

## 로컬 실행

프로젝트 루트에서 실행합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- 상태 확인: `http://127.0.0.1:8000/health`

## 환경변수

루트의 `.env.example`을 `.env`로 복사하고 값을 설정합니다.

| 변수 | 용도 |
|---|---|
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | 백엔드용 Supabase 키. 프론트엔드에 노출하지 않습니다. |
| `AI_PROVIDER` | `gemini` 또는 `openai` |
| `GEMINI_API_KEY` | Gemini 사용 시 API 키 |
| `GEMINI_MODEL` | Gemini 모델명 |
| `OPENAI_API_KEY` | OpenAI 사용 시 API 키 |
| `OPENAI_MODEL` | OpenAI 모델명 |
| `ALLOWED_ORIGINS` | CORS 허용 출처. 쉼표로 구분합니다. |

## 주요 API

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 상태 확인 |
| `GET` | `/api/database/health` | Supabase 연결 확인 |
| `GET` | `/api/market` | 기간별 시장금리 조회 |
| `GET` | `/api/bonds` | 채권 목록, 검색, 필터 및 정렬 |
| `GET` | `/api/bonds/{isin_code}` | 개별 채권 상세 조회 |
| `GET` | `/api/bond-snapshot` | 기준일별 화면용 채권 스냅샷 조회 |
| `GET` | `/api/analysis` | 채권 분석 지표 조회 |
| `GET` | `/api/analysis/risk-return` | 수익·금리위험·신용위험 데이터 조회 |
| `GET` | `/api/bonds/compare` | ISIN 2~5개 비교 |
| `POST` | `/api/compare` | 요청 본문을 이용한 채권 비교 |
| `POST` | `/api/ai/explain` | 개별 채권 AI 설명 |
| `POST` | `/api/ai/compare` | 복수 채권 AI 비교 설명 |

## 테스트

```powershell
python -m pytest -q
```

## 배포

Render 설정은 루트의 `render.yaml`에 있습니다.

```text
Build: pip install -r backend/requirements.txt
Start: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Render에는 `SUPABASE_URL`, `SUPABASE_KEY`, AI 키, `ALLOWED_ORIGINS`를 별도로 등록해야 합니다.

## 보안 주의사항

- Supabase Secret/Service Role 키를 Git에 커밋하거나 브라우저 코드에 포함하지 않습니다.
- AI API 키도 서버 환경변수로만 관리합니다.
- 운영 환경에서는 `ALLOWED_ORIGINS`를 실제 프론트엔드 도메인으로 제한합니다.

