"use client";

import { useEffect, useState } from "react";

import { getBondSnapshots } from "@/lib/api";
import type { BondSnapshotRow } from "@/types/api";

export type BondSnapshotsState =
  | { status: "loading" }
  | { status: "loaded"; bonds: BondSnapshotRow[] }
  | { status: "error" };

/** 기준일(referenceDate)에 해당하는 채권 스냅샷 358건을 한 번에 가져온다. */
export function useBondSnapshots(referenceDate: string): BondSnapshotsState {
  const [resolved, setResolved] = useState<{ date: string; state: BondSnapshotsState } | null>(null);

  useEffect(() => {
    let cancelled = false;

    getBondSnapshots({ referenceDate })
      .then((response) => {
        if (cancelled) return;
        setResolved({ date: referenceDate, state: { status: "loaded", bonds: response.data } });
      })
      .catch(() => {
        if (!cancelled) setResolved({ date: referenceDate, state: { status: "error" } });
      });

    return () => {
      cancelled = true;
    };
  }, [referenceDate]);

  // resolved가 이전 referenceDate에 대한 응답이면 render-time에 loading으로 파생 (useMarketSnapshot과 동일 패턴)
  return resolved && resolved.date === referenceDate ? resolved.state : { status: "loading" };
}
