# Bond Insight Frontend

Bond Insight의 Next.js App Router 기반 대시보드입니다. 시장 개요, 채권 스크리너, 채권 상세 분석 및 AI 분석 화면을 제공합니다.

## 기술 구성

- Next.js 16 App Router
- React / TypeScript
- Tailwind CSS 4
- Vercel 배포

## 현재 데이터 연결 방식

현재 메인 화면은 정적 CSV를 서버 컴포넌트에서 읽어 화면 데이터로 변환합니다.

```text
data/processed/tableau_bond_dashboard.csv
data/processed/market_rates_2026-08-01_07.csv
                    ↓
frontend/src/lib/bond-data.ts
                    ↓
frontend/src/app/page.tsx
                    ↓
frontend/src/app/bond-bridge-dashboard.tsx
```

Supabase를 조회하는 `/api/market`, `/api/bond-snapshot`용 클라이언트와 훅도 구현되어 있지만, 현재 메인 페이지는 이 경로를 사용하지 않습니다. 따라서 CSV 변경사항은 프론트엔드를 다시 빌드·배포해야 운영 화면에 반영됩니다.

## 폴더 구조

```text
frontend/
├── src/
│   ├── app/          # App Router 페이지, 레이아웃, 전역 스타일
│   ├── components/   # 대시보드 구성 요소
│   ├── lib/          # CSV 변환, API 클라이언트, 계산 유틸리티
│   └── types/        # TypeScript 타입
├── package.json
├── next.config.ts
└── vercel.json
```

## 로컬 실행

```powershell
cd frontend
npm install
npm run dev
```

Chrome에서 `http://127.0.0.1:3000` 또는 `http://localhost:3000`을 엽니다.

PowerShell 실행 정책으로 `npm.ps1`이 차단되는 경우 다음 명령을 사용합니다.

```powershell
& "C:\Program Files\nodejs\npm.cmd" run dev
```

## 환경변수

동적 API 연결 코드를 사용할 때 `frontend/.env.local`에 설정합니다.

```dotenv
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

`NEXT_PUBLIC_` 변수는 브라우저 번들에 포함되므로 비밀 키를 저장하면 안 됩니다.

## 명령어

```powershell
npm run dev       # 개발 서버
npm run lint      # ESLint
npm run typecheck # TypeScript 검사
npm run build     # 프로덕션 빌드
npm run start     # 프로덕션 서버
```

## 화면 구성

1. `BOND MARKET OVERVIEW`: 기준금리, 국고채 금리, 장단기 금리차, CPI
2. `BOND SCREENER`: 채권 검색·필터·수익률·듀레이션 비교
3. `BOND INSIGHT`: 선택한 채권의 상세 지표와 진단
4. `AI ANALYSIS`: 수익, 금리위험, 종합 성향 설명

## Vercel 배포

Preview 배포:

```powershell
cd frontend
npx vercel deploy
```

Production 배포:

```powershell
cd frontend
npx vercel deploy --prod
```

현재 Vercel Git 자동 배포가 설정되어 있지 않다면 GitHub에 push하거나 PR을 merge하는 것만으로 운영 사이트가 갱신되지 않습니다. 배포 전에 `npm run build`를 실행하고 Preview에서 화면을 확인하세요.
