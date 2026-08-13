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
