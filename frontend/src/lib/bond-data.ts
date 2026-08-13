import { readFile } from "node:fs/promises";
import path from "node:path";

import type { BondDashboardData, BondRow, MarketSnapshot } from "@/types/bond";

type CsvRecord = Record<string, string>;

const DASHBOARD_CSV = path.join(
  process.cwd(),
  "..",
  "data",
  "processed",
  "tableau_bond_dashboard.csv",
);

const MARKET_RATES_CSV = path.join(
  process.cwd(),
  "..",
  "data",
  "processed",
  "market_rates_2026-08-01_07.csv",
);

const MARKET_RULE_THRESHOLDS = {
  termSpreadFlatAbs: 0.1,
  policySpreadFlatAbs: 0.1,
  rateMoveFlatAbs: 0.03,
  cpiMoveFlatAbs: 0.05,
};

// src/analysis/calculate_after_tax_yield.py와 동일한 공식/가드 - 그쪽이 원본(source of
// truth)이다. B안(이 CSV 기반 대시보드)은 Python을 직접 호출할 수 없어 같은 로직을
// TypeScript로 그대로 옮겨 왔다. 두 구현이 갈라지지 않도록, 이 상수/공식을 바꿀 때는
// calculate_after_tax_yield.py도 함께 바꿔야 한다.
const WITHHOLDING_TAX_RATE = 0.154;
const YTM_DISPLAY_MIN_PCT = -5;
const YTM_DISPLAY_MAX_PCT = 15;

type AfterTaxYieldStatus = "CALCULATED" | "MISSING_YTM" | "MISSING_COUPON" | "OUTLIER_YTM";

function classifyAfterTaxYieldStatus(
  ytm: number | null,
  couponRate: number | null,
): AfterTaxYieldStatus {
  if (ytm === null) return "MISSING_YTM";
  if (couponRate === null) return "MISSING_COUPON";
  if (ytm < YTM_DISPLAY_MIN_PCT || ytm > YTM_DISPLAY_MAX_PCT) return "OUTLIER_YTM";
  return "CALCULATED";
}

function calculateAfterTaxYieldApprox(ytm: number, couponRate: number): number {
  return ytm - couponRate * WITHHOLDING_TAX_RATE;
}

// src/analysis/classify_duration_sensitivity.py와 동일한 임계값(그쪽이 원본).
const DURATION_LOW_THRESHOLD = 0.5;
const DURATION_HIGH_THRESHOLD = 2.5;

type DurationSensitivity = "저민감" | "중간" | "고민감";

function classifyDurationSensitivity(duration: number | null): DurationSensitivity | null {
  if (duration === null) return null;
  if (duration <= DURATION_LOW_THRESHOLD) return "저민감";
  if (duration <= DURATION_HIGH_THRESHOLD) return "중간";
  return "고민감";
}

// src/analysis/classify_investment_priority.py와 동일한 임계값/규칙(그쪽이 원본).
type Signal = "STABLE" | "NEUTRAL" | "YIELD";
const SIGNAL_SCORE: Record<Signal, number> = { STABLE: 1, NEUTRAL: 0, YIELD: -1 };
const SPREAD_STABLE_MAX = 0;
const SPREAD_YIELD_MIN = 0.5;
const MIN_AVAILABLE_SIGNALS = 2;

function classifyRatingSignal(creditRating: string | null): Signal | null {
  if (creditRating === null) return null;
  const grade = creditRating.replace(/[+\-0]+$/, "");
  if (grade === "AAA" || grade === "AA") return "STABLE";
  if (grade === "A") return "NEUTRAL";
  return "YIELD";
}

function classifySpreadSignal(creditSpread: number | null): Signal | null {
  if (creditSpread === null) return null;
  if (creditSpread <= SPREAD_STABLE_MAX) return "STABLE";
  if (creditSpread <= SPREAD_YIELD_MIN) return "NEUTRAL";
  return "YIELD";
}

function classifyDurationSignal(durationSensitivity: DurationSensitivity | null): Signal | null {
  if (durationSensitivity === null) return null;
  return { 저민감: "STABLE", 중간: "NEUTRAL", 고민감: "YIELD" }[durationSensitivity] as Signal;
}

type InvestmentPriority = "안정성 중심" | "수익률 중심" | "균형형";

function classifyInvestmentPriority(
  ratingSignal: Signal | null,
  spreadSignal: Signal | null,
  durationSignal: Signal | null,
): InvestmentPriority | null {
  const signals = [ratingSignal, spreadSignal, durationSignal].filter((s): s is Signal => s !== null);
  if (signals.length < MIN_AVAILABLE_SIGNALS) return null;

  const total = signals.reduce((sum, s) => sum + SIGNAL_SCORE[s], 0);
  if (total > 0) return "안정성 중심";
  if (total < 0) return "수익률 중심";
  return "균형형";
}

function parseCsv(text: string): CsvRecord[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && quoted && next === '"') {
      field += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(field);
      if (row.some((value) => value.trim() !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }

  if (field || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  const headers = rows.shift() ?? [];
  return rows.map((values) =>
    Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])),
  );
}

function toNumber(value: string | undefined): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function inferKind(row: CsvRecord): string {
  const name = row.bond_name ?? "";
  if (/국고|국민주택|재정|통안/.test(name)) return "국채";
  if (/은행|금융|카드|캐피탈/.test(name)) return "금융채";
  if (/회사|공사|전력|도로|토지|주택/.test(name)) return "회사채";
  return row.market_type || "미분류";
}

function inferIssuer(row: CsvRecord, kind: string): string | null {
  if (kind === "국채") return "대한민국 정부";
  const name = row.bond_name ?? "";
  const match = name.match(/^([가-힣A-Za-z0-9]+?)(?:\d|채|[(-])/);
  return match?.[1] ?? null;
}

function maturityLabel(years: number): string {
  if (years < 1) return `${Math.max(1, Math.round(years * 365)).toLocaleString("ko-KR")}일`;
  return `${years.toFixed(2)}년`;
}

export function getBondTags(bond: Omit<BondRow, "tags">): string[] {
  const tags: string[] = [];

  if (bond.kind === "국채") tags.push("안정성 중심");
  if (bond.ytm >= 4) tags.push("수익률 높음");
  if (bond.remainingYears < 3) tags.push("단기");
  if (bond.volume >= 100_000_000_000) tags.push("거래 활발");

  return tags;
}

function evaluateMarketRules(
  current: Pick<MarketSnapshot, "policySpread" | "yieldSpread" | "treasury3y" | "cpi">,
  previous?: Pick<MarketSnapshot, "treasury3y" | "cpi">,
): string[] {
  const rules: string[] = [];

  if (current.policySpread > MARKET_RULE_THRESHOLDS.policySpreadFlatAbs) {
    rules.push("POLICY_SPREAD_POSITIVE");
  } else if (current.policySpread < -MARKET_RULE_THRESHOLDS.policySpreadFlatAbs) {
    rules.push("POLICY_SPREAD_NEGATIVE");
  } else {
    rules.push("POLICY_SPREAD_FLAT");
  }

  if (current.yieldSpread > MARKET_RULE_THRESHOLDS.termSpreadFlatAbs) {
    rules.push("TERM_SPREAD_POSITIVE");
  } else if (current.yieldSpread < -MARKET_RULE_THRESHOLDS.termSpreadFlatAbs) {
    rules.push("TERM_SPREAD_NEGATIVE");
  } else {
    rules.push("TERM_SPREAD_FLAT");
  }

  if (previous) {
    const rateMove = current.treasury3y - previous.treasury3y;
    if (rateMove > MARKET_RULE_THRESHOLDS.rateMoveFlatAbs) rules.push("RATE_RISING");
    else if (rateMove < -MARKET_RULE_THRESHOLDS.rateMoveFlatAbs) rules.push("RATE_FALLING");
    else rules.push("RATE_FLAT");

    if (current.cpi !== null && previous.cpi !== null) {
      const cpiMove = current.cpi - previous.cpi;
      if (cpiMove > MARKET_RULE_THRESHOLDS.cpiMoveFlatAbs) rules.push("CPI_RISING");
      else if (cpiMove < -MARKET_RULE_THRESHOLDS.cpiMoveFlatAbs) rules.push("CPI_FALLING");
      else rules.push("CPI_FLAT");
    }
  }

  return rules;
}

function buildMarketSummary(
  current: Pick<MarketSnapshot, "policySpread" | "yieldSpread" | "treasury3y" | "cpi">,
  rules: string[],
): Pick<MarketSnapshot, "scenario" | "summary" | "summaryTitle" | "summaryLines" | "rules"> {
  const priority = [
    "TERM_SPREAD_NEGATIVE",
    "RATE_RISING",
    "RATE_FALLING",
    "TERM_SPREAD_POSITIVE",
    "POLICY_SPREAD_POSITIVE",
    "POLICY_SPREAD_NEGATIVE",
    "CPI_RISING",
    "CPI_FALLING",
    "TERM_SPREAD_FLAT",
  ];
  const primaryRule = priority.find((rule) => rules.includes(rule)) ?? rules[0];
  const lineByRule: Record<string, string> = {
    TERM_SPREAD_POSITIVE: `장기금리가 단기금리보다 +${current.yieldSpread.toFixed(2)}%p 높습니다.`,
    TERM_SPREAD_FLAT: `장단기 금리차가 ${current.yieldSpread.toFixed(2)}%p로 크지 않습니다.`,
    TERM_SPREAD_NEGATIVE: `장기금리가 단기금리보다 ${current.yieldSpread.toFixed(2)}%p 낮습니다.`,
    POLICY_SPREAD_POSITIVE: `국고채 3Y가 기준금리보다 +${current.policySpread.toFixed(2)}%p 높습니다.`,
    POLICY_SPREAD_NEGATIVE: `국고채 3Y가 기준금리보다 ${current.policySpread.toFixed(2)}%p 낮습니다.`,
    POLICY_SPREAD_FLAT: `국고채 3Y와 기준금리의 차이가 크지 않습니다.`,
    RATE_RISING: `이전 기준일보다 국고채 3Y 금리가 상승했습니다.`,
    RATE_FALLING: `이전 기준일보다 국고채 3Y 금리가 하락했습니다.`,
    RATE_FLAT: `이전 기준일 대비 국고채 3Y 금리가 보합권입니다.`,
    CPI_RISING: `최근 CPI가 이전 월보다 상승했습니다.`,
    CPI_FALLING: `최근 CPI가 이전 월보다 하락했습니다.`,
    CPI_FLAT: `최근 CPI 변화가 크지 않습니다.`,
  };
  const supportLine =
    primaryRule === "TERM_SPREAD_NEGATIVE"
      ? "단기금리 부담이 상대적으로 크게 반영될 수 있습니다."
      : primaryRule === "RATE_RISING"
        ? "금리가 오를 때는 채권 가격 변동 가능성을 함께 봐야 합니다."
        : primaryRule === "RATE_FALLING"
          ? "금리가 내려갈 때는 기존 채권 가격에 우호적으로 작용할 수 있습니다."
          : "장기채는 금리 변화에 더 민감할 수 있어요.";
  const mainLine = lineByRule[primaryRule] ?? lineByRule.TERM_SPREAD_FLAT;

  return {
    scenario: primaryRule,
    summaryTitle: "오늘의 시장 요약",
    summary: `${mainLine} ${supportLine}`,
    summaryLines: [mainLine, supportLine],
    rules,
  };
}

export async function getBondDashboardData(): Promise<BondDashboardData> {
  const [text, marketRatesText] = await Promise.all([
    readFile(DASHBOARD_CSV, "utf8"),
    readFile(MARKET_RATES_CSV, "utf8"),
  ]);
  const records = parseCsv(text);
  const marketRateRecords = parseCsv(marketRatesText);

  const parsedBonds = records
    .map((row, index): BondRow | null => {
      const ytm = toNumber(row.close_yield);
      const price = toNumber(row.close_price);
      const remainingYears = toNumber(row.remaining_years);
      const volume = toNumber(row.volume);
      const tradingValue = toNumber(row.trading_value);
      const treasury3y = toNumber(row.treasury_3y);
      const treasury10y = toNumber(row.treasury_10y);
      const baseRate = toNumber(row.base_rate);
      const yieldSpread = toNumber(row.yield_spread);
      const creditSpread = toNumber(row.credit_spread);
      const policySpread = toNumber(row.policy_spread);

      if (
        !row.bond_name ||
        ytm === null ||
        price === null ||
        remainingYears === null ||
        volume === null ||
        tradingValue === null ||
        treasury3y === null ||
        treasury10y === null ||
        baseRate === null ||
        yieldSpread === null ||
        creditSpread === null ||
        policySpread === null
      ) {
        return null;
      }

      const kind = inferKind(row);
      const couponRate = toNumber(row.coupon_rate);
      const afterTaxYieldStatus = classifyAfterTaxYieldStatus(ytm, couponRate);
      const afterTaxYieldApprox =
        afterTaxYieldStatus === "CALCULATED" ? calculateAfterTaxYieldApprox(ytm, couponRate!) : null;

      // 국채/지방채처럼 등급 자체가 없는 채권은 "국채니까 AAA"로 추정하지 않고 그대로 null로 둔다
      // (src/processing/enrich_tableau_dashboard.py, classify_investment_priority.py와 동일 원칙).
      const rating = row.credit_rating || null;
      const duration = toNumber(row.modified_duration);
      const durationSensitivity = classifyDurationSensitivity(duration);
      // ①이 OUTLIER_YTM이면 같은 YTM에서 파생된 신용스프레드도 신호에서 제외
      // (classify_investment_priority.py의 build_investment_priority와 동일 가드).
      const spreadForSignal = afterTaxYieldStatus === "OUTLIER_YTM" ? null : creditSpread;
      const investmentPriority = classifyInvestmentPriority(
        classifyRatingSignal(rating),
        classifySpreadSignal(spreadForSignal),
        classifyDurationSignal(durationSensitivity),
      );

      const baseBond = {
        id: row.isin_code || row.short_code || `bond-${index}`,
        date: row.reference_date || row.date,
        bondName: row.bond_name,
        issuer: inferIssuer(row, kind),
        kind,
        rating,
        ytm,
        couponRate,
        afterTaxYieldApprox,
        afterTaxYieldStatus,
        duration,
        durationSensitivity,
        investmentPriority,
        remainingYears,
        remainingLabel: maturityLabel(remainingYears),
        currentPrice: price,
        volume,
        tradingValue,
        maturityDate: row.maturity_date,
        issueDate: row.issue_date || null,
        treasury3y,
        treasury10y,
        baseRate,
        yieldSpread,
        creditSpread,
        policySpread,
        cpi: toNumber(row.cpi),
        calculationStatus: row.calculation_status,
      };

      return { ...baseBond, tags: getBondTags(baseBond) };
    })
    .filter((bond): bond is BondRow => bond !== null);

  const bonds = Array.from(
    new Map(parsedBonds.map((bond) => [`${bond.date}:${bond.id}`, bond])).values(),
  ).sort((a, b) => b.tradingValue - a.tradingValue);

  const availableDates = marketRateRecords.map((row) => row.date).filter(Boolean).sort();
  const cpi = bonds[0]?.cpi ?? null;
  const markets = marketRateRecords.map((row, index) => {
    const previous = index > 0 ? marketRateRecords[index - 1] : undefined;
    const snapshot = {
      policySpread: toNumber(row.policy_spread) ?? 0,
      yieldSpread: toNumber(row.yield_spread) ?? 0,
      treasury3y: toNumber(row.treasury_3y) ?? 0,
      cpi,
    };
    const previousSnapshot = previous
      ? { treasury3y: toNumber(previous.treasury_3y) ?? 0, cpi }
      : undefined;
    const summary = buildMarketSummary(snapshot, evaluateMarketRules(snapshot, previousSnapshot));
    const isWeekendFreeze = row.date === "2026-08-01" || row.date === "2026-08-02";

    return {
      date: row.date,
      marketRateDate: isWeekendFreeze ? "2026-07-31" : row.date,
      baseRate: toNumber(row.base_rate) ?? 0,
      treasury3y: snapshot.treasury3y,
      treasury10y: toNumber(row.treasury_10y) ?? 0,
      yieldSpread: snapshot.yieldSpread,
      creditSpread: toNumber(row.credit_spread) ?? 0,
      policySpread: snapshot.policySpread,
      cpi,
      scenario: summary.scenario,
      summary: summary.summary,
      summaryTitle: summary.summaryTitle,
      summaryLines: summary.summaryLines,
      rules: summary.rules,
    };
  });

  const first = bonds[0];

  if (!first) {
    throw new Error("tableau_bond_dashboard.csv에서 표시 가능한 채권 데이터를 찾지 못했습니다.");
  }

  return { bonds, markets, availableDates };
}
