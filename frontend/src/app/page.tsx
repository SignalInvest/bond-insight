"use client";

import { useState } from "react";

import { DashboardBody } from "@/components/DashboardBody";
import { Header } from "@/components/Header";

// Bond Market/Bond Overview 데이터가 아직 2026-08-07 하루치뿐이라 기본값으로 고정 (docs/SKILL_1034.md 3-2).
const DEFAULT_REFERENCE_DATE = "2026-08-07";

export default function HomePage() {
  const [referenceDate, setReferenceDate] = useState(DEFAULT_REFERENCE_DATE);

  return (
    <>
      <Header referenceDate={referenceDate} onReferenceDateChange={setReferenceDate} />
      <DashboardBody referenceDate={referenceDate} />
    </>
  );
}
