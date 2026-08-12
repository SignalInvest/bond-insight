# 채권 CSV 3개 파이프라인 — 아키텍처

> `SKILL.md`(설계 노트)의 결정사항을 코드/파일 구조 관점에서 정리한 문서예요.
> "왜 이렇게 계산하는가"는 `SKILL.md`를 보고, "어디서 어디로 데이터가 흐르는가"는 이 문서를 보면 돼요.
> 범위는 이번에 만드는 3개 CSV 파이프라인으로 한정합니다 (DB/FastAPI/프론트엔드 연동은 다루지 않음).

---

## 1. 전체 흐름

```
[raw]                          [clean]                         [merge/derive]                 [output]

bond_info_raw.csv     ──▶  clean_bond_data.py   ──▶  bond_info_clean ─┐
                                                                        │
bond_market_raw.csv   ──▶  clean_market_data.py ──▶  bond_market_clean┤──▶ merge_data.py ──▶ 기본 데이터.csv   (표1)
                                                                        │        │
market_rates_daily.csv (이미 처리됨) ─────────────────────────────────┤        │
                                                                        │        ▼
cpi_monthly.csv (이미 처리됨) ──────────────────────────────────────────┘   시장 흐름 데이터.csv (표2)
                                                                                 │
                                                        기본 데이터.csv + 시장 흐름 데이터.csv
                                                                 │
                                                                 ▼
                                                      calculate_metrics.py
                                                                 │
                                                                 ▼
                                                      파생 데이터.csv (표3)
```

**표3(파생 데이터)은 표1·표2가 먼저 완성돼야 만들 수 있다** — 이게 이 파이프라인의 유일한 순서 제약이에요. 표1과 표2는 서로 독립적이라 병렬로 작업 가능.

---

## 2. 산출물 (output)

> **작업 범위 안내**: 이번 작업은 전부 `yunseo/` 폴더 안에서만 진행해요. 원본 프로젝트의 `data/`, `src/`는 **읽기만** 하고, 새로 만드는 스크립트와 결과 CSV는 전부 `yunseo/scripts/`, `yunseo/output/`에 둡니다. `src/processing/*.py` 같은 원본 프로젝트 파일은 건드리지 않아요 (나중에 이 로직을 정식으로 프로젝트에 편입할 때 참고용으로 씀).

| 파일 | 위치 | grain(행 하나의 단위) | 의존 |
| --- | --- | --- | --- |
| `기본 데이터.csv` | `yunseo/output/` | 채권(isin) × 날짜 | `data/raw/bond_info/bond_info_raw.csv` + `data/processed/bond_market.csv` |
| `시장 흐름 데이터.csv` | `yunseo/output/` | 날짜 | `data/processed/market_rates_daily.csv` + `data/processed/cpi_monthly.csv` |
| `파생 데이터.csv` | `yunseo/output/` | 채권(isin) × 날짜 | `기본 데이터.csv` + `시장 흐름 데이터.csv` |

`data/processed/`에 있는 `bond_market.csv`, `market_rates_daily.csv`, `cpi_monthly.csv`는 원본 프로젝트가 이미 만들어둔 정제 파일이라 **읽기 전용 입력**으로만 쓰고, 위 3개는 `yunseo/output/`에 새로 만드는 **분석용 최종 산출물**이에요.

---

## 3. 스크립트별 책임 (`yunseo/scripts/` 안에 위치)

| 스크립트 | 입력 | 출력 | 해야 할 일 |
| --- | --- | --- | --- |
| `yunseo/scripts/clean_bond_data.py` | `data/raw/bond_info/bond_info_raw.csv` (읽기 전용) | `yunseo/output/bond_info_clean.csv` (중간 산출물) | 날짜 형식 통일(`YYYYMMDD`→`YYYY-MM-DD`), `bond_type` 재분류(`SKILL.md` 1-1), `credit_rating` fallback 적용(`SKILL.md` 1-2), `interest_payment_cycle` 문자열→숫자(연간 지급횟수) 파싱, `has_option`/`is_fixed_rate` 플래그 컬럼 생성(`SKILL.md` 3-1) |
| `yunseo/scripts/clean_market_data.py` | `data/raw/bond_market/bond_market_raw.csv` (읽기 전용) | `yunseo/output/bond_market_clean.csv` (중간 산출물) | 날짜 형식 통일, 컬럼명 정리 (기존 `data/processed/bond_market.csv`와 동일한 결과가 나오는지 검증용으로도 사용) |
| `yunseo/scripts/merge_data.py` | `bond_info_clean.csv` + `data/processed/bond_market.csv`, `data/processed/market_rates_daily.csv` + `data/processed/cpi_monthly.csv` (읽기 전용) | `yunseo/output/기본 데이터.csv`, `yunseo/output/시장 흐름 데이터.csv` | isin 기준 조인(표1), date 기준 조인 + `cpi_yoy`/`short_rate_change`/`long_rate_change` 계산(표2). 매칭 안 되는 isin은 버리지 말고 결측으로 남긴 뒤 별도 로그 남기기 |
| `yunseo/scripts/calculate_metrics.py` | `yunseo/output/기본 데이터.csv` + `yunseo/output/시장 흐름 데이터.csv` | `yunseo/output/파생 데이터.csv` | date로 두 표 조인 → `is_fixed_rate & !has_option`인 채권만 duration류 계산, 나머지는 해당 컬럼 결측 처리 |

---

## 4. 표3 계산 대상 필터링 (아키텍처 상 중요한 분기점)

`파생 데이터.csv`를 만들 때 모든 채권을 계산하지 않고, `clean_bond_data.py`에서 미리 붙여둔 플래그로 걸러요.

```
기본 데이터.csv 한 행
     │
     ├─ is_fixed_rate == True  AND  has_option == False
     │        │
     │        ▼
     │   duration/sensitivity/expected_maturity_* 계산 (SKILL.md 3-1)
     │
     └─ 그 외 (변동금리 또는 옵션부)
              │
              ▼
         duration류는 결측(NaN)으로 남기고, real_yield/relative_yield_spread처럼
         현금흐름 스케줄이 필요 없는 값만 계산
```

이렇게 하면 "계산이 안 맞는 채권을 억지로 계산해서 틀린 숫자를 만드는" 대신, 어떤 채권이 왜 빠졌는지 데이터 자체에 남길 수 있어요.

---

## 5. 조인 키 정리

| 조인 | 키 | 방향 |
| --- | --- | --- |
| `bond_info_clean` + `bond_market_clean` | `isin` | left join (시세 기준, 정보 없는 채권은 결측) |
| `market_rates_daily` + `cpi_monthly` | `date` (월 단위 forward-fill) | left join (일별 기준) |
| `기본 데이터.csv` + `시장 흐름 데이터.csv` | `date` | left join (채권 기준) |

---

## 6. 확정된 값 (2026-08-11)

한때 미정이었던 3가지가 확정됐어요. 코드에는 이 값을 그대로 상수/매핑표로 반영하면 됩니다.

- `short_rate_change`/`long_rate_change`의 **N = 20영업일** (`SKILL.md` 2-2)
- `credit_rating` fallback 순서 = **KIS → FN → KBP → NICE** (`SKILL.md` 1-2)
- `bond_type` 매핑 = **국채(국채) / 지방채(지방채·지방공사채) / 특수채(특수채) / 금융채(금융채) / 회사채(일반회사채) / 유동화증권(유동화SPC채·MBS·SLBS·유사집합투자기구채)** 6종 (`SKILL.md` 1-1)

이 값을 바꿔야 할 필요가 생기면(예: 분석 목적이 바뀌어서 N을 다르게 잡아야 할 때) 코드를 먼저 고치지 말고 `SKILL.md`의 "결정된 값" 섹션부터 갱신하세요.
