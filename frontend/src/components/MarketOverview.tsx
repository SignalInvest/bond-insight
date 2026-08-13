"use client";

import { ArrowUpDown, Landmark, Percent, ShoppingBasket, TrendingUp } from "lucide-react";
import { useEffect, useState } from "react";
import type { ComponentType } from "react";

import { getMarketRates } from "@/lib/api";
import type { MarketRatesRow } from "@/types/api";

type Direction = "up" | "down" | "flat";

interface MarketKpi {
  label: string;
  value: string;
  delta: string;
  direction: Direction;
  icon: ComponentType<{ size?: number }>;
}

// Bond Insight(개별 채권)가 2026-08-07 하루치 스냅샷만 있어서, 대시보드 전체를 같은 기준일로
// 맞추기 위해 market_rates도 최신값(2026-08-11) 대신 이 날짜로 고정. 채권 데이터가 매일
// 쌓이기 시작하면 이 고정을 풀고 다시 최신값(startDate/endDate 생략)을 쓰면 됨 — docs/SKILL.md 참고.
const DASHBOARD_REFERENCE_DATE = "2026-08-07";
const DASHBOARD_PREVIOUS_DATE = "2026-08-06";

// 2026-08-12 src/loading/upload_cpi.py로 market_rates.cpi_yoy 채워넣기 전까지 쓰던 값.
// 백엔드가 아예 안 켜져 있을 때(FALLBACK_KPIS)만 이 값을 씀.
const CPI_MOCK: MarketKpi = {
  label: "CPI (소비자물가지수)",
  value: "2.8%",
  delta: "-0.1%p",
  direction: "down",
  icon: ShoppingBasket,
};

const FALLBACK_KPIS: MarketKpi[] = [
  { label: "Base Rate (한국은행)", value: "3.50%", delta: "0.00%p", direction: "flat", icon: Percent },
  { label: "Gov 3Y (국고채 3년)", value: "3.25%", delta: "-0.03%p", direction: "down", icon: Landmark },
  { label: "Gov 10Y (국고채 10년)", value: "3.38%", delta: "-0.05%p", direction: "down", icon: Landmark },
  { label: "Yield Spread (국고 10Y - 3Y)", value: "13bp", delta: "+2bp", direction: "up", icon: ArrowUpDown },
  CPI_MOCK,
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

function direction(delta: number): Direction {
  if (Math.abs(delta) < 0.0005) return "flat";
  return delta > 0 ? "up" : "down";
}

function percentKpi(label: string, icon: ComponentType<{ size?: number }>, latest: number, delta: number): MarketKpi {
  return {
    label,
    value: `${latest.toFixed(2)}%`,
    delta: `${delta >= 0 ? "+" : ""}${delta.toFixed(2)}%p`,
    direction: direction(delta),
    icon,
  };
}

function cpiKpi(latest: MarketRatesRow, prev: MarketRatesRow): MarketKpi {
  if (latest.cpi_yoy === null) {
    return { label: "CPI (소비자물가지수, 전년比)", value: "데이터 없음", delta: "", direction: "flat", icon: ShoppingBasket };
  }
  const delta = prev.cpi_yoy === null ? 0 : latest.cpi_yoy - prev.cpi_yoy;
  return percentKpi("CPI (소비자물가지수, 전년比)", ShoppingBasket, latest.cpi_yoy, delta);
}

function buildKpisFromRows(latest: MarketRatesRow, previous: MarketRatesRow | undefined): MarketKpi[] {
  const prev = previous ?? latest; // 전일 데이터가 없으면 증감 0으로 표시
  const spreadBpLatest = latest.yield_spread * 100;
  const spreadBpDelta = (latest.yield_spread - prev.yield_spread) * 100;

  return [
    percentKpi("Base Rate (한국은행)", Percent, latest.base_rate, latest.base_rate - prev.base_rate),
    percentKpi("Gov 3Y (국고채 3년)", Landmark, latest.treasury_3y, latest.treasury_3y - prev.treasury_3y),
    percentKpi("Gov 10Y (국고채 10년)", Landmark, latest.treasury_10y, latest.treasury_10y - prev.treasury_10y),
    {
      label: "Yield Spread (국고 10Y - 3Y)",
      value: `${spreadBpLatest.toFixed(0)}bp`,
      delta: `${spreadBpDelta >= 0 ? "+" : ""}${spreadBpDelta.toFixed(0)}bp`,
      direction: direction(spreadBpDelta),
      icon: ArrowUpDown,
    },
    cpiKpi(latest, prev),
  ];
}

type State =
  | { status: "loading" }
  | { status: "loaded"; kpis: MarketKpi[]; referenceDate: string }
  | { status: "error" };

export function MarketOverview() {
  const [state, setState] = useState<State>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    getMarketRates({ limit: 2, startDate: DASHBOARD_PREVIOUS_DATE, endDate: DASHBOARD_REFERENCE_DATE })
      .then((response) => {
        if (cancelled) return;
        if (!response.latest) {
          setState({ status: "error" });
          return;
        }
        setState({
          status: "loaded",
          kpis: buildKpisFromRows(response.latest, response.data[1]),
          referenceDate: response.latest.reference_date,
        });
      })
      .catch(() => {
        if (!cancelled) setState({ status: "error" });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const kpis = state.status === "loaded" ? state.kpis : FALLBACK_KPIS;

  return (
    <section aria-labelledby="market-overview-title">
      <div className="mb-4 flex items-center justify-between">
        <h2 id="market-overview-title" className="flex items-center gap-2 text-lg font-bold text-navy-900">
          <TrendingUp size={20} className="text-gold-600" />
          Bond Market Overview Index
        </h2>
        <span className="text-xs text-ink-400">
          {state.status === "loaded"
            ? `${state.referenceDate} 기준 (Supabase)`
            : state.status === "error"
              ? "백엔드 연결 실패 — 예시 값 표시 중"
              : "불러오는 중..."}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
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
