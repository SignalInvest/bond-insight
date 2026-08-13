"use client";

import { useMarketSnapshot } from "@/lib/useMarketSnapshot";
import type { MarketStatus } from "@/lib/marketStatus";
import type { MarketRatesRow } from "@/types/api";

interface MarketKpi {
  label: string;
  value: string;
  caption: string;
}

// 2026-08-12 src/loading/upload_cpi.py로 market_rates.cpi_yoy 채워넣기 전까지 쓰던 값.
// 백엔드가 아예 안 켜져 있을 때(FALLBACK_KPIS)만 이 값을 씀.
const FALLBACK_KPIS: MarketKpi[] = [
  { label: "기준금리", value: "3.50%", caption: "정책금리 기준" },
  { label: "국고채 3Y", value: "3.25%", caption: "Policy Spread +0.75%p" },
  { label: "국고채 10Y", value: "3.38%", caption: "시장금리 기준" },
  { label: "장단기 금리차", value: "+13bp", caption: "10Y - 3Y" },
  { label: "CPI", value: "2.8%", caption: "최근 월 기준" },
];

const FALLBACK_STATUS: MarketStatus = {
  label: "정상 금리 구조",
  description: "장단기 금리차 +0.13%p, 장기금리가 단기금리보다 높은 구조입니다.",
  condition: "조건: Yield Spread(국고 10Y · 국고 3Y) > 0",
};

function buildKpis(latest: MarketRatesRow): MarketKpi[] {
  return [
    { label: "기준금리", value: `${latest.base_rate.toFixed(2)}%`, caption: "정책금리 기준" },
    {
      label: "국고채 3Y",
      value: `${latest.treasury_3y.toFixed(2)}%`,
      caption: `Policy Spread ${latest.policy_spread >= 0 ? "+" : ""}${latest.policy_spread.toFixed(2)}%p`,
    },
    { label: "국고채 10Y", value: `${latest.treasury_10y.toFixed(2)}%`, caption: "시장금리 기준" },
    {
      label: "장단기 금리차",
      value: `${latest.yield_spread >= 0 ? "+" : ""}${latest.yield_spread.toFixed(2)}%p`,
      caption: "10Y - 3Y",
    },
    {
      label: "CPI",
      value: latest.cpi_yoy !== null ? `${latest.cpi_yoy.toFixed(2)}%` : "데이터 없음",
      caption: "최근 월 기준",
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
        <div className="flex items-start gap-3">
          <span className="font-serif text-2xl leading-none text-gold-500">01</span>
          <div>
            <h2 id="bond-market-title" className="text-2xl font-bold text-ink-900">
              BOND MARKET
            </h2>
            <p className="mt-1 text-sm text-ink-600">지금 채권시장은 어떤 상황일까요?</p>
          </div>
        </div>
        <span className="text-[11px] text-ink-400">
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
        <div className="grid min-h-[220px] place-items-center rounded-lg border border-gold-500/30 bg-white/60 p-10 text-center shadow-sm">
          <p className="text-sm text-ink-600">
            {referenceDate} 기준 시장 데이터가 없어요. 상단에서 다른 기준일을 선택해 보세요.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-[1.4fr_repeat(5,1fr)]">
          <div className="min-h-[125px] rounded-lg border border-gold-500/30 bg-white/60 p-5 shadow-sm">
            <p className="mb-2.5 text-[13px] font-extrabold text-ink-900">시장상황</p>
            <p className="text-lg font-black leading-snug text-navy-950">{marketStatus.label}</p>
            <p className="mt-3 text-xs leading-relaxed text-ink-600">{marketStatus.description}</p>
            <p className="mt-2 text-[11px] text-ink-400">{marketStatus.condition}</p>
          </div>

          {kpis.map((kpi) => (
            <div key={kpi.label} className="min-h-[125px] rounded-lg border border-gold-500/30 bg-white/60 p-5 shadow-sm">
              <p className="mb-2.5 text-[13px] font-extrabold text-ink-900">{kpi.label}</p>
              <p className="font-serif text-3xl leading-tight text-navy-950">{kpi.value}</p>
              <p className="mt-3 text-xs leading-relaxed text-ink-600">{kpi.caption}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
