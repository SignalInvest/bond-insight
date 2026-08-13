"use client";

import { useState } from "react";

import type { BondSnapshotRow } from "@/types/api";

import { BondInsight } from "./BondInsight";
import { BondScreener } from "./BondScreener";
import { MarketOverview } from "./MarketOverview";

interface DashboardBodyProps {
  referenceDate: string;
}

export function DashboardBody({ referenceDate }: DashboardBodyProps) {
  const [selectedBond, setSelectedBond] = useState<BondSnapshotRow | null>(null);

  return (
    <main className="mx-auto flex max-w-[1300px] flex-col gap-8 px-6 py-8">
      <MarketOverview referenceDate={referenceDate} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <BondScreener referenceDate={referenceDate} selectedIsin={selectedBond?.isin_code} onSelectBond={setSelectedBond} />
        </div>
        <BondInsight selectedFields={selectedBond} />
      </div>
    </main>
  );
}
