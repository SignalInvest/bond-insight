"use client";

import { Activity, LineChart, Loader2, MousePointerClick, Percent, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import type { ComponentType } from "react";

interface InsightMetric {
  label: string;
  value: string;
  caption: string;
  icon: ComponentType<{ size?: number }>;
}

interface BondInsightBaseRow {
  date: string;
  isin: string;
  bond_name: string;
  issuer: string;
  bond_type: string;
  credit_rating: string;
  coupon_rate: string;
  close_price: string;
  ytm: string;
  volume: string;
  trading_value: string;
  has_option: string;
  is_fixed_rate: string;
}

interface BondInsightDerivedRow {
  isin: string;
  macaulay_duration: string;
  modified_duration: string;
  relative_yield_spread: string;
}

// backend/app/services/bond_service.py get_bond()의 응답 형태
interface BackendBond {
  isin_code: string;
  bond_name: string;
  market: {
    reference_date: string;
    close_price: number | null;
    ytm: number | null;
    volume: number | null;
    trading_value: number | null;
    benchmark_treasury_rate: number | null;
    credit_spread: number | null;
  } | null;
  metrics: {
    reference_date: string;
    macaulay_duration: number | null;
    modified_duration: number | null;
    duration_status: string | null;
  } | null;
}

interface BondInsightApiResponse {
  found: boolean;
  isin?: string;
  backendAvailable?: boolean;
  base?: BondInsightBaseRow;
  derived?: BondInsightDerivedRow | null;
  backend?: BackendBond | null;
}

// Bond Screener(Tableau, yunseo_3h48m)의 실제 컬럼명 기준 (2026-08-12 확인):
// 채권명 / 발행사 / 유형 / 신용등급 / 잔존만기 / YTM(수익률) / 현재가
const FIELD_CANDIDATES = {
  bondName: ["채권명", "Bond Name", "bond_name"],
  ytm: ["YTM", "수익률", "ytm"],
};

const WITHHOLDING_TAX_RATE = 0.154;

function pickField(fields: Record<string, string>, candidates: string[]): string | undefined {
  for (const key of candidates) {
    if (fields[key] !== undefined) return fields[key];
  }
  const lowerCandidates = candidates.map((c) => c.toLowerCase());
  for (const [key, value] of Object.entries(fields)) {
    const lowerKey = key.toLowerCase();
    if (lowerCandidates.some((c) => lowerKey.includes(c))) return value;
  }
  return undefined;
}

function parsePercent(raw: string | undefined): number | null {
  if (!raw) return null;
  const num = Number.parseFloat(raw.replace(/[^0-9.-]/g, ""));
  return Number.isNaN(num) ? null : num;
}

function parseNullableFloat(raw: string | undefined): number | null {
  if (raw === undefined || raw === "") return null;
  const num = Number.parseFloat(raw);
  return Number.isNaN(num) ? null : num;
}

function formatKoreanNumber(value: number, unit: string): string {
  const abs = Math.abs(value);
  if (abs >= 1_0000_0000) return `${(value / 1_0000_0000).toFixed(2)}억${unit}`;
  if (abs >= 10000) return `${(value / 10000).toFixed(0)}만${unit}`;
  return `${value.toLocaleString()}${unit}`;
}

async function fetchBondInsight(bondName: string): Promise<BondInsightApiResponse> {
  const response = await fetch(`/api/bond-insight?bondName=${encodeURIComponent(bondName)}`);
  return (await response.json()) as BondInsightApiResponse;
}

/** 1순위: 백엔드(FastAPI + Supabase, /api/bonds/{isin})의 공식 계산값. */
function buildMetricsFromBackend(bond: BackendBond): InsightMetric[] {
  const market = bond.market;
  const metrics = bond.metrics;
  const ytm = market?.ytm ?? null;
  const tradingValue = market?.trading_value ?? null;
  const volume = market?.volume ?? null;
  const creditSpread = market?.credit_spread ?? null;
  const modifiedDuration = metrics?.modified_duration ?? null;

  return [
    {
      label: "오늘 거래량 (유동성)",
      value: tradingValue !== null ? formatKoreanNumber(tradingValue, "원") : "데이터 없음",
      caption:
        volume !== null && market
          ? `${formatKoreanNumber(volume, "좌")} 체결 · ${market.reference_date} 기준 (Supabase)`
          : "Supabase에 거래 데이터가 없어요",
      icon: Activity,
    },
    {
      label: "실질수익률 (세후)",
      value: ytm !== null ? `${(ytm * (1 - WITHHOLDING_TAX_RATE)).toFixed(2)}%` : "데이터 없음",
      caption: ytm !== null ? `세전 YTM ${ytm}% × (1 − 이자소득세 15.4%)` : "YTM 데이터가 없어요",
      icon: Percent,
    },
    {
      label: "신용 스프레드",
      value:
        creditSpread !== null ? `${creditSpread >= 0 ? "+" : ""}${(creditSpread * 100).toFixed(0)}bp` : "데이터 없음",
      caption: creditSpread !== null ? "YTM − 잔존만기 보간 국고채 금리 (Supabase 계산값)" : "벤치마크 금리를 찾지 못했어요",
      icon: ShieldAlert,
    },
    {
      label: "Duration (금리 민감도)",
      value: modifiedDuration !== null ? modifiedDuration.toFixed(2) : "데이터 없음",
      caption:
        modifiedDuration !== null
          ? `금리 1%p 오르면 가격 약 -${modifiedDuration.toFixed(2)}% 변동 (Supabase 계산값)`
          : metrics?.duration_status
            ? `계산 제외 사유: ${metrics.duration_status}`
            : "Duration 데이터가 없어요",
      icon: LineChart,
    },
  ];
}

/** 2순위: 백엔드 서버가 꺼져 있을 때 — yunseo/output 로컬 CSV 값. */
function buildMetricsFromCsv(base: BondInsightBaseRow, derived: BondInsightDerivedRow | null): InsightMetric[] {
  const ytm = parseNullableFloat(base.ytm);
  const tradingValue = parseNullableFloat(base.trading_value);
  const volume = parseNullableFloat(base.volume);
  const modifiedDuration = derived ? parseNullableFloat(derived.modified_duration) : null;
  const relativeSpread = derived ? parseNullableFloat(derived.relative_yield_spread) : null;

  const unavailableReason =
    base.has_option === "True"
      ? "옵션부 채권이라 계산 대상에서 제외됐어요"
      : base.is_fixed_rate === "False"
        ? "변동금리 채권이라 계산 대상에서 제외됐어요"
        : "계산에 필요한 데이터가 부족해요";

  return [
    {
      label: "오늘 거래량 (유동성)",
      value: tradingValue !== null ? formatKoreanNumber(tradingValue, "원") : "데이터 없음",
      caption:
        volume !== null
          ? `${formatKoreanNumber(volume, "좌")} 체결 · ${base.date} 기준 (백엔드 서버 꺼짐, 로컬 값)`
          : `${base.date} 기준 (백엔드 서버 꺼짐, 로컬 값)`,
      icon: Activity,
    },
    {
      label: "실질수익률 (세후)",
      value: ytm !== null ? `${(ytm * (1 - WITHHOLDING_TAX_RATE)).toFixed(2)}%` : "데이터 없음",
      caption: ytm !== null ? `세전 YTM ${ytm}% × (1 − 이자소득세 15.4%)` : "YTM 데이터가 없어요",
      icon: Percent,
    },
    {
      label: "신용 스프레드",
      value:
        relativeSpread !== null ? `${relativeSpread >= 0 ? "+" : ""}${(relativeSpread * 100).toFixed(0)}bp` : "데이터 없음",
      caption: relativeSpread !== null ? "YTM − 잔존만기와 가장 가까운 국고채 금리 (로컬 계산)" : unavailableReason,
      icon: ShieldAlert,
    },
    {
      label: "Duration (금리 민감도)",
      value: modifiedDuration !== null ? modifiedDuration.toFixed(2) : "데이터 없음",
      caption:
        modifiedDuration !== null
          ? `금리 1%p 오르면 가격 약 -${modifiedDuration.toFixed(2)}% 변동 (로컬 계산)`
          : unavailableReason,
      icon: LineChart,
    },
  ];
}

/** 3순위: yunseo CSV에도 없을 때 — Tableau의 YTM만으로 계산 가능한 것만. */
function buildFallbackMetrics(fields: Record<string, string>): InsightMetric[] {
  const ytm = parsePercent(pickField(fields, FIELD_CANDIDATES.ytm));

  return [
    { label: "오늘 거래량 (유동성)", value: "데이터 없음", caption: "이 채권을 찾지 못했어요", icon: Activity },
    {
      label: "실질수익률 (세후)",
      value: ytm !== null ? `${(ytm * (1 - WITHHOLDING_TAX_RATE)).toFixed(2)}%` : "데이터 없음",
      caption: ytm !== null ? `세전 YTM ${ytm}% × (1 − 이자소득세 15.4%)` : "YTM 필드를 찾지 못했어요",
      icon: Percent,
    },
    { label: "신용 스프레드", value: "데이터 없음", caption: "이 채권을 찾지 못했어요", icon: ShieldAlert },
    { label: "Duration (금리 민감도)", value: "데이터 없음", caption: "이 채권을 찾지 못했어요", icon: LineChart },
  ];
}

const PLACEHOLDER_METRICS: InsightMetric[] = [
  { label: "오늘 거래량 (유동성)", value: "-", caption: "왼쪽 표에서 채권을 선택하세요", icon: Activity },
  { label: "실질수익률 (세후)", value: "-", caption: "왼쪽 표에서 채권을 선택하세요", icon: Percent },
  { label: "신용 스프레드", value: "-", caption: "왼쪽 표에서 채권을 선택하세요", icon: ShieldAlert },
  { label: "Duration (금리 민감도)", value: "-", caption: "왼쪽 표에서 채권을 선택하세요", icon: LineChart },
];

const LOADING_METRICS: InsightMetric[] = [
  { label: "오늘 거래량 (유동성)", value: "…", caption: "불러오는 중", icon: Activity },
  { label: "실질수익률 (세후)", value: "…", caption: "불러오는 중", icon: Percent },
  { label: "신용 스프레드", value: "…", caption: "불러오는 중", icon: ShieldAlert },
  { label: "Duration (금리 민감도)", value: "…", caption: "불러오는 중", icon: LineChart },
];

type RemoteState =
  | { status: "idle" }
  | { status: "loading" }
  | {
      status: "found";
      isin: string;
      backendAvailable: boolean;
      base: BondInsightBaseRow;
      derived: BondInsightDerivedRow | null;
      backend: BackendBond | null;
    }
  | { status: "not-found" }
  | { status: "error" };

interface BondInsightProps {
  selectedFields: Record<string, string> | null;
}

export function BondInsight({ selectedFields }: BondInsightProps) {
  const bondName = selectedFields ? pickField(selectedFields, FIELD_CANDIDATES.bondName) : undefined;
  const [remote, setRemote] = useState<RemoteState>({ status: "idle" });
  // remote가 어느 bondName에 대한 응답인지 추적 → "loading" 여부를 렌더링 시점에 파생시키기 위함
  const [resolvedBondName, setResolvedBondName] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!bondName) {
      return;
    }

    let cancelled = false;

    fetchBondInsight(bondName)
      .then((data) => {
        if (cancelled) return;
        if (data.found && data.base && data.isin) {
          setRemote({
            status: "found",
            isin: data.isin,
            backendAvailable: data.backendAvailable ?? false,
            base: data.base,
            derived: data.derived ?? null,
            backend: data.backend ?? null,
          });
        } else {
          setRemote({ status: "not-found" });
        }
        setResolvedBondName(bondName);
      })
      .catch(() => {
        if (cancelled) return;
        setRemote({ status: "error" });
        setResolvedBondName(bondName);
      });

    return () => {
      cancelled = true;
    };
  }, [bondName]);

  // bondName이 없거나, 아직 이 bondName에 대한 응답을 못 받았으면(=이전 응답이거나 없음) idle/loading으로 파생시킴
  // (useEffect 안에서 동기적으로 setState하지 않기 위함 — react-hooks/set-state-in-effect)
  const effectiveRemote: RemoteState = !bondName
    ? { status: "idle" }
    : resolvedBondName === bondName
      ? remote
      : { status: "loading" };

  const metrics = !selectedFields
    ? PLACEHOLDER_METRICS
    : effectiveRemote.status === "found"
      ? effectiveRemote.backendAvailable && effectiveRemote.backend
        ? buildMetricsFromBackend(effectiveRemote.backend)
        : buildMetricsFromCsv(effectiveRemote.base, effectiveRemote.derived)
      : effectiveRemote.status === "loading"
        ? LOADING_METRICS
        : buildFallbackMetrics(selectedFields ?? {});

  return (
    <section
      aria-labelledby="bond-insight-title"
      className="rounded-2xl border border-gold-500/30 bg-white p-5 shadow-sm shadow-navy-900/5"
    >
      <h2 id="bond-insight-title" className="mb-1 flex items-center gap-2 text-lg font-bold text-navy-900">
        <LineChart size={20} className="text-gold-600" />
        Bond Insight
      </h2>
      <p className="mb-4 flex items-center gap-1 text-xs text-ink-600">
        {!selectedFields ? (
          <>
            <MousePointerClick size={14} /> Bond Screener에서 채권을 선택해 보세요
          </>
        ) : effectiveRemote.status === "loading" ? (
          <>
            <Loader2 size={14} className="animate-spin" /> {bondName} 불러오는 중
          </>
        ) : effectiveRemote.status === "found" ? (
          <span>
            선택한 채권 <span className="font-semibold text-navy-800">{bondName}</span> ·{" "}
            {effectiveRemote.backendAvailable ? "Supabase 데이터" : "로컬 데이터 (백엔드 서버를 켜면 공식 값으로 바뀌어요)"}
          </span>
        ) : (
          <span>
            선택한 채권 <span className="font-semibold text-navy-800">{bondName ?? "(이름 필드 없음)"}</span> — 정확한
            데이터를 찾지 못했어요
          </span>
        )}
      </p>

      <div className="flex flex-col gap-3">
        {metrics.map((metric) => (
          <div key={metric.label} className="flex items-start gap-3 rounded-xl bg-cream-50 p-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cream-100 text-gold-600">
              <metric.icon size={16} />
            </span>
            <div>
              <p className="text-xs text-ink-600">{metric.label}</p>
              <p className="text-lg font-bold text-navy-900">{metric.value}</p>
              <p className="text-xs text-ink-400">{metric.caption}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
