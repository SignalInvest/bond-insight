import { Search } from "lucide-react";

import { TableauEmbed } from "./TableauEmbed";

// public.tableau.com/app/profile/yunseo.lee6797/viz/yunseo_3h48m/1 의 임베드용 view URL
const TABLEAU_VIEW_URL = "https://public.tableau.com/views/yunseo_3h48m/1";

interface BondScreenerProps {
  onSelectBond?: (fields: Record<string, string> | null) => void;
}

export function BondScreener({ onSelectBond }: BondScreenerProps) {
  return (
    <section
      aria-labelledby="bond-screener-title"
      className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5"
    >
      <h2 id="bond-screener-title" className="mb-1 flex items-center gap-2 text-lg font-bold text-navy-900">
        <Search size={20} className="text-gold-600" />
        Bond Screener
      </h2>
      <p className="mb-4 text-xs text-ink-600">채권 행을 선택하면 오른쪽 Bond Insight에 상세 지표가 표시됩니다.</p>

      <TableauEmbed
        src={TABLEAU_VIEW_URL}
        className="w-full min-w-0 rounded-xl"
        onMarkSelectionChange={onSelectBond}
        height={900}
      />
    </section>
  );
}
