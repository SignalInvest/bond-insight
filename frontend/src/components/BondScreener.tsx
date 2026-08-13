"use client";

import { Loader2, Search } from "lucide-react";
import { useMemo, useState } from "react";

import {
  MATURITY_BUCKETS,
  buildDisplayTags,
  formatRemainingMaturity,
  maturityBucketOf,
  type DisplayTag,
  type MaturityTag,
  type StrategyTag,
} from "@/lib/bondSnapshot";
import { useBondSnapshots } from "@/lib/useBondSnapshots";
import type { BondSnapshotRow } from "@/types/api";

const TAG_STYLES: Record<string, string> = {
  "안정성 중심": "bg-navy-900/5 text-navy-800",
  "수익률 중심": "bg-gold-500/15 text-gold-700",
  "단기채": "bg-navy-900/5 text-navy-800",
  "장기채": "bg-navy-900/5 text-navy-800",
  "거래 활발": "bg-up/10 text-up",
  "수익률 높음": "bg-up/10 text-up",
};

interface BondScreenerProps {
  referenceDate: string;
  selectedIsin?: string | null;
  onSelectBond?: (bond: BondSnapshotRow | null) => void;
}

export function BondScreener({ referenceDate, selectedIsin, onSelectBond }: BondScreenerProps) {
  const snapshot = useBondSnapshots(referenceDate);
  const bonds = useMemo(() => (snapshot.status === "loaded" ? snapshot.bonds : []), [snapshot]);
  const tagsByIsin = useMemo(() => buildDisplayTags(bonds), [bonds]);

  const [bondType, setBondType] = useState<string | null>(null);
  const [strategy, setStrategy] = useState<StrategyTag | null>(null);
  const [maturityTag, setMaturityTag] = useState<MaturityTag | null>(null);
  const [ratingFilter, setRatingFilter] = useState<string>("전체");
  const [maturityBucket, setMaturityBucket] = useState<string>("전체");
  const [search, setSearch] = useState("");

  const bondTypeOptions = useMemo(
    () => Array.from(new Set(bonds.map((b) => b.bond_type).filter((v): v is string => v !== null))).sort(),
    [bonds],
  );
  const ratingOptions = useMemo(
    () => Array.from(new Set(bonds.map((b) => b.credit_rating).filter((v): v is string => v !== null))).sort(),
    [bonds],
  );

  const filteredBonds = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    return bonds.filter((bond) => {
      const tags = tagsByIsin.get(bond.isin_code) ?? [];
      if (bondType && bond.bond_type !== bondType) return false;
      if (strategy && !tags.includes(strategy)) return false;
      if (maturityTag && !tags.includes(maturityTag)) return false;
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
  }, [bonds, tagsByIsin, bondType, strategy, maturityTag, ratingFilter, maturityBucket, search]);

  function resetGroups() {
    setBondType(null);
    setStrategy(null);
    setMaturityTag(null);
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
        <FilterButton label="전체" active={!bondType && !strategy && !maturityTag} onClick={resetGroups} />
        <FilterButton label="국채" active={bondType === "국채"} onClick={() => setBondType(bondType === "국채" ? null : "국채")} />
        <FilterButton
          label="회사채"
          active={bondType === "회사채"}
          onClick={() => setBondType(bondType === "회사채" ? null : "회사채")}
        />
        <FilterButton
          label="안정성 중심"
          active={strategy === "안정성 중심"}
          onClick={() => setStrategy(strategy === "안정성 중심" ? null : "안정성 중심")}
        />
        <FilterButton
          label="수익률 중심"
          active={strategy === "수익률 중심"}
          onClick={() => setStrategy(strategy === "수익률 중심" ? null : "수익률 중심")}
        />
        <FilterButton
          label="단기채"
          active={maturityTag === "단기채"}
          onClick={() => setMaturityTag(maturityTag === "단기채" ? null : "단기채")}
        />
        <FilterButton
          label="장기채"
          active={maturityTag === "장기채"}
          onClick={() => setMaturityTag(maturityTag === "장기채" ? null : "장기채")}
        />
      </div>

      <div className="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <label className="flex flex-col gap-1 text-xs text-ink-600">
          채권 종류
          <select
            value={bondType ?? "전체"}
            onChange={(event) => setBondType(event.target.value === "전체" ? null : event.target.value)}
            className="rounded-lg border border-gold-500/30 bg-white px-2 py-1.5 text-sm text-navy-900"
          >
            <option value="전체">전체</option>
            {bondTypeOptions.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>

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
                const tags: DisplayTag[] = tagsByIsin.get(bond.isin_code) ?? [];
                return (
                  <tr
                    key={bond.isin_code}
                    onClick={() => onSelectBond?.(bond)}
                    className={`cursor-pointer border-t border-gold-500/10 transition-colors hover:bg-cream-50 ${
                      isSelected ? "bg-cream-100" : ""
                    }`}
                  >
                    <td className="px-3 py-2">
                      <p className="font-medium text-navy-900">{bond.bond_name}</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {tags.map((tag) => (
                          <span
                            key={tag}
                            className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${TAG_STYLES[tag] ?? "bg-cream-100 text-ink-600"}`}
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
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
