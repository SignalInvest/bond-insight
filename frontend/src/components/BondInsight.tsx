"use client";

import { MousePointerClick, Sparkles } from "lucide-react";
import { useState } from "react";

import { formatRemainingMaturity } from "@/lib/bondSnapshot";
import type { BondSnapshotRow } from "@/types/api";

import { AiAnalysisPanel } from "./AiAnalysisPanel";

interface InsightMetric {
  label: string;
  value: string;
  caption: string;
}

function afterTaxYieldUnavailableReason(bond: BondSnapshotRow): string {
  if (bond.after_tax_yield_status === "OUTLIER_YTM") {
    return "YTM이 일반적 해석 범위를 벗어나 근사값을 표시하지 않아요";
  }
  if (bond.after_tax_yield_status === "MISSING_COUPON") {
    return "표면금리 데이터가 없어요";
  }
  return "YTM 데이터가 없어요";
}

function formatKoreanNumber(value: number, unit: string): string {
  const abs = Math.abs(value);
  if (abs >= 1_0000_0000) return `${(value / 1_0000_0000).toFixed(2)}억${unit}`;
  if (abs >= 10000) return `${(value / 10000).toFixed(0)}만${unit}`;
  return `${value.toLocaleString()}${unit}`;
}

function durationUnavailableReason(bond: BondSnapshotRow): string {
  if (bond.has_option) return "옵션부 채권이라 계산 대상에서 제외됐어요";
  if (bond.is_fixed_rate === false) return "변동금리 채권이라 계산 대상에서 제외됐어요";
  if (bond.remaining_days === null) return "영구채라 계산 대상에서 제외됐어요";
  return "계산에 필요한 데이터가 부족해요";
}

// 남색 블록 4지표 — 계산식은 mock 이전(백엔드/CSV 연동판)과 동일, 데이터 소스만
// bond_snapshot(Supabase)으로 바뀜 (docs/SKILL_1035.md Step 4).
function buildInsightMetrics(bond: BondSnapshotRow): InsightMetric[] {
  const isTreasury = bond.bond_type === "국채";

  return [
    {
      label: "오늘 거래량 (유동성)",
      value: bond.trading_value !== null ? formatKoreanNumber(bond.trading_value, "원") : "데이터 없음",
      caption: `${bond.reference_date} 기준 (Supabase)`,
    },
    {
      label: "세후 예상수익률",
      value:
        bond.after_tax_yield_approx !== null ? `${bond.after_tax_yield_approx.toFixed(2)}%` : "데이터 없음",
      caption:
        bond.after_tax_yield_approx !== null
          ? `세전 YTM ${bond.ytm.toFixed(2)}% − 표면금리 × 이자소득세 15.4% (근사값, Supabase 계산)`
          : afterTaxYieldUnavailableReason(bond),
    },
    {
      label: "신용 스프레드",
      value:
        isTreasury
          ? "해당 없음"
          : bond.relative_yield_spread !== null
            ? `${bond.relative_yield_spread >= 0 ? "+" : ""}${(bond.relative_yield_spread * 100).toFixed(0)}bp`
            : "데이터 없음",
      caption: isTreasury
        ? "국채는 스스로가 기준금리라 신용 스프레드가 의미 없어요"
        : bond.relative_yield_spread !== null
          ? "YTM − 잔존만기 보간 국고채 금리 (Supabase 계산값)"
          : "벤치마크 금리를 찾지 못했어요",
    },
    {
      label: "Duration (금리 민감도)",
      value: bond.modified_duration !== null ? bond.modified_duration.toFixed(2) : "데이터 없음",
      caption:
        bond.modified_duration !== null
          ? `금리 1%p 오르면 가격 약 -${bond.modified_duration.toFixed(2)}% 변동 (Supabase 계산값)`
          : durationUnavailableReason(bond),
    },
  ];
}

const DETAIL_FIELDS: { label: string; value: (bond: BondSnapshotRow) => string }[] = [
  { label: "채권명", value: (bond) => bond.bond_name },
  { label: "발행사", value: (bond) => bond.issuer ?? "-" },
  { label: "유형", value: (bond) => bond.bond_type ?? "-" },
  { label: "신용등급", value: (bond) => bond.credit_rating ?? "-" },
  { label: "잔존만기", value: formatRemainingMaturity },
  { label: "YTM(수익률)", value: (bond) => `${bond.ytm.toFixed(2)}%` },
  { label: "현재가격", value: (bond) => `${bond.close_price.toLocaleString()}원` },
];

interface BondInsightProps {
  selectedFields: BondSnapshotRow | null;
}

export function BondInsight({ selectedFields: bond }: BondInsightProps) {
  const [isAiOpen, setIsAiOpen] = useState(false);

  return (
    <section
      aria-labelledby="bond-overview-title"
      className="rounded-lg border border-gold-500/30 bg-white/60 p-5 shadow-sm"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="font-serif text-2xl leading-none text-gold-500">03</span>
          <div>
            <h2 id="bond-overview-title" className="text-xl font-bold text-ink-900">
              BOND OVERVIEW
            </h2>
            <p className="mt-1 flex items-center gap-1 text-sm text-ink-600">
              {bond ? (
                <>선택한 채권의 상세 정보예요.</>
              ) : (
                <>
                  <MousePointerClick size={14} /> 좌측에서 채권을 선택하면 상세 정보가 표시됩니다.
                </>
              )}
            </p>
          </div>
        </div>
        {bond && (
          <button
            type="button"
            onClick={() => setIsAiOpen(true)}
            className="flex shrink-0 items-center gap-1.5 rounded border border-gold-500 bg-navy-950 px-3.5 py-2 text-xs font-black tracking-wide text-cream-50"
          >
            <Sparkles size={13} className="text-gold-400" />
            AI Analysis
          </button>
        )}
      </div>

      {bond && isAiOpen && <AiAnalysisPanel bond={bond} onClose={() => setIsAiOpen(false)} />}

      {!bond ? (
        <div className="flex flex-col gap-3">
          {["오늘 거래량 (유동성)", "세후 예상수익률", "신용 스프레드", "Duration (금리 민감도)"].map((label) => (
            <div key={label} className="rounded bg-cream-50 p-3">
              <p className="text-xs text-ink-600">{label}</p>
              <p className="text-lg font-bold text-navy-900">-</p>
              <p className="text-xs text-ink-400">왼쪽 표에서 채권을 선택하세요</p>
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="mb-3.5">
            <p className="text-xl font-bold text-ink-900">{bond.bond_name}</p>
            <p className="mt-1 text-sm text-ink-600">
              {bond.bond_type ?? "-"} · {bond.credit_rating ?? "무등급"}
            </p>
          </div>

          <div className="mb-4 grid grid-cols-2 overflow-hidden rounded-lg bg-navy-950 text-cream-50">
            {buildInsightMetrics(bond).map((metric, index) => (
              <div key={metric.label} className={`p-4 ${index !== 0 ? "border-l border-gold-500/40" : ""}`}>
                <p className="mb-2 text-xs font-black text-gold-400">{metric.label}</p>
                <p className="text-xl font-bold text-cream-50">{metric.value}</p>
                <p className="mt-1 text-[11px] leading-tight text-cream-100/60">{metric.caption}</p>
              </div>
            ))}
          </div>

          <dl className="grid grid-cols-2 gap-x-5 gap-y-3.5">
            {DETAIL_FIELDS.map((field) => (
              <div key={field.label}>
                <dt className="text-xs font-extrabold text-ink-400">{field.label}</dt>
                <dd className="mt-0.5 font-bold text-ink-900">{field.value(bond)}</dd>
              </div>
            ))}
          </dl>
        </>
      )}
    </section>
  );
}
