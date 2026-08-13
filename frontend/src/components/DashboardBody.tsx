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
    <main className="mx-auto flex max-w-[1600px] flex-col gap-4 px-8 py-6">
      <MarketOverview referenceDate={referenceDate} />

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1.55fr)_minmax(420px,1fr)]">
        <div className="min-w-0">
          <BondScreener referenceDate={referenceDate} selectedIsin={selectedBond?.isin_code} onSelectBond={setSelectedBond} />
        </div>
        <BondInsight selectedFields={selectedBond} />
      </div>
    </main>
  );
}
