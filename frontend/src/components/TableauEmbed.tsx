"use client";

import { useEffect, useRef } from "react";

const TABLEAU_MODULE_SRC = "https://public.tableau.com/javascripts/api/tableau.embedding.3.latest.js";

// 공식 타입 정의가 없어서 실제 쓰는 부분만 최소한으로 선언.
// 참고: https://help.tableau.com/current/api/embedding_api/en-us/docs/embedding_api_select_marks.html
interface TableauMarksDataTable {
  columns: { fieldName: string }[];
  data: { formattedValue: string }[][];
}

interface TableauMarksCollection {
  data: TableauMarksDataTable[];
}

interface TableauMarkSelectionEvent extends Event {
  detail: {
    getMarksAsync: () => Promise<TableauMarksCollection>;
  };
}

interface TableauEmbeddingModule {
  TableauEventType: { MarkSelectionChanged: string; FirstInteractive: string };
}

// 정적 분석 대상 URL이 아니라 런타임에 그대로 브라우저 네이티브 import()로 실행되도록,
// 번들러(Turbopack/webpack)가 이 문자열을 로컬 모듈처럼 해석하지 않게 우회.
const dynamicImport = (specifier: string): Promise<TableauEmbeddingModule> =>
  new Function("specifier", "return import(specifier)")(specifier) as Promise<TableauEmbeddingModule>;

let modulePromise: Promise<TableauEmbeddingModule> | null = null;
function loadTableauModule(): Promise<TableauEmbeddingModule> {
  if (!modulePromise) {
    modulePromise = dynamicImport(TABLEAU_MODULE_SRC);
  }
  return modulePromise;
}

/** 선택된 마크(행) 하나의 필드를 { 컬럼명: 표시값 } 형태로 변환. 여러 개 선택 시 첫 번째만 사용. */
function extractSelectedFields(marksData: TableauMarksDataTable | undefined): Record<string, string> | null {
  const row = marksData?.data[0];
  if (!marksData || !row) return null;

  const fields: Record<string, string> = {};
  marksData.columns.forEach((column, index) => {
    fields[column.fieldName] = row[index]?.formattedValue ?? "";
  });
  return fields;
}

/** Tableau URL 쿼리는 `:device=desktop`처럼 콜론이 인코딩되면 안 돼서 URLSearchParams 대신 직접 이어붙임. */
function withDesktopDeviceParam(src: string, device: "desktop" | "tablet" | "phone"): string {
  const separator = src.includes("?") ? "&" : "?";
  return `${src}${separator}:device=${device}`;
}

interface TableauEmbedProps {
  src: string;
  className?: string;
  /** 태블로에서 행(마크)을 선택/해제할 때 호출. 선택 해제 시 null. */
  onMarkSelectionChange?: (fields: Record<string, string> | null) => void;
  /**
   * 뷰포트가 좁아도 Tableau가 모바일(세로 버튼) 레이아웃으로 자동 전환하지 않도록 강제.
   * 기본값 desktop — Bond Screener 필터 버튼 7개가 한 줄로 나오려면 이게 꼭 필요함.
   */
  device?: "desktop" | "tablet" | "phone";
  /** Tableau Desktop 원본 대시보드 기준 크기(px). 이보다 좁은 화면에서는 부모가 가로 스크롤 처리. */
  width?: number;
  height?: number;
}

export function TableauEmbed({
  src,
  className,
  onMarkSelectionChange,
  device = "desktop",
  width = 1200,
  height = 700,
}: TableauEmbedProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    loadTableauModule()
      .then(({ TableauEventType }) => {
        if (cancelled || !containerRef.current) return;

        containerRef.current.innerHTML = "";
        const viz = document.createElement("tableau-viz");
        viz.setAttribute("src", withDesktopDeviceParam(src, device));
        viz.setAttribute("toolbar", "bottom");
        viz.setAttribute("hide-tabs", "");
        // <tableau-viz>가 공식 지원하는 디바이스 강제 속성 (URL 파라미터와 이중 보장).
        viz.setAttribute("device", device);
        viz.style.width = `${width}px`;
        viz.style.height = `${height}px`;
        viz.style.display = "block";

        viz.addEventListener(TableauEventType.MarkSelectionChanged, (event) => {
          (event as TableauMarkSelectionEvent).detail
            .getMarksAsync()
            .then((marks) => {
              const fields = extractSelectedFields(marks.data[0]);
              // 실제 필드명 확인용 — 콘솔에서 컬럼명을 보고 BondInsight의 FIELD_CANDIDATES를 맞추세요.
              console.debug("[Tableau] selected mark fields:", fields);
              onMarkSelectionChange?.(fields);
            })
            .catch((error) => console.warn("Tableau mark selection 처리 실패:", error));
        });

        containerRef.current.appendChild(viz);
      })
      .catch((error) => {
        if (cancelled || !containerRef.current) return;
        containerRef.current.textContent = error instanceof Error ? error.message : String(error);
      });

    return () => {
      cancelled = true;
    };
  }, [src, onMarkSelectionChange, device, width, height]);

  // 부모 폭이 1200px보다 좁으면 대시보드를 찌그러뜨리는 대신 가로 스크롤을 보여준다
  // (요구사항 4, 5) — 실제 크기는 안쪽 <tableau-viz>에 고정 width/height로 부여됨.
  return (
    <div
      ref={containerRef}
      className={className}
      style={{ width: "100%", minWidth: 0, overflowX: "auto" }}
    />
  );
}
