import type {
  AiExplainResponse,
  ApiErrorResponse,
  BondSnapshotResponse,
  HealthResponse,
  MarketResponse,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code = "API_ERROR",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    throw new ApiError(
      body?.error.message ?? "API 요청에 실패했습니다.",
      response.status,
      body?.error.code,
    );
  }

  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse & { connected: boolean }> {
  try {
    const health = await apiFetch<HealthResponse>("/health", { cache: "no-store" });
    return { ...health, connected: health.status === "ok" };
  } catch {
    return { status: "unavailable", connected: false };
  }
}

/** 시장금리(최신순). startDate/endDate를 안 주면 진짜 최신값, 주면 그 구간(최신순)만. */
export async function getMarketRates(
  params: { limit?: number; startDate?: string; endDate?: string } = {},
): Promise<MarketResponse> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 2));
  if (params.startDate) query.set("start_date", params.startDate);
  if (params.endDate) query.set("end_date", params.endDate);
  return apiFetch<MarketResponse>(`/api/market?${query.toString()}`, { cache: "no-store" });
}

/** Bond Screener용 — 359건 정도라 페이지네이션 없이 한 번에 전부 받아온다(docs/SKILL_1035.md 2-4). */
export async function getBondSnapshots(
  params: { referenceDate?: string } = {},
): Promise<BondSnapshotResponse> {
  const query = new URLSearchParams();
  if (params.referenceDate) query.set("reference_date", params.referenceDate);
  return apiFetch<BondSnapshotResponse>(`/api/bond-snapshot?${query.toString()}`, { cache: "no-store" });
}

/** AI Analysis 패널용 — ISIN이 Supabase에 없으면 ApiError(status 404, code "NOT_FOUND")를 던진다. */
export async function explainBond(isin: string): Promise<AiExplainResponse> {
  return apiFetch<AiExplainResponse>("/api/ai/explain", {
    method: "POST",
    body: JSON.stringify({ isin }),
    cache: "no-store",
  });
}
