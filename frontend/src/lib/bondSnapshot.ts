import type { BondSnapshotRow } from "@/types/api";

// bond_snapshot.remaining_days는 "일" 단위 — 반드시 365로 나눠서 써야 함 (docs/SKILL_1035.md 1절).
export function remainingYears(bond: BondSnapshotRow): number | null {
  return bond.remaining_days === null ? null : bond.remaining_days / 365;
}

export const MATURITY_BUCKETS = ["1년 이하", "1~3년", "3~5년", "5~10년", "10년 이상", "영구채"] as const;
export type MaturityBucket = (typeof MATURITY_BUCKETS)[number];

// 라벨은 bond_metrics.maturity_bucket에서 실제 쓰던 값 그대로(docs/SKILL_1035.md 2-3).
// remaining_days가 없는 채권(영구채 등, 예: maturity_date "9999-12-31")은 "영구채"로 표시.
export function maturityBucketOf(bond: BondSnapshotRow): MaturityBucket {
  const years = remainingYears(bond);
  if (years === null) return "영구채";
  if (years <= 1) return "1년 이하";
  if (years <= 3) return "1~3년";
  if (years <= 5) return "3~5년";
  if (years <= 10) return "5~10년";
  return "10년 이상";
}

export function formatRemainingMaturity(bond: BondSnapshotRow): string {
  const years = remainingYears(bond);
  return years === null ? "영구채" : `${years.toFixed(2)}년`;
}

export type StrategyTag = "안정성 중심" | "수익률 중심";
export type MaturityTag = "단기채" | "장기채";
export type DisplayTag = StrategyTag | MaturityTag | "거래 활발" | "수익률 높음";

const STABLE_RATINGS = new Set(["AAA", "AA+", "AA", "AA-"]);

function percentileThreshold(values: number[], percentile: number): number {
  if (values.length === 0) return Infinity;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.min(sorted.length - 1, Math.floor(sorted.length * percentile));
  return sorted[index];
}

/**
 * mock 단계에서 손으로 붙였던 전략/거래 뱃지를 실데이터에서 계산하는 규칙 (docs/SKILL_1035.md 2-2).
 * DB에 이런 분류 컬럼이 없어서 클라이언트에서 전체 목록 기준으로 계산한다.
 */
export function buildDisplayTags(bonds: BondSnapshotRow[]): Map<string, DisplayTag[]> {
  const tradingValueP80 = percentileThreshold(
    bonds.map((b) => b.trading_value).filter((v): v is number => v !== null),
    0.8,
  );
  const ytmP90 = percentileThreshold(bonds.map((b) => b.ytm), 0.9);

  const tagsByIsin = new Map<string, DisplayTag[]>();
  for (const bond of bonds) {
    const tags: DisplayTag[] = [];
    const isStable = bond.bond_type === "국채" || (bond.credit_rating !== null && STABLE_RATINGS.has(bond.credit_rating));
    tags.push(isStable ? "안정성 중심" : "수익률 중심");

    const years = remainingYears(bond);
    if (years !== null) {
      if (years <= 3) tags.push("단기채");
      else if (years >= 10) tags.push("장기채");
    }

    if (bond.trading_value !== null && bond.trading_value >= tradingValueP80) tags.push("거래 활발");
    if (bond.ytm >= ytmP90) tags.push("수익률 높음");

    tagsByIsin.set(bond.isin_code, tags);
  }
  return tagsByIsin;
}
