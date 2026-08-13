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
