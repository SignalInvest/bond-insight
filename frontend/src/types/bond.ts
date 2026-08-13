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
