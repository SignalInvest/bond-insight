"use client";

import { CalendarDays, Landmark } from "lucide-react";

interface HeaderProps {
  referenceDate: string;
  onReferenceDateChange: (value: string) => void;
}

// PR#27(agent/bond-bridge-ui)의 배치를 참고 — 시장 요약 텍스트는 헤더에 중복 표시하지 않고
// 01 BOND MARKET의 "시장상황" 카드(넓은 첫 칸) 하나에서만 보여준다. 그래서 Header는 더 이상
// 시장 데이터를 조회할 필요가 없어짐(중복 fetch 제거).
export function Header({ referenceDate, onReferenceDateChange }: HeaderProps) {
  return (
    <header className="flex min-h-[104px] flex-wrap items-center justify-between gap-6 border-b-[3px] border-gold-500 bg-navy-950 px-8 py-5 text-cream-50">
      <div className="flex items-center gap-4">
        <span className="flex h-16 w-16 items-center justify-center rounded-lg border border-gold-500 text-gold-400">
          <Landmark size={30} />
        </span>
        <div>
          <p className="font-serif text-3xl tracking-[0.12em] text-cream-50">BOND BRIDGE</p>
          <p className="mt-1 text-sm font-bold text-gold-400">채권 투자 첫걸음 대시보드</p>
        </div>
      </div>

      <label className="grid gap-1.5">
        <span className="flex items-center gap-2 text-sm font-extrabold text-cream-100/90">
          <CalendarDays size={16} className="text-gold-400" />
          기준일
        </span>
        <input
          type="date"
          value={referenceDate}
          onChange={(event) => onReferenceDateChange(event.target.value)}
          style={{ colorScheme: "dark" }}
          className="h-9 w-40 rounded border border-gold-400/70 bg-white/10 px-2.5 text-sm font-semibold text-cream-50"
        />
      </label>
    </header>
  );
}
