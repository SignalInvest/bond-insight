import { Bell, CalendarDays, Landmark, UserCircle } from "lucide-react";

const REFERENCE_DATE = "2026.08.07";

export function Header() {
  return (
    <header className="bg-navy-900 text-cream-50">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-gold-500 text-gold-400">
            <Landmark size={20} />
          </span>
          <div>
            <p className="text-lg font-bold tracking-wide text-gold-400">BOND LEDGER</p>
            <p className="text-xs text-cream-100/70">채권 투자 첫걸음 대시보드</p>
          </div>
        </div>

        <nav className="hidden items-center gap-6 text-sm font-medium sm:flex">
          <span className="border-b-2 border-gold-500 pb-1 text-cream-50">Market</span>
        </nav>

        <div className="flex items-center gap-4 text-cream-100/80">
          <div className="hidden items-center gap-2 text-xs sm:flex">
            <CalendarDays size={16} />
            <div>
              <p className="opacity-70">기준월</p>
              <p className="font-semibold text-cream-50">{REFERENCE_DATE}</p>
            </div>
          </div>
          <Bell size={18} />
          <UserCircle size={20} />
        </div>
      </div>
    </header>
  );
}
