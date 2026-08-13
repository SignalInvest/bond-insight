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
