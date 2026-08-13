export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}

export interface HealthResponse {
  status: "ok" | "unavailable";
}

// backend/app/services/market_service.py get_market_rates() 한 행
export interface MarketRatesRow {
  reference_date: string;
  base_rate: number;
  treasury_3y: number;
  treasury_5y: number;
  treasury_10y: number;
  corporate_aa_3y: number;
  yield_spread: number;
  credit_spread: number;
  policy_spread: number;
  // 2026-08-12 src/loading/upload_cpi.py로 추가 — 발표 전 달은 마지막 발표값이 이월되어 있음
  cpi_yoy: number | null;
}

// backend/app/api/market.py GET /api/market 응답
export interface MarketResponse {
  count: number;
  latest: MarketRatesRow | null;
  data: MarketRatesRow[];
}

// backend/app/api/ai.py POST /api/ai/explain 응답 (context는 화면에서 안 씀)
export interface AiExplainResponse {
  explanation: string;
  model: string;
}

// backend/app/services/bond_snapshot_service.py 한 행 (bond_snapshot 테이블, 2026-08-07 358건)
// remaining_days는 "일" 단위 — 년 단위로 쓰려면 반드시 365(.25)로 나눌 것 (docs/SKILL_1035.md 1절).
// relative_yield_spread가 "신용 스프레드"다. real_yield 컬럼은 업로드하지 않았음(1절 참고).
export interface BondSnapshotRow {
  id: number;
  isin_code: string;
  reference_date: string;
  bond_name: string;
  issuer: string | null;
  bond_type: string | null;
  credit_rating: string | null;
  issue_date: string | null;
  maturity_date: string;
  remaining_days: number | null;
  coupon_rate: number | null;
  close_price: number;
  ytm: number;
  volume: number | null;
  trading_value: number | null;
  has_option: boolean | null;
  is_fixed_rate: boolean | null;
  macaulay_duration: number | null;
  modified_duration: number | null;
  relative_yield_spread: number | null;
  // backend/app/services/bond_snapshot_service.py에서 계산해 붙임 (src/analysis/calculate_after_tax_yield.py와 동일 공식/가드).
  // status가 "CALCULATED"가 아니면 approx는 항상 null — status를 반드시 같이 확인할 것.
  after_tax_yield_approx: number | null;
  after_tax_yield_status: "CALCULATED" | "MISSING_YTM" | "MISSING_COUPON" | "OUTLIER_YTM";
}

// backend/app/api/bond_snapshot.py GET /api/bond-snapshot 응답
export interface BondSnapshotResponse {
  count: number;
  data: BondSnapshotRow[];
}
