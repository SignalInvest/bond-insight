from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_BOND_MARKET = PROJECT_ROOT / "data" / "raw" / "bond_market" / "bond_market_raw.csv"
RAW_BOND_INFO = PROJECT_ROOT / "data" / "raw" / "bond_info" / "bond_info_raw.csv"
MARKET_RATES = PROJECT_ROOT / "data" / "processed" / "market_rates_daily.csv"
OUTPUT = PROJECT_ROOT / "data" / "processed" / "bond_credit_spread.csv"

CALCULATED = "CALCULATED"
MISSING_YTM = "MISSING_YTM"
MISSING_MATURITY = "MISSING_MATURITY"
MISSING_BENCHMARK = "MISSING_BENCHMARK"


def interpolate_treasury_rate(years: float, rate_3y: float, rate_5y: float, rate_10y: float) -> float:
    """Return a maturity-matched treasury rate using linear interpolation."""
    if pd.isna(years) or any(pd.isna(rate) for rate in (rate_3y, rate_5y, rate_10y)):
        return float("nan")
    if years <= 3:
        return float(rate_3y)
    if years <= 5:
        return float(rate_3y + (rate_5y - rate_3y) * (years - 3) / 2)
    if years <= 10:
        return float(rate_5y + (rate_10y - rate_5y) * (years - 5) / 5)
    return float(rate_10y)


def build_credit_spread(info: pd.DataFrame, bond_market: pd.DataFrame, rates: pd.DataFrame) -> pd.DataFrame:
    info_dates = info[["isinCd", "bondExprDt"]].drop_duplicates("isinCd")
    merged = bond_market[["isinCd", "basDt", "clprBnfRt"]].merge(info_dates, on="isinCd", how="left")
    merged["reference_date"] = pd.to_datetime(merged["basDt"], format="%Y%m%d", errors="coerce")
    merged["maturity_date"] = pd.to_datetime(merged["bondExprDt"], format="%Y%m%d", errors="coerce")
    merged["remaining_years"] = (merged["maturity_date"] - merged["reference_date"]).dt.days / 365.25
    merged["ytm"] = pd.to_numeric(merged["clprBnfRt"], errors="coerce")

    benchmark = rates.rename(columns={"date": "reference_date"}).copy()
    benchmark["reference_date"] = pd.to_datetime(benchmark["reference_date"], errors="coerce")
    merged = merged.merge(
        benchmark[["reference_date", "treasury_3y", "treasury_5y", "treasury_10y"]],
        on="reference_date",
        how="left",
    )
    merged["benchmark_treasury_rate"] = [
        interpolate_treasury_rate(years, r3, r5, r10)
        for years, r3, r5, r10 in zip(
            merged["remaining_years"], merged["treasury_3y"], merged["treasury_5y"], merged["treasury_10y"]
        )
    ]
    merged["credit_spread"] = merged["ytm"] - merged["benchmark_treasury_rate"]
    merged["calculation_status"] = CALCULATED
    merged.loc[merged["ytm"].isna(), "calculation_status"] = MISSING_YTM
    merged.loc[merged["remaining_years"].isna(), "calculation_status"] = MISSING_MATURITY
    merged.loc[merged["benchmark_treasury_rate"].isna(), "calculation_status"] = MISSING_BENCHMARK

    return merged[[
        "isinCd", "reference_date", "remaining_years", "ytm",
        "benchmark_treasury_rate", "credit_spread", "calculation_status",
    ]]


def main() -> None:
    info = pd.read_csv(RAW_BOND_INFO, dtype=str, usecols=["isinCd", "bondExprDt"])
    bond_market = pd.read_csv(RAW_BOND_MARKET, dtype=str, usecols=["isinCd", "basDt", "clprBnfRt"])
    rates = pd.read_csv(MARKET_RATES)
    result = build_credit_spread(info, bond_market, rates)
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"[DONE] Credit spread CSV -> {OUTPUT} ({len(result)} rows)")
    print(result["calculation_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
