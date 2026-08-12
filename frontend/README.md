# Bond Insight Frontend

Next.js App Router 기반 Bond Insight 웹 클라이언트다.

## 시작하기

```powershell
Copy-Item .env.example .env.local
npm install
npm run dev
```

기본 주소는 `http://localhost:3000`이다. Backend는 기본적으로 `http://127.0.0.1:8000`을 사용한다.

## 환경변수

| 이름 | 기본값 | 설명 |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | FastAPI 공개 기본 URL |

## 명령어

```powershell
npm run dev
npm run lint
npm run typecheck
npm run build
npm run start
```
