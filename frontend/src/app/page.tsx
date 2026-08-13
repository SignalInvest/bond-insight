"use client";

import { useState } from "react";

import { DashboardBody } from "@/components/DashboardBody";
import { Header } from "@/components/Header";

// Keep the default date aligned with the current Bond Market/Bond Overview data scope.
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
