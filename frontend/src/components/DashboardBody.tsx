"use client";

import { useState } from "react";

import { BondInsight } from "./BondInsight";
import { BondScreener } from "./BondScreener";
import { MarketOverview } from "./MarketOverview";

export function DashboardBody() {
  const [selectedBond, setSelectedBond] = useState<Record<string, string> | null>(null);

  return (
    <main className="mx-auto flex max-w-6xl flex-col gap-8 px-6 py-8">
      <MarketOverview />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <BondScreener onSelectBond={setSelectedBond} />
        </div>
        <BondInsight selectedFields={selectedBond} />
      </div>
    </main>
  );
}
