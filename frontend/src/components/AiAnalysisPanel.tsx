"use client";

import { Loader2, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { ApiError, explainBond } from "@/lib/api";
import type { BondSnapshotRow } from "@/types/api";

type ExplainState =
  | { status: "loading" }
  | { status: "loaded"; explanation: string; model: string }
  | { status: "not-found" }
  | { status: "error"; message: string };

interface AiAnalysisPanelProps {
  bond: BondSnapshotRow;
  onClose: () => void;
}

export function AiAnalysisPanel({ bond, onClose }: AiAnalysisPanelProps) {
  const [resolved, setResolved] = useState<{ isin: string; state: ExplainState } | null>(null);

  useEffect(() => {
    let cancelled = false;

    explainBond(bond.isin_code)
      .then((response) => {
        if (cancelled) return;
        setResolved({
          isin: bond.isin_code,
          state: { status: "loaded", explanation: response.explanation, model: response.model },
        });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        // bond_snapshot(358건) 중 극소수는 bonds 테이블(29,088건)에 없을 수 있음 — 404(NOT_FOUND)
        // (docs/SKILL_1035.md 1절: 358/359건은 겹침을 이미 확인함)
        if (error instanceof ApiError && error.code === "NOT_FOUND") {
          setResolved({ isin: bond.isin_code, state: { status: "not-found" } });
        } else {
          setResolved({
            isin: bond.isin_code,
            state: { status: "error", message: error instanceof Error ? error.message : "알 수 없는 오류" },
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [bond.isin_code]);

  // resolved가 이전 채권에 대한 응답이면 render-time에 loading으로 파생 (useMarketSnapshot과 동일 패턴)
  const state: ExplainState = resolved && resolved.isin === bond.isin_code ? resolved.state : { status: "loading" };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-navy-950/40 backdrop-blur-[2px]" onClick={onClose} aria-hidden="true" />
      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l-[3px] border-gold-500 bg-cream-50 p-7 shadow-2xl sm:w-1/3 sm:min-w-[380px]">
        <div className="mb-6 flex items-start justify-between gap-4">
          <div>
            <p className="flex items-center gap-1.5 text-xs font-black tracking-[0.1em] text-gold-500">
              <Sparkles size={13} />
              AI ANALYSIS
            </p>
            <h2 className="mt-1.5 text-xl font-bold text-navy-950">{bond.bond_name}</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded border border-gold-500/30 px-2.5 py-1.5 text-xs font-extrabold text-ink-900 hover:bg-white"
          >
            닫기
          </button>
        </div>

        <div className="flex-1 overflow-y-auto text-sm text-ink-700">
          {state.status === "loading" && (
            <div className="flex items-center gap-2 text-ink-500">
              <Loader2 size={16} className="animate-spin" /> AI 분석을 불러오는 중이에요
            </div>
          )}
          {state.status === "not-found" && (
            <p className="text-ink-500">
              이 채권은 아직 AI 분석 데이터가 없어요. bond_snapshot의 극소수 채권은 Supabase bonds 테이블과
              매칭되지 않을 수 있어요.
            </p>
          )}
          {state.status === "error" && <p className="text-down">AI 분석을 불러오지 못했어요: {state.message}</p>}
          {state.status === "loaded" && (
            <>
              <p className="whitespace-pre-wrap leading-relaxed">{state.explanation}</p>
              <p className="mt-4 text-[11px] text-ink-400">모델: {state.model}</p>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
