# Bond Insight 문서 안내

프로젝트의 설계, API, 데이터베이스 및 데이터 정의 문서를 모아둔 폴더입니다.

| 문서 | 내용 |
|---|---|
| `architecture.md` | 전체 시스템 구조와 데이터 흐름 |
| `api_spec.md` | 백엔드 API 명세 |
| `database-erd.md` | Supabase PostgreSQL 테이블과 관계 |
| `data_dictionary.md` | 데이터 컬럼과 지표 정의 |
| `project-plan.md` | 프로젝트 단계별 계획 및 진행 기록 |
| `sql/bond_snapshot.sql` | `bond_snapshot` 테이블 생성 SQL |

구성 요소별 실행 및 운영 방법은 다음 README를 참고합니다.

- `backend/README.md`: FastAPI, 환경변수, API, Render 배포
- `frontend/README.md`: Next.js, 정적 데이터 연결, Vercel 배포
- `data/README.md`: CSV 파이프라인, Supabase 테이블, 적재 방법

> 일부 기존 상세 문서는 과거 작업 기록을 포함할 수 있습니다. 실제 실행 명령과 현재 데이터 연결 방식은 각 구성 요소의 README를 우선 기준으로 사용합니다.

