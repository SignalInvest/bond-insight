"use client";

import { useMemo, useState } from "react";

import type { BondDashboardData, BondRow, MarketSnapshot } from "@/types/bond";

interface Props {
  data: BondDashboardData;
}

type QuickFilter = "전체" | "국채" | "회사채" | "안정성 중심" | "수익률 중심" | "단기채";

const quickFilters: QuickFilter[] = ["전체", "국채", "회사채", "안정성 중심", "수익률 중심", "단기채"];

function formatPercent(value: number | null, digits = 2): string {
  return value === null ? "데이터 미확보" : `${value.toFixed(digits)}%`;
}

function formatMillion(value: number | null): string {
  return value === null ? "데이터 미확보" : Math.round(value / 1_000_000).toLocaleString("ko-KR");
}

function formatPrice(value: number): string {
  return `${Math.round(value).toLocaleString("ko-KR")}원`;
}

function formatDate(value: string | null): string {
  if (!value) return "데이터 미확보";
  return value.replaceAll("-", ".");
}

function deltaText(value: number, unit: string): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}${unit}`;
}

function toInputDate(value: string): string {
  return value.slice(0, 10);
}

function generateInvestmentInsight(bond: BondRow, market: MarketSnapshot) {
  const extraYield = bond.ytm - market.treasury3y;
  const durationText = bond.duration === null ? "듀레이션 산출 데이터가 없어" : `듀레이션 ${bond.duration.toFixed(2)}년 기준`;

  return {
    headline: `선택 채권의 만기수익률은 ${bond.ytm.toFixed(2)}%이고 국고채 3Y 대비 ${deltaText(extraYield, "%p")} 차이를 보입니다.`,
    returnView: `수익률 관점에서는 현재 만기수익률 ${bond.ytm.toFixed(2)}%와 기준금리 ${market.baseRate.toFixed(2)}% 사이의 간격을 함께 볼 수 있습니다.`,
    riskView: `${durationText} 시장금리 변동에 따른 가격 민감도를 확인해야 합니다. 잔존만기는 ${bond.remainingLabel}입니다.`,
    checkView: `거래량은 ${formatMillion(bond.volume)}백만 단위이며, 신용등급 또는 표면금리처럼 CSV에 없는 항목은 추가 데이터 연결 후 판단 범위를 넓힐 수 있습니다.`,
  };
}

function buildComparisonPoints(bond: BondRow, market: MarketSnapshot) {
  const values = [
    { label: "기준금리", value: market.baseRate },
    { label: "국고 3Y", value: market.treasury3y },
    { label: "국고 10Y", value: market.treasury10y },
    { label: "선택 만기수익률", value: bond.ytm },
  ];
  const min = Math.min(...values.map((item) => item.value)) - 0.3;
  const max = Math.max(...values.map((item) => item.value)) + 0.3;

  return values.map((item, index) => ({
    ...item,
    x: 34 + index * 112,
    y: 140 - ((item.value - min) / (max - min)) * 98,
  }));
}

function buildTrendPoints(bond: BondRow) {
  const base = bond.currentPrice;
  const change = Math.abs(bond.currentPrice * 0.006);
  const values = [
    { label: "T-4", value: base - change * 0.4 },
    { label: "T-3", value: base + change * 0.15 },
    { label: "T-2", value: base - change * 0.2 },
    { label: "T-1", value: base + change * 0.35 },
    { label: "현재", value: base },
  ];
  const min = Math.min(...values.map((item) => item.value));
  const max = Math.max(...values.map((item) => item.value));

  return values.map((item, index) => ({
    ...item,
    x: 30 + index * 92,
    y: 142 - ((item.value - min) / Math.max(max - min, 1)) * 98,
  }));
}

function MiniCalendarIcon() {
  return (
    <svg aria-hidden="true" className="line-icon" viewBox="0 0 24 24">
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M8 3v4M16 3v4M4 10h16" />
    </svg>
  );
}

function BondMark() {
  return (
    <svg aria-hidden="true" className="brand-mark" viewBox="0 0 64 64">
      <path d="M10 24h44L32 12 10 24Z" />
      <path d="M16 28v18M26 28v18M38 28v18M48 28v18M12 50h40" />
    </svg>
  );
}

export default function BondBridgeDashboard({ data }: Props) {
  const [selectedDate, setSelectedDate] = useState(data.availableDates.at(-1) ?? "");
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);
  const [quickFilter, setQuickFilter] = useState<QuickFilter>("전체");
  const [kindFilter, setKindFilter] = useState("전체");
  const [ratingFilter, setRatingFilter] = useState("전체");
  const [maturityFilter, setMaturityFilter] = useState("전체");
  const [query, setQuery] = useState("");
  const [isAiOpen, setIsAiOpen] = useState(false);
  const [hoveredTrend, setHoveredTrend] = useState<number | null>(null);
  const [hoveredComparison, setHoveredComparison] = useState<number | null>(null);

  const bondsForDate = useMemo(
    () => data.bonds.filter((bond) => bond.date === selectedDate),
    [data.bonds, selectedDate],
  );
  const market = data.markets.find((item) => item.date === selectedDate);
  const hasDataForDate = bondsForDate.length > 0 && market !== undefined;
  const selectedBond = bondsForDate.find((bond) => bond.id === selectedId) ?? bondsForDate[0];

  const filteredBonds = useMemo(() => {
    return bondsForDate.filter((bond) => {
      if (quickFilter === "국채" && bond.kind !== "국채") return false;
      if (quickFilter === "회사채" && bond.kind === "국채") return false;
      if (quickFilter === "안정성 중심" && !bond.tags.includes("안정성 중심")) return false;
      if (quickFilter === "수익률 중심" && !bond.tags.includes("수익률 높음")) return false;
      if (quickFilter === "단기채" && bond.remainingYears >= 3) return false;
      if (kindFilter !== "전체" && bond.kind !== kindFilter) return false;
      if (ratingFilter !== "전체" && (bond.rating ?? "데이터 미확보") !== ratingFilter) return false;
      if (maturityFilter === "단기" && bond.remainingYears >= 3) return false;
      if (maturityFilter === "중기" && (bond.remainingYears < 3 || bond.remainingYears >= 7)) return false;
      if (maturityFilter === "장기" && bond.remainingYears < 7) return false;

      const search = query.trim().toLowerCase();
      if (search && !`${bond.bondName} ${bond.issuer ?? ""} ${bond.id}`.toLowerCase().includes(search)) {
        return false;
      }

      return true;
    });
  }, [bondsForDate, kindFilter, maturityFilter, query, quickFilter, ratingFilter]);

  const kinds = ["전체", ...Array.from(new Set(bondsForDate.map((bond) => bond.kind)))];
  const ratings = ["전체", ...Array.from(new Set(bondsForDate.map((bond) => bond.rating ?? "데이터 미확보")))];
  const insight = selectedBond && market ? generateInvestmentInsight(selectedBond, market) : null;
  const trend = selectedBond ? buildTrendPoints(selectedBond) : [];
  const trendPath = trend.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
  const comparison = selectedBond && market ? buildComparisonPoints(selectedBond, market) : [];
  const comparisonLine = comparison.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");

  return (
    <>
      <header className="bridge-header">
        <div className="brand-block">
          <BondMark />
          <div>
            <p className="brand-title">BOND BRIDGE</p>
            <p className="brand-subtitle">채권 투자 첫걸음 대시보드</p>
          </div>
        </div>
        <div className="header-report">
          <label className="date-picker">
            <span><MiniCalendarIcon /> 기준일</span>
            <input
              type="date"
              value={toInputDate(selectedDate)}
              onChange={(event) => {
                setSelectedDate(event.target.value);
                setSelectedId(undefined);
                setIsAiOpen(false);
              }}
            />
            <strong>{formatDate(selectedDate)} 기준</strong>
          </label>
        </div>
      </header>

      <main className="bridge-shell">
        {!hasDataForDate ? (
          <section className="empty-state">
            <h1>{formatDate(selectedDate)} 기준 데이터가 없습니다.</h1>
            <p>현재 CSV에 존재하는 기준일만 화면에 반영합니다. 사용 가능한 기준일: {data.availableDates.map(formatDate).join(", ")}</p>
          </section>
        ) : (
          <>
            <section className="market-section" aria-labelledby="market-title">
              <div className="section-heading">
                <span>01</span>
                <div>
                  <h1 id="market-title">BOND MARKET</h1>
                  <p>지금 채권시장은 어떤 상황일까요?</p>
                </div>
              </div>

              <div className="market-grid">
                <article className="market-card market-card-wide">
                  <p className="card-label">{market.summaryTitle}</p>
                  <strong>{market.summaryLines[0]}</strong>
                  <span>{market.summaryLines[1]}</span>
                </article>
                <article className="market-card">
                  <p className="card-label">기준금리</p>
                  <strong>{formatPercent(market.baseRate)}</strong>
                  <span>정책금리 기준</span>
                </article>
                <article className="market-card">
                  <p className="card-label">국고채 3Y</p>
                  <strong>{formatPercent(market.treasury3y)}</strong>
                  <span>Policy Spread {deltaText(market.policySpread, "%p")}</span>
                </article>
                <article className="market-card">
                  <p className="card-label">국고채 10Y</p>
                  <strong>{formatPercent(market.treasury10y)}</strong>
                  <span>시장금리 기준</span>
                </article>
                <article className="market-card">
                  <p className="card-label">장단기 금리차</p>
                  <strong>{deltaText(market.yieldSpread, "%p")}</strong>
                  <span>10Y - 3Y</span>
                </article>
                <article className="market-card">
                  <p className="card-label">CPI</p>
                  <strong>{market.cpi === null ? "데이터 미확보" : market.cpi.toFixed(2)}</strong>
                  <span>최근 월 기준</span>
                </article>
              </div>
            </section>

            <div className="main-grid">
              <section className="panel explorer-panel" aria-labelledby="explorer-title">
                <div className="section-heading compact">
                  <span>02</span>
                  <div>
                    <h2 id="explorer-title">BOND SCREENER</h2>
                    <p>조건을 선택하거나 검색하여 관심 채권을 찾아보세요.</p>
                  </div>
                </div>

                <div className="quick-filters" aria-label="빠른 필터">
                  {quickFilters.map((filter) => (
                    <button
                      className={filter === quickFilter ? "active" : ""}
                      key={filter}
                      onClick={() => setQuickFilter(filter)}
                      type="button"
                    >
                      {filter}
                    </button>
                  ))}
                </div>

                <div className="detail-filters">
                  <label>
                    채권 종류
                    <select value={kindFilter} onChange={(event) => setKindFilter(event.target.value)}>
                      {kinds.map((kind) => <option key={kind}>{kind}</option>)}
                    </select>
                  </label>
                  <label>
                    신용등급
                    <select value={ratingFilter} onChange={(event) => setRatingFilter(event.target.value)}>
                      {ratings.map((rating) => <option key={rating}>{rating}</option>)}
                    </select>
                  </label>
                  <label>
                    잔존만기
                    <select value={maturityFilter} onChange={(event) => setMaturityFilter(event.target.value)}>
                      {["전체", "단기", "중기", "장기"].map((maturity) => <option key={maturity}>{maturity}</option>)}
                    </select>
                  </label>
                  <label className="search-label">
                    채권명 검색
                    <input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="채권명 또는 종목코드 입력"
                    />
                  </label>
                </div>

                <div className="bond-table" role="table" aria-label="채권 목록">
                  <div className="bond-table-head" role="row">
                    <span>채권명</span>
                    <span>발행기관</span>
                    <span>종류</span>
                    <span>신용등급</span>
                    <span>만기수익률</span>
                    <span>표면금리</span>
                    <span>잔존만기</span>
                    <span>듀레이션</span>
                    <span>현재가</span>
                  </div>
                  {filteredBonds.map((bond) => (
                    <button
                      className={`bond-row ${bond.id === selectedBond?.id ? "selected" : ""}`}
                      key={bond.id}
                      onClick={() => {
                        setSelectedId(bond.id);
                        setIsAiOpen(false);
                      }}
                      role="row"
                      type="button"
                    >
                      <span className="bond-name-cell">
                        <strong>{bond.bondName}</strong>
                        <small>{bond.tags.slice(0, 2).map((tag) => <em key={tag}>{tag}</em>)}</small>
                      </span>
                      <span>{bond.issuer ?? "데이터 미확보"}</span>
                      <span>{bond.kind}</span>
                      <span>{bond.rating ?? "데이터 미확보"}</span>
                      <span className={bond.ytm >= market.treasury3y ? "positive" : "negative"}>{formatPercent(bond.ytm)}</span>
                      <span>{formatPercent(bond.couponRate)}</span>
                      <span>{bond.remainingLabel}</span>
                      <span>{bond.duration === null ? "데이터 미확보" : bond.duration.toFixed(3)}</span>
                      <span>{formatPrice(bond.currentPrice)}</span>
                    </button>
                  ))}
                </div>
              </section>

              {selectedBond && (
                <section className="panel detail-panel" aria-labelledby="detail-title">
                  <div className="detail-heading-row">
                    <div className="section-heading compact">
                      <span>03</span>
                      <div>
                        <h2 id="detail-title">BOND OVERVIEW</h2>
                        <p>좌측에서 채권을 선택하면 상세 정보가 표시됩니다.</p>
                      </div>
                    </div>
                    <button className="ai-button" onClick={() => setIsAiOpen(true)} type="button">
                      AI Analysis
                    </button>
                  </div>

                  <div className="selected-title">
                    <h3>{selectedBond.bondName}</h3>
                    <p>{selectedBond.kind} · {selectedBond.rating ?? "신용등급 데이터 미확보"}</p>
                    <div>{selectedBond.tags[0] ?? "태그 산출 기준 TODO"}</div>
                  </div>

                  <div className="navy-kpis">
                    <div><span>만기수익률</span><strong>{formatPercent(selectedBond.ytm)}</strong></div>
                    <div><span>현재가격</span><strong>{formatPrice(selectedBond.currentPrice)}</strong></div>
                    <div><span>잔존만기</span><strong>{selectedBond.remainingLabel}</strong></div>
                    <div><span>신용등급</span><strong>{selectedBond.rating ?? "미확보"}</strong></div>
                  </div>

                  <dl className="detail-list">
                    <div><dt>발행기관</dt><dd>{selectedBond.issuer ?? "데이터 미확보"}</dd></div>
                    <div><dt>표면금리</dt><dd>{formatPercent(selectedBond.couponRate)}</dd></div>
                    <div><dt>발행일</dt><dd>{formatDate(selectedBond.issueDate)}</dd></div>
                    <div><dt>만기일</dt><dd>{formatDate(selectedBond.maturityDate)}</dd></div>
                    <div><dt>듀레이션</dt><dd>{selectedBond.duration === null ? "산출 데이터 없음" : selectedBond.duration.toFixed(3)}</dd></div>
                    <div><dt>거래량(백만)</dt><dd>{formatMillion(selectedBond.volume)}</dd></div>
                  </dl>

                  <div className="chart-card">
                    <div className="chart-head">
                      <div>
                        <h4>선택 채권 가격 추이</h4>
                        <span>현재 CSV는 단일 기준일 데이터라 시계열 연결 TODO</span>
                      </div>
                      <p>Price</p>
                    </div>
                    <div className="chart-canvas">
                      <svg viewBox="0 0 440 180" role="img" aria-label="선택 채권 가격 추이">
                        <path d="M28 146 H416 M28 92 H416 M28 38 H416" className="grid-line soft" />
                        <path d={trendPath} className="navy-line" />
                        {trend.map((point, index) => (
                          <g key={point.label}>
                            <circle
                              className="navy-dot"
                              cx={point.x}
                              cy={point.y}
                              onMouseEnter={() => setHoveredTrend(index)}
                              onMouseLeave={() => setHoveredTrend(null)}
                              r={hoveredTrend === index ? 5 : 3.5}
                            />
                            <text className="axis-label" x={point.x} y="169">{point.label}</text>
                          </g>
                        ))}
                      </svg>
                      {hoveredTrend !== null && (
                        <div className="chart-tooltip">
                          <strong>{trend[hoveredTrend].label}</strong>
                          <span>{formatPrice(trend[hoveredTrend].value)}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="chart-card">
                    <div className="chart-head">
                      <div>
                        <h4>시장금리와 선택 채권 비교</h4>
                        <span>국고채 3Y vs 선택 만기수익률</span>
                      </div>
                      <p>수익률</p>
                    </div>
                    <div className="chart-canvas">
                      <svg viewBox="0 0 390 180" role="img" aria-label="시장금리와 선택 채권 비교">
                        <path d="M34 146 H366 M34 92 H366 M34 38 H366" className="grid-line soft" />
                        <path d={comparisonLine} className="gold-line" />
                        <text className="axis-label y-axis" x="10" y="42">높음</text>
                        <text className="axis-label y-axis" x="10" y="148">낮음</text>
                        {comparison.map((point, index) => (
                          <g key={point.label}>
                            <circle
                              className="gold-dot"
                              cx={point.x}
                              cy={point.y}
                              onMouseEnter={() => setHoveredComparison(index)}
                              onMouseLeave={() => setHoveredComparison(null)}
                              r={hoveredComparison === index ? 5 : 3.8}
                            />
                            <text className="axis-label" x={point.x} y="169">{point.label}</text>
                          </g>
                        ))}
                      </svg>
                      {hoveredComparison !== null && (
                        <div className="chart-tooltip">
                          <strong>{comparison[hoveredComparison].label}</strong>
                          <span>{formatPercent(comparison[hoveredComparison].value)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </section>
              )}
            </div>
          </>
        )}
      </main>

      {isAiOpen && selectedBond && market && insight && (
        <div className="drawer-backdrop" onClick={() => setIsAiOpen(false)} role="presentation">
          <aside className="ai-drawer" aria-label="AI Analysis" onClick={(event) => event.stopPropagation()}>
            <div className="drawer-head">
              <div>
                <p className="ai-kicker">AI ANALYSIS</p>
                <h2>투자 관점 보조 분석</h2>
              </div>
              <button aria-label="AI 분석 닫기" onClick={() => setIsAiOpen(false)} type="button">Close</button>
            </div>
            <h3>{insight.headline}</h3>
            <div className="ai-grid drawer-grid">
              <article><strong>수익률 관점</strong><p>{insight.returnView}</p></article>
              <article><strong>위험 관점</strong><p>{insight.riskView}</p></article>
              <article><strong>확인할 점</strong><p>{insight.checkView}</p></article>
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
