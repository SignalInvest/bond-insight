"use client";

import { useState } from "react";

import { BondInsight } from "./BondInsight";
import { BondScreener } from "./BondScreener";
import { MarketOverview } from "./MarketOverview";

export function DashboardBody() {
  const [selectedBond, setSelectedBond] = useState<Record<string, string> | null>(null);

  return (
    <main className="mx-auto flex max-w-[1300px] flex-col gap-8 px-6 py-8">
      <MarketOverview />

      {/* Bond Insight는 오른쪽 배치 유지. Tableau가 1200px 고정 폭이라 이 칸(2/3 폭)보다 넓어서
          TableauEmbed 안쪽에서 가로 스크롤로 처리됨(min-w-0 필요) — docs/SKILL.md 참고. */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <BondScreener onSelectBond={setSelectedBond} />
        </div>
        <BondInsight selectedFields={selectedBond} />
      </div>
    </main>
  );
}
