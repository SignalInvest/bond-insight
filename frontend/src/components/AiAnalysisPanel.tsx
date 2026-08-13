"use client";

import { Loader2, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";

import type { MockBond } from "@/data/mockBonds";
import { ApiError, explainBond } from "@/lib/api";

type ExplainState =
  | { status: "loading" }
  | { status: "loaded"; explanation: string; model: string }
  | { status: "not-found" }
  | { status: "error"; message: string };

interface AiAnalysisPanelProps {
  bond: MockBond;
  onClose: () => void;
}

export function AiAnalysisPanel({ bond, onClose }: AiAnalysisPanelProps) {
  const [resolved, setResolved] = useState<{ isin: string; state: ExplainState } | null>(null);

  useEffect(() => {
    let cancelled = false;

    explainBond(bond.isin)
      .then((response) => {
        if (cancelled) return;
        setResolved({
          isin: bond.isin,
          state: { status: "loaded", explanation: response.explanation, model: response.model },
        });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        // mock ISIN이 Supabase에 없는 채권이면 404(NOT_FOUND) — docs/SKILL_1034.md 3-5
        if (error instanceof ApiError && error.code === "NOT_FOUND") {
          setResolved({ isin: bond.isin, state: { status: "not-found" } });
        } else {
          setResolved({
            isin: bond.isin,
            state: { status: "error", message: error instanceof Error ? error.message : "알 수 없는 오류" },
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [bond.isin]);

  // resolved가 이전 채권에 대한 응답이면 render-time에 loading으로 파생 (useMarketSnapshot과 동일 패턴)
  const state: ExplainState = resolved && resolved.isin === bond.isin ? resolved.state : { status: "loading" };

  return (
    <>
      <div className="fixed inset-0 z-40 bg-navy-950/40" onClick={onClose} aria-hidden="true" />
      <aside className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-gold-500/30 bg-white shadow-xl sm:w-1/3 sm:min-w-[360px]">
        <div className="flex items-center justify-between border-b border-gold-500/20 bg-navy-900 px-5 py-4 text-cream-50">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-gold-400" />
            <div>
              <p className="text-sm font-bold">AI Analysis</p>
              <p className="text-xs text-cream-100/70">{bond.bondName}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1 text-cream-100/80 hover:bg-cream-50/10 hover:text-cream-50"
            aria-label="닫기"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 text-sm text-ink-700">
          {state.status === "loading" && (
            <div className="flex items-center gap-2 text-ink-500">
              <Loader2 size={16} className="animate-spin" /> AI 분석을 불러오는 중이에요
            </div>
          )}
          {state.status === "not-found" && (
            <p className="text-ink-500">
              이 채권은 아직 AI 분석 데이터가 없어요. Bond Screener가 지금은 mock 데이터라 실제 Supabase 채권과
              매칭되지 않을 수 있어요 (DB 연동 후 해결될 예정).
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
