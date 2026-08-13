"use client";

import { ArrowUpDown, Gauge, Landmark, Percent, ShoppingBasket } from "lucide-react";
import type { ComponentType } from "react";

import { useMarketSnapshot } from "@/lib/useMarketSnapshot";
import type { MarketStatus } from "@/lib/marketStatus";
import type { MarketRatesRow } from "@/types/api";

interface MarketKpi {
  label: string;
  value: string;
  caption: string;
  icon: ComponentType<{ size?: number }>;
}

// 2026-08-12 src/loading/upload_cpi.py로 market_rates.cpi_yoy 채워넣기 전까지 쓰던 값.
// 백엔드가 아예 안 켜져 있을 때(FALLBACK_KPIS)만 이 값을 씀.
const FALLBACK_KPIS: MarketKpi[] = [
  { label: "기준금리", value: "3.50%", caption: "정책금리 기준", icon: Percent },
  { label: "국고채 3Y", value: "3.25%", caption: "Policy Spread +0.75%p", icon: Landmark },
  { label: "국고채 10Y", value: "3.38%", caption: "시장금리 기준", icon: Landmark },
  { label: "장단기 금리차", value: "+13bp", caption: "10Y - 3Y", icon: ArrowUpDown },
  { label: "CPI", value: "2.8%", caption: "최근 월 기준", icon: ShoppingBasket },
];

const FALLBACK_STATUS: MarketStatus = {
  label: "정상 금리 구조",
  description: "장단기 금리차 +0.13%p, 장기금리가 단기금리보다 높은 구조입니다.",
  condition: "조건: Yield Spread(국고 10Y · 국고 3Y) > 0",
};

function buildKpis(latest: MarketRatesRow): MarketKpi[] {
  return [
    { label: "기준금리", value: `${latest.base_rate.toFixed(2)}%`, caption: "정책금리 기준", icon: Percent },
    {
      label: "국고채 3Y",
      value: `${latest.treasury_3y.toFixed(2)}%`,
      caption: `Policy Spread ${latest.policy_spread >= 0 ? "+" : ""}${latest.policy_spread.toFixed(2)}%p`,
      icon: Landmark,
    },
    { label: "국고채 10Y", value: `${latest.treasury_10y.toFixed(2)}%`, caption: "시장금리 기준", icon: Landmark },
    {
      label: "장단기 금리차",
      value: `${latest.yield_spread >= 0 ? "+" : ""}${latest.yield_spread.toFixed(2)}%p`,
      caption: "10Y - 3Y",
      icon: ArrowUpDown,
    },
    {
      label: "CPI",
      value: latest.cpi_yoy !== null ? `${latest.cpi_yoy.toFixed(2)}%` : "데이터 없음",
      caption: "최근 월 기준",
      icon: ShoppingBasket,
    },
  ];
}

interface MarketOverviewProps {
  referenceDate: string;
}

export function MarketOverview({ referenceDate }: MarketOverviewProps) {
  const snapshot = useMarketSnapshot(referenceDate);

  const kpis = snapshot.status === "loaded" ? buildKpis(snapshot.latest) : FALLBACK_KPIS;
  const marketStatus = snapshot.status === "loaded" ? snapshot.marketStatus : FALLBACK_STATUS;

  return (
    <section aria-labelledby="bond-market-title">
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <h2 id="bond-market-title" className="flex items-baseline gap-2">
            <span className="text-sm font-bold text-gold-600">01</span>
            <span className="text-lg font-bold text-navy-900">BOND MARKET</span>
          </h2>
          <p className="text-xs text-ink-600">지금 채권시장은 어떤 상황일까요?</p>
        </div>
        <span className="text-xs text-ink-400">
          {snapshot.status === "loaded"
            ? `${snapshot.latest.reference_date} 기준 (Supabase)`
            : snapshot.status === "empty"
              ? "선택한 날짜에는 데이터가 없어요"
              : snapshot.status === "error"
                ? "백엔드 연결 실패 — 예시 값 표시 중"
                : "불러오는 중..."}
        </span>
      </div>

      {snapshot.status === "empty" ? (
        <div className="rounded-2xl border border-gold-500/30 bg-white p-6 text-center text-sm text-ink-600 shadow-sm shadow-navy-900/5">
          {referenceDate} 기준 시장 데이터가 없어요. 상단에서 다른 기준일을 선택해 보세요.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5">
            <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-cream-100 text-gold-600">
              <Gauge size={18} />
            </span>
            <p className="text-xs text-ink-600">시장상황</p>
            <p className="mt-1 text-lg font-bold text-navy-900">{marketStatus.label}</p>
            <p className="mt-1 text-xs text-ink-600">{marketStatus.description}</p>
            <p className="mt-1 text-[11px] text-ink-400">{marketStatus.condition}</p>
          </div>

          {kpis.map((kpi) => (
            <div
              key={kpi.label}
              className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5"
            >
              <span className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-cream-100 text-gold-600">
                <kpi.icon size={18} />
              </span>
              <p className="text-xs text-ink-600">{kpi.label}</p>
              <p className="mt-1 text-2xl font-bold text-navy-900">{kpi.value}</p>
              <p className="mt-1 text-xs text-ink-400">{kpi.caption}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
