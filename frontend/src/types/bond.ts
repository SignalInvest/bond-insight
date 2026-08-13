export interface BondRow {
  id: string;
  date: string;
  bondName: string;
  issuer: string | null;
  kind: string;
  rating: string | null;
  ytm: number;
  couponRate: number | null;
  remainingYears: number;
  remainingLabel: string;
  duration: number | null;
  currentPrice: number;
  volume: number;
  tradingValue: number;
  maturityDate: string;
  issueDate: string | null;
  treasury3y: number;
  treasury10y: number;
  baseRate: number;
  yieldSpread: number;
  creditSpread: number;
  policySpread: number;
  cpi: number | null;
  calculationStatus: string;
  // src/analysis/calculate_after_tax_yield.py와 동일 공식/가드로 bond-data.ts에서 계산.
  // status가 "CALCULATED"가 아니면 afterTaxYieldApprox는 항상 null.
  afterTaxYieldApprox: number | null;
  afterTaxYieldStatus: "CALCULATED" | "MISSING_YTM" | "MISSING_COUPON" | "OUTLIER_YTM";
  // src/analysis/classify_duration_sensitivity.py와 동일 임계값. duration이 null이면 null.
  durationSensitivity: "저민감" | "중간" | "고민감" | null;
  // src/analysis/classify_investment_priority.py와 동일 규칙. 신호가 2개 미만이면 null(판정불가).
  investmentPriority: "안정성 중심" | "수익률 중심" | "균형형" | null;
  tags: string[];
}

export interface MarketSnapshot {
  date: string;
  marketRateDate: string;
  baseRate: number;
  treasury3y: number;
  treasury10y: number;
  yieldSpread: number;
  creditSpread: number;
  policySpread: number;
  cpi: number | null;
  scenario: string;
  summary: string;
  summaryTitle: string;
  summaryLines: string[];
  rules: string[];
}

export interface BondDashboardData {
  bonds: BondRow[];
  markets: MarketSnapshot[];
  availableDates: string[];
}
