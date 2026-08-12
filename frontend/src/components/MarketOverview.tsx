import { ArrowUpDown, Landmark, Percent, ShoppingBasket, TrendingUp } from "lucide-react";
import type { ComponentType } from "react";

type Direction = "up" | "down" | "flat";

interface MarketKpi {
  label: string;
  value: string;
  delta: string;
  direction: Direction;
  icon: ComponentType<{ size?: number }>;
}

// TODO: 실제 데이터 연동 전 예시 값 (docs/SKILL.md 2절 참고)
const KPIS: MarketKpi[] = [
  { label: "Base Rate (한국은행)", value: "3.50%", delta: "0.00%p", direction: "flat", icon: Percent },
  { label: "Gov 3Y (국고채 3년)", value: "3.25%", delta: "-0.03%p", direction: "down", icon: Landmark },
  { label: "Gov 10Y (국고채 10년)", value: "3.38%", delta: "-0.05%p", direction: "down", icon: Landmark },
  { label: "Yield Spread (국고 10Y - 3Y)", value: "13bp", delta: "+2bp", direction: "up", icon: ArrowUpDown },
  { label: "CPI (소비자물가지수)", value: "2.8%", delta: "-0.1%p", direction: "down", icon: ShoppingBasket },
];

const DELTA_STYLES: Record<Direction, string> = {
  up: "text-up",
  down: "text-down",
  flat: "text-ink-400",
};

const DELTA_PREFIX: Record<Direction, string> = {
  up: "↑ ",
  down: "↓ ",
  flat: "— ",
};

export function MarketOverview() {
  return (
    <section aria-labelledby="market-overview-title">
      <h2 id="market-overview-title" className="mb-4 flex items-center gap-2 text-lg font-bold text-navy-900">
        <TrendingUp size={20} className="text-gold-600" />
        Bond Market Overview Index
      </h2>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {KPIS.map((kpi) => (
          <div
            key={kpi.label}
            className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5"
          >
            <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-cream-100 text-gold-600">
              <kpi.icon size={18} />
            </span>
            <p className="text-xs text-ink-600">{kpi.label}</p>
            <p className="mt-1 text-2xl font-bold text-navy-900">{kpi.value}</p>
            <p className={`mt-1 text-xs font-medium ${DELTA_STYLES[kpi.direction]}`}>
              {DELTA_PREFIX[kpi.direction]}
              {kpi.delta}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
