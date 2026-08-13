"use client";

import { Activity, LineChart, MousePointerClick, Percent, ShieldAlert, Sparkles } from "lucide-react";
import { useState } from "react";
import type { ComponentType } from "react";

import type { MockBond } from "@/data/mockBonds";

import { AiAnalysisPanel } from "./AiAnalysisPanel";

interface InsightMetric {
  label: string;
  value: string;
  caption: string;
  icon: ComponentType<{ size?: number }>;
}

const WITHHOLDING_TAX_RATE = 0.154;

function formatKoreanNumber(value: number, unit: string): string {
  const abs = Math.abs(value);
  if (abs >= 1_0000_0000) return `${(value / 1_0000_0000).toFixed(2)}억${unit}`;
  if (abs >= 10000) return `${(value / 10000).toFixed(0)}만${unit}`;
  return `${value.toLocaleString()}${unit}`;
}

// 남색 블록 4지표 — 기존 BondInsight(백엔드/CSV 연동판)와 계산식은 동일하게 재사용,
// 데이터 소스만 mock 데이터로 바뀜 (docs/SKILL_1034.md 0-4, Step 3에서 Screener가 mock으로
// 바뀐 것과 같은 이유).
function buildInsightMetrics(bond: MockBond): InsightMetric[] {
  return [
    {
      label: "오늘 거래량 (유동성)",
      value: formatKoreanNumber(bond.tradingValue, "원"),
      caption: `${bond.maturityDate} 만기 · mock 데이터 기준`,
      icon: Activity,
    },
    {
      label: "실질수익률 (세후)",
      value: `${(bond.ytm * (1 - WITHHOLDING_TAX_RATE)).toFixed(2)}%`,
      caption: `세전 YTM ${bond.ytm.toFixed(2)}% × (1 − 이자소득세 15.4%)`,
      icon: Percent,
    },
    {
      label: "신용 스프레드",
      value: bond.creditSpread !== null ? `+${(bond.creditSpread * 100).toFixed(0)}bp` : "해당 없음",
      caption:
        bond.creditSpread !== null
          ? "YTM − 잔존만기 보간 국고채 금리"
          : "국채는 스스로가 기준금리라 신용 스프레드가 의미 없어요",
      icon: ShieldAlert,
    },
    {
      label: "Duration (금리 민감도)",
      value: bond.modifiedDuration.toFixed(2),
      caption: `금리 1%p 오르면 가격 약 -${bond.modifiedDuration.toFixed(2)}% 변동`,
      icon: LineChart,
    },
  ];
}

const DETAIL_FIELDS: { label: string; value: (bond: MockBond) => string }[] = [
  { label: "채권명", value: (bond) => bond.bondName },
  { label: "발행사", value: (bond) => bond.issuer },
  { label: "유형", value: (bond) => bond.bondType },
  { label: "신용등급", value: (bond) => bond.creditRating },
  { label: "잔존만기", value: (bond) => `${bond.remainingMaturityYears.toFixed(2)}년` },
  { label: "YTM(수익률)", value: (bond) => `${bond.ytm.toFixed(2)}%` },
  { label: "현재가격", value: (bond) => `${bond.price.toLocaleString()}원` },
];

interface BondInsightProps {
  selectedFields: MockBond | null;
}

export function BondInsight({ selectedFields: bond }: BondInsightProps) {
  const [isAiOpen, setIsAiOpen] = useState(false);

  return (
    <section
      aria-labelledby="bond-overview-title"
      className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5"
    >
      <div className="mb-4 flex items-start justify-between gap-2">
        <div>
          <h2 id="bond-overview-title" className="flex items-baseline gap-2">
            <span className="text-sm font-bold text-gold-600">03</span>
            <span className="text-lg font-bold text-navy-900">BOND OVERVIEW</span>
          </h2>
          <p className="flex items-center gap-1 text-xs text-ink-600">
            {bond ? (
              <>선택한 채권의 상세 정보예요.</>
            ) : (
              <>
                <MousePointerClick size={14} /> 좌측에서 채권을 선택하면 상세 정보가 표시됩니다.
              </>
            )}
          </p>
        </div>
        {bond && (
          <button
            type="button"
            onClick={() => setIsAiOpen(true)}
            className="flex shrink-0 items-center gap-1 rounded-full bg-navy-900 px-3 py-1.5 text-xs font-semibold text-cream-50 hover:bg-navy-800"
          >
            <Sparkles size={13} className="text-gold-400" />
            AI Analysis
          </button>
        )}
      </div>

      {bond && isAiOpen && <AiAnalysisPanel bond={bond} onClose={() => setIsAiOpen(false)} />}

      {!bond ? (
        <div className="flex flex-col gap-3">
          {["오늘 거래량 (유동성)", "실질수익률 (세후)", "신용 스프레드", "Duration (금리 민감도)"].map((label) => (
            <div key={label} className="flex items-start gap-3 rounded-xl bg-cream-50 p-3">
              <div>
                <p className="text-xs text-ink-600">{label}</p>
                <p className="text-lg font-bold text-navy-900">-</p>
                <p className="text-xs text-ink-400">왼쪽 표에서 채권을 선택하세요</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <>
          <div className="mb-3">
            <p className="text-lg font-bold text-navy-900">{bond.bondName}</p>
            <p className="text-xs text-ink-600">
              {bond.bondType} · {bond.creditRating}
            </p>
            <div className="mt-1 flex flex-wrap gap-1">
              {bond.tags.map((tag) => (
                <span key={tag} className="rounded-full bg-cream-100 px-1.5 py-0.5 text-[10px] font-medium text-ink-600">
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div className="mb-4 grid grid-cols-2 gap-3 rounded-xl bg-navy-900 p-4 text-cream-50">
            {buildInsightMetrics(bond).map((metric) => (
              <div key={metric.label} className="flex items-start gap-2">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-cream-50/10 text-gold-400">
                  <metric.icon size={15} />
                </span>
                <div>
                  <p className="text-[11px] text-cream-100/70">{metric.label}</p>
                  <p className="text-base font-bold text-cream-50">{metric.value}</p>
                  <p className="text-[10px] leading-tight text-cream-100/60">{metric.caption}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mb-4 grid grid-cols-2 gap-x-4 gap-y-2 rounded-xl bg-cream-50 p-3 text-xs">
            {DETAIL_FIELDS.map((field) => (
              <div key={field.label}>
                <p className="text-ink-400">{field.label}</p>
                <p className="font-medium text-navy-800">{field.value(bond)}</p>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-dashed border-gold-500/30 p-4 text-center">
            <div className="mb-1 flex items-center justify-center gap-2">
              <p className="text-xs font-semibold text-ink-600">선택 채권 가격 추이</p>
              <span className="rounded-full bg-gold-500/15 px-2 py-0.5 text-[10px] font-medium text-gold-700">Price</span>
            </div>
            <p className="text-[11px] text-ink-400">현재는 mock 단일 기준일 데이터라 시계열 연결 TODO</p>
          </div>
        </>
      )}
    </section>
  );
}
