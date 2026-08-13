"use client";

import { CalendarDays, Landmark } from "lucide-react";

import { useMarketSnapshot } from "@/lib/useMarketSnapshot";

interface HeaderProps {
  referenceDate: string;
  onReferenceDateChange: (value: string) => void;
}

export function Header({ referenceDate, onReferenceDateChange }: HeaderProps) {
  const snapshot = useMarketSnapshot(referenceDate);

  const summaryText =
    snapshot.status === "loaded"
      ? snapshot.marketStatus.description
      : snapshot.status === "empty"
        ? "선택한 날짜에는 시장 데이터가 없어요"
        : snapshot.status === "error"
          ? "시장 데이터를 불러오지 못했어요"
          : "채권시장 요약을 불러오는 중이에요";

  return (
    <header className="bg-navy-900 text-cream-50">
      <div className="mx-auto flex max-w-[1300px] flex-wrap items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-gold-500 text-gold-400">
            <Landmark size={20} />
          </span>
          <div>
            <p className="text-lg font-bold tracking-wide text-gold-400">BOND BRIDGE</p>
            <p className="text-xs text-cream-100/70">채권 투자 첫걸음 대시보드</p>
          </div>
        </div>

        <div className="flex items-center gap-6 text-cream-100/80">
          <div className="flex items-center gap-2 text-xs">
            <CalendarDays size={16} className="text-gold-400" />
            <div>
              <p className="opacity-70">기준일</p>
              <input
                type="date"
                value={referenceDate}
                onChange={(event) => onReferenceDateChange(event.target.value)}
                style={{ colorScheme: "dark" }}
                className="rounded-md border border-gold-500/40 bg-navy-800 px-2 py-1 text-sm font-semibold text-cream-50"
              />
            </div>
          </div>

          <div className="hidden border-l border-cream-100/20 pl-6 sm:block">
            <p className="text-xs font-semibold text-gold-400">오늘의 한 줄 요약</p>
            <p className="mt-1 max-w-xs text-sm text-cream-50">{summaryText}</p>
            <p className="text-[11px] text-cream-100/60">{referenceDate} 기준</p>
          </div>
        </div>
      </div>
    </header>
  );
}
