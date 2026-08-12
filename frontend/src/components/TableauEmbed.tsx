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

interface TableauEmbedProps {
  src: string;
  className?: string;
  /** 태블로에서 행(마크)을 선택/해제할 때 호출. 선택 해제 시 null. */
  onMarkSelectionChange?: (fields: Record<string, string> | null) => void;
}

export function TableauEmbed({ src, className, onMarkSelectionChange }: TableauEmbedProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;

    loadTableauModule()
      .then(({ TableauEventType }) => {
        if (cancelled || !containerRef.current) return;

        containerRef.current.innerHTML = "";
        const viz = document.createElement("tableau-viz");
        viz.setAttribute("src", src);
        viz.setAttribute("toolbar", "bottom");
        viz.setAttribute("hide-tabs", "");
        viz.style.width = "100%";
        viz.style.height = "100%";
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
  }, [src, onMarkSelectionChange]);

  return <div ref={containerRef} className={className} />;
}
