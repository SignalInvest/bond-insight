"use client";

import { useEffect, useState } from "react";

import { getMarketRates } from "@/lib/api";
import { computeMarketStatus, type MarketStatus } from "@/lib/marketStatus";
import type { MarketRatesRow } from "@/types/api";

export type MarketSnapshotState =
  | { status: "loading" }
  | { status: "empty"; referenceDate: string }
  | { status: "error" }
  | { status: "loaded"; latest: MarketRatesRow; previous: MarketRatesRow | null; marketStatus: MarketStatus };

/**
 * 기준일(referenceDate)에 해당하는 시장금리 스냅샷을 가져온다.
 * 선택한 날짜에 정확히 일치하는 행이 없으면(과거 데이터에 없거나 미래 날짜) "empty" 상태를 반환한다 —
 * 더 과거 날짜의 값을 대신 보여주지 않는다 (docs/SKILL_1034.md 3-2).
 */
export function useMarketSnapshot(referenceDate: string): MarketSnapshotState {
  const [resolved, setResolved] = useState<{ date: string; state: MarketSnapshotState } | null>(null);

  useEffect(() => {
    let cancelled = false;

    getMarketRates({ endDate: referenceDate, limit: 2 })
      .then((response) => {
        if (cancelled) return;
        if (!response.latest || response.latest.reference_date !== referenceDate) {
          setResolved({ date: referenceDate, state: { status: "empty", referenceDate } });
          return;
        }
        const previous = response.data[1] ?? null;
        setResolved({
          date: referenceDate,
          state: {
            status: "loaded",
            latest: response.latest,
            previous,
            marketStatus: computeMarketStatus(response.latest, previous ?? undefined),
          },
        });
      })
      .catch(() => {
        if (!cancelled) setResolved({ date: referenceDate, state: { status: "error" } });
      });

    return () => {
      cancelled = true;
    };
  }, [referenceDate]);

  // resolved가 이전 referenceDate에 대한 응답이면(아직 이번 날짜 응답 전) render-time에 loading으로 파생시킴
  // (useEffect 안에서 동기적으로 setState하지 않기 위함 — react-hooks/set-state-in-effect, BondInsight.tsx와 동일 패턴)
  return resolved && resolved.date === referenceDate ? resolved.state : { status: "loading" };
}
