import { readFile } from "node:fs/promises";
import path from "node:path";

import { NextResponse } from "next/server";

// Tableau(yunseo_3h48m)의 채권명 표기가 Supabase `bonds.bond_name`과 달라서(예:
// "국고01875-5103(21-2)" vs "국고채권 01875-5103(21-2)") 이름으로 바로 백엔드를 조회할 수 없다.
// 그래서 yunseo/output/기본 데이터.csv에서 같은 채권명으로 ISIN을 먼저 찾고, 그 ISIN으로
// 진짜 백엔드(FastAPI + Supabase, /api/bonds/{isin})를 조회하는 다리 역할만 한다.
// Supabase는 이미 2026-08-12에 전체 채권 업로드가 끝나 있음 (docs/SKILL.md 참고).
const YUNSEO_OUTPUT_DIR = path.join(process.cwd(), "..", "yunseo", "output");
const BASE_DATA_CSV = path.join(YUNSEO_OUTPUT_DIR, "기본 데이터.csv");
const DERIVED_DATA_CSV = path.join(YUNSEO_OUTPUT_DIR, "파생 데이터.csv");

const BACKEND_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

function parseCsv(content: string): Record<string, string>[] {
  const lines = content.replace(/^﻿/, "").split(/\r?\n/).filter((line) => line.length > 0);
  const [headerLine, ...rows] = lines;
  if (!headerLine) return [];
  const headers = headerLine.split(",");

  return rows.map((line) => {
    const cells = line.split(",");
    const record: Record<string, string> = {};
    headers.forEach((header, index) => {
      record[header] = cells[index] ?? "";
    });
    return record;
  });
}

async function loadCsv(filePath: string): Promise<Record<string, string>[]> {
  const content = await readFile(filePath, "utf-8");
  return parseCsv(content);
}

async function fetchFromBackend(isin: string): Promise<unknown | null> {
  try {
    const response = await fetch(`${BACKEND_API_URL}/api/bonds/${isin}`, { cache: "no-store" });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    // 백엔드(uvicorn)가 꺼져 있는 경우 등 — 로컬 CSV만으로 대체 응답
    return null;
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const bondName = searchParams.get("bondName")?.trim();

  if (!bondName) {
    return NextResponse.json({ error: "bondName query parameter is required" }, { status: 400 });
  }

  try {
    const [baseRows, derivedRows] = await Promise.all([loadCsv(BASE_DATA_CSV), loadCsv(DERIVED_DATA_CSV)]);

    const base = baseRows.find((row) => row.bond_name.trim() === bondName);
    if (!base) {
      return NextResponse.json({ found: false, bondName }, { status: 404 });
    }

    const derived = derivedRows.find((row) => row.isin === base.isin) ?? null;
    const backend = await fetchFromBackend(base.isin);

    return NextResponse.json({
      found: true,
      isin: base.isin,
      backendAvailable: backend !== null,
      base,
      derived,
      backend,
    });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "unknown error" },
      { status: 500 },
    );
  }
}
