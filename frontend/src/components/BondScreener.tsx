"use client";

import { Loader2, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { MATURITY_BUCKETS, formatRemainingMaturity, maturityBucketOf } from "@/lib/bondSnapshot";
import { useBondSnapshots } from "@/lib/useBondSnapshots";
import type { BondSnapshotRow } from "@/types/api";

interface BondScreenerProps {
  referenceDate: string;
  selectedIsin?: string | null;
  onSelectBond?: (bond: BondSnapshotRow | null) => void;
}

// 사용자가 Tableau에서 쓰던 필터 계산식 그대로 이식.
const STABLE_RATINGS = new Set(["AAA", "AA+", "AA0"]); // "안정성 중심" = 국채이거나 신용등급 AA0 이상
const HIGH_YIELD_THRESHOLD = 4; // "높은 수익률" = YTM 4% 이상
const SHORT_TERM_MAX_DAYS = 1095; // "단기" = 잔존만기 3년(1095일) 이하, "장기"는 초과

export function BondScreener({ referenceDate, selectedIsin, onSelectBond }: BondScreenerProps) {
  const snapshot = useBondSnapshots(referenceDate);
  const bonds = useMemo(() => (snapshot.status === "loaded" ? snapshot.bonds : []), [snapshot]);

  const [stableOnly, setStableOnly] = useState(false);
  const [highYieldOnly, setHighYieldOnly] = useState(false);
  const [shortTerm, setShortTerm] = useState(false);
  const [longTerm, setLongTerm] = useState(false);
  const [govBond, setGovBond] = useState(false);
  const [corpBond, setCorpBond] = useState(false);
  const [ratingFilter, setRatingFilter] = useState<string>("전체");
  const [maturityBucket, setMaturityBucket] = useState<string>("전체");
  const [search, setSearch] = useState("");

  const anyFilterActive = stableOnly || highYieldOnly || shortTerm || longTerm || govBond || corpBond;

  const ratingOptions = useMemo(
    () => Array.from(new Set(bonds.map((b) => b.credit_rating).filter((v): v is string => v !== null))).sort(),
    [bonds],
  );

  const filteredBonds = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return bonds.filter((bond) => {
      // 안정성 중심: 선택 안 했으면 통과, 선택했으면 국채이거나 신용등급 AA0 이상만
      if (stableOnly) {
        const isStable = bond.bond_type === "국채" || (bond.credit_rating !== null && STABLE_RATINGS.has(bond.credit_rating));
        if (!isStable) return false;
      }

      // 높은 수익률: 선택 안 했으면 통과, 선택했으면 YTM 4% 이상만
      if (highYieldOnly && bond.ytm < HIGH_YIELD_THRESHOLD) return false;

      // 단기/장기: 같은 그룹 내에서는 OR — 단기·장기 둘 다 선택하면 둘 다 보임, 하나도 선택 안 하면 전부 통과
      if (shortTerm || longTerm) {
        const days = bond.remaining_days;
        const matchesShort = shortTerm && days !== null && days <= SHORT_TERM_MAX_DAYS;
        const matchesLong = longTerm && days !== null && days > SHORT_TERM_MAX_DAYS;
        if (!matchesShort && !matchesLong) return false;
      }

      // 국채/회사채: 같은 그룹 내에서는 OR
      if (govBond || corpBond) {
        const matchesGov = govBond && bond.bond_type === "국채";
        const matchesCorp = corpBond && bond.bond_type === "회사채";
        if (!matchesGov && !matchesCorp) return false;
      }

      if (ratingFilter !== "전체" && bond.credit_rating !== ratingFilter) return false;
      if (maturityBucket !== "전체" && maturityBucketOf(bond) !== maturityBucket) return false;
      if (
        keyword &&
        !bond.bond_name.toLowerCase().includes(keyword) &&
        !bond.isin_code.toLowerCase().includes(keyword)
      ) {
        return false;
      }
      return true;
    });
  }, [bonds, stableOnly, highYieldOnly, shortTerm, longTerm, govBond, corpBond, ratingFilter, maturityBucket, search]);

  function resetGroups() {
    setStableOnly(false);
    setHighYieldOnly(false);
    setShortTerm(false);
    setLongTerm(false);
    setGovBond(false);
    setCorpBond(false);
  }

  return (
    <section
      aria-labelledby="bond-screener-title"
      className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5"
    >
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <h2 id="bond-screener-title" className="flex items-baseline gap-2">
            <span className="text-sm font-bold text-gold-600">02</span>
            <span className="text-lg font-bold text-navy-900">BOND SCREENER</span>
          </h2>
          <p className="text-xs text-ink-600">조건을 선택하거나 검색하여 관심 채권을 찾아보세요.</p>
        </div>
        <span className="text-xs text-ink-400">
          {snapshot.status === "loaded"
            ? bonds.length > 0
              ? `${referenceDate} 기준 ${bonds.length}건 (Supabase)`
              : "선택한 날짜에는 채권 데이터가 없어요"
            : snapshot.status === "error"
              ? "백엔드 연결 실패"
              : "불러오는 중..."}
        </span>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <FilterButton label="전체" active={!anyFilterActive} onClick={resetGroups} />
        <FilterButton label="국채" active={govBond} onClick={() => setGovBond((v) => !v)} />
        <FilterButton label="회사채" active={corpBond} onClick={() => setCorpBond((v) => !v)} />
        <FilterButton label="안정성 중심" active={stableOnly} onClick={() => setStableOnly((v) => !v)} />
        <FilterButton label="높은 수익률" active={highYieldOnly} onClick={() => setHighYieldOnly((v) => !v)} />
        <FilterButton label="단기" active={shortTerm} onClick={() => setShortTerm((v) => !v)} />
        <FilterButton label="장기" active={longTerm} onClick={() => setLongTerm((v) => !v)} />
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <label className="flex flex-col gap-1 text-xs text-ink-600">
          신용등급
          <select
            value={ratingFilter}
            onChange={(event) => setRatingFilter(event.target.value)}
            className="rounded-lg border border-gold-500/30 bg-white px-2 py-1.5 text-sm text-navy-900"
          >
            <option value="전체">전체</option>
            {ratingOptions.map((rating) => (
              <option key={rating} value={rating}>
                {rating}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-ink-600">
          잔존만기
          <select
            value={maturityBucket}
            onChange={(event) => setMaturityBucket(event.target.value)}
            className="rounded-lg border border-gold-500/30 bg-white px-2 py-1.5 text-sm text-navy-900"
          >
            <option value="전체">전체</option>
            {MATURITY_BUCKETS.map((bucket) => (
              <option key={bucket} value={bucket}>
                {bucket}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-ink-600">
          채권명 검색
          <div className="flex items-center gap-1.5 rounded-lg border border-gold-500/30 bg-white px-2 py-1.5">
            <Search size={14} className="text-ink-400" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="채권명 또는 종목코드 입력"
              className="w-full text-sm text-navy-900 outline-none placeholder:text-ink-400"
            />
          </div>
        </label>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gold-500/20">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="bg-navy-900 text-cream-50">
            <tr>
              <th className="px-3 py-2 font-semibold">채권명</th>
              <th className="px-3 py-2 font-semibold">발행사</th>
              <th className="px-3 py-2 font-semibold">유형</th>
              <th className="px-3 py-2 font-semibold">신용등급</th>
              <th className="px-3 py-2 font-semibold">잔존만기</th>
              <th className="px-3 py-2 font-semibold">YTM(수익률)</th>
              <th className="px-3 py-2 font-semibold">현재가격</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.status === "loading" ? (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-ink-400">
                  <span className="inline-flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" /> 불러오는 중...
                  </span>
                </td>
              </tr>
            ) : snapshot.status === "error" ? (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-down">
                  채권 데이터를 불러오지 못했어요. 백엔드가 켜져 있는지 확인해 주세요.
                </td>
              </tr>
            ) : filteredBonds.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-ink-400">
                  조건에 맞는 채권이 없어요.
                </td>
              </tr>
            ) : (
              filteredBonds.map((bond) => {
                const isSelected = bond.isin_code === selectedIsin;
                return (
                  <tr
                    key={bond.isin_code}
                    onClick={() => onSelectBond?.(bond)}
                    className={`cursor-pointer border-t border-gold-500/10 transition-colors hover:bg-cream-50 ${
                      isSelected ? "bg-cream-100" : ""
                    }`}
                  >
                    <td className="px-3 py-2 font-medium text-navy-900">{bond.bond_name}</td>
                    <td className="px-3 py-2 text-ink-700">{bond.issuer ?? "-"}</td>
                    <td className="px-3 py-2 text-ink-700">{bond.bond_type ?? "-"}</td>
                    <td className="px-3 py-2 text-ink-700">{bond.credit_rating ?? "-"}</td>
                    <td className="px-3 py-2 text-ink-700">{formatRemainingMaturity(bond)}</td>
                    <td className="px-3 py-2 font-semibold text-up">{bond.ytm.toFixed(2)}%</td>
                    <td className="px-3 py-2 text-ink-700">{bond.close_price.toLocaleString()}원</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FilterButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
        active
          ? "border-navy-900 bg-navy-900 text-cream-50"
          : "border-gold-500/30 bg-white text-ink-700 hover:border-gold-500"
      }`}
    >
      {label}
    </button>
  );
}
