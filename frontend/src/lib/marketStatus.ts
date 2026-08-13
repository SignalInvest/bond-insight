import type { MarketRatesRow } from "@/types/api";

export type MarketStatusLabel = "정상 금리 구조" | "상승 금리 구조" | "하락 금리 구조";

export interface MarketStatus {
  label: MarketStatusLabel;
  /** "장단기 금리차 +0.46%p, 장기금리가 단기금리보다 높은 구조입니다." 같은 한 줄 설명 */
  description: string;
  /** "조건: Yield Spread(국고 10Y · 국고 3Y) > 0" 같은 판정 조건 문구 */
  condition: string;
}

/**
 * docs/SKILL_1034.md 3-1 규칙:
 * - yield_spread(10Y-3Y) > 0 → 정상 금리 구조
 * - yield_spread ≤ 0(역전)이면서 기준금리가 전일 대비 상승 → 상승 금리 구조 (긴축 국면)
 * - yield_spread ≤ 0(역전)이면서 기준금리가 전일 대비 하락·보합 → 하락 금리 구조 (완화 국면)
 */
export function computeMarketStatus(latest: MarketRatesRow, previous?: MarketRatesRow): MarketStatus {
  const spread = latest.yield_spread;
  const spreadText = `장단기 금리차 ${spread >= 0 ? "+" : ""}${spread.toFixed(2)}%p`;

  if (spread > 0) {
    return {
      label: "정상 금리 구조",
      description: `${spreadText}, 장기금리가 단기금리보다 높은 구조입니다.`,
      condition: "조건: Yield Spread(국고 10Y · 국고 3Y) > 0",
    };
  }

  const baseRateDelta = previous ? latest.base_rate - previous.base_rate : 0;

  if (baseRateDelta > 0) {
    return {
      label: "상승 금리 구조",
      description: `${spreadText}, 장단기 금리가 역전된 가운데 기준금리가 오르는 추세입니다.`,
      condition: "조건: Yield Spread ≤ 0, 기준금리 전일 대비 상승",
    };
  }

  return {
    label: "하락 금리 구조",
    description: `${spreadText}, 장단기 금리가 역전된 가운데 기준금리가 내리거나 보합인 추세입니다.`,
    condition: "조건: Yield Spread ≤ 0, 기준금리 전일 대비 하락·보합",
  };
}
