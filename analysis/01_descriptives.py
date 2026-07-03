"""
01_descriptives.py — Summary statistics for mart_occupation_exposure.

Outputs:
  - Overall summary stats (N, means, medians, SDs for key measures)
  - Top 15 / bottom 15 theoretically exposed occupations (overall)
  - Top 15 / bottom 15 observed exposure (overall)
  - Health-sector summary: admin_share vs clinical_share distribution
  - Coverage report (non-null rates for each key column)

All output goes to stdout. Redirect to a file if needed:
    python analysis/01_descriptives.py > reports/descriptives.txt
"""

import sys
from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "warehouse" / "aei.duckdb"


def load_mart() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_occupation_exposure").fetchdf()
    con.close()
    return df


def section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def coverage_report(df: pd.DataFrame) -> None:
    section("COVERAGE REPORT")
    key_cols = [
        "theoretical_exposure", "observed_exposure", "diffusion_gap",
        "job_zone", "admin_share", "clinical_share",
        "tot_emp", "a_median", "a_mean",
    ]
    for col in key_cols:
        n = df[col].notna().sum()
        pct = 100 * n / len(df)
        print(f"  {col:30s}  {n:>4d} / {len(df)}  ({pct:5.1f}%)")


def summary_stats(df: pd.DataFrame) -> None:
    section("SUMMARY STATISTICS (all 798 occupations)")
    measures = ["theoretical_exposure", "observed_exposure", "diffusion_gap"]
    stats = df[measures].describe().T[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
    print(stats.to_string(float_format="{:.4f}".format))

    has_wages = df["a_median"].notna().any()
    if has_wages:
        print("\n  Wage statistics (non-suppressed occupations):")
        wage_df = df[df["a_median"].notna() & ~df["suppressed"]]
        wage_stats = wage_df[["a_median", "a_mean", "tot_emp"]].describe().T
        print(wage_stats.to_string(float_format="{:.0f}".format))
    else:
        print("\n  [OEWS wages not yet loaded — skipping wage statistics]")


def top_bottom(df: pd.DataFrame, col: str, label: str, n: int = 15) -> None:
    section(f"TOP {n} / BOTTOM {n}: {label}")
    valid = df[df[col].notna()].copy()
    valid = valid.sort_values(col, ascending=False)

    print(f"  TOP {n}:")
    top = valid.head(n)[["soc_code", "soc_title", col]].reset_index(drop=True)
    top.index = range(1, n + 1)
    print(top.to_string(float_format="{:.4f}".format))

    print(f"\n  BOTTOM {n}:")
    bottom = valid.tail(n)[["soc_code", "soc_title", col]].reset_index(drop=True)
    bottom.index = range(1, n + 1)
    print(bottom.to_string(float_format="{:.4f}".format))


def health_sector(df: pd.DataFrame) -> None:
    section("HEALTH-SECTOR ANALYSIS (SOC groups 29 + 31)")
    h = df[df["is_health"]].copy()
    print(f"  Health occupations: {len(h)}")
    print(f"  With observed exposure: {h['observed_exposure'].notna().sum()}")
    print()

    measures = [
        "theoretical_exposure", "observed_exposure", "diffusion_gap",
        "admin_share", "clinical_share",
    ]
    stats = h[measures].describe().T[["count", "mean", "std", "min", "50%", "max"]]
    print(stats.to_string(float_format="{:.4f}".format))

    # Top diffusion gaps within health
    print(f"\n  Top 10 diffusion gaps (health):")
    gap = h[h["diffusion_gap"].notna()].sort_values("diffusion_gap", ascending=False).head(10)
    cols = ["soc_code", "soc_title", "theoretical_exposure", "observed_exposure",
            "diffusion_gap", "admin_share", "clinical_share"]
    print(gap[cols].to_string(index=False, float_format="{:.4f}".format))

    # Admin-heavy vs clinical-heavy
    print(f"\n  Admin-heavy occupations (admin_share > clinical_share):")
    admin_heavy = h[h["admin_share"] > h["clinical_share"]].sort_values("admin_share", ascending=False)
    print(f"    Count: {len(admin_heavy)}")
    if len(admin_heavy) > 0:
        print(f"    Mean observed_exposure: {admin_heavy['observed_exposure'].mean():.4f}")
        print(f"    Top 5:")
        print(admin_heavy[["soc_code", "soc_title", "admin_share", "clinical_share",
                           "observed_exposure"]].head(5).to_string(index=False, float_format="{:.4f}".format))

    print(f"\n  Clinical-heavy occupations (clinical_share > admin_share):")
    clinical_heavy = h[h["clinical_share"] > h["admin_share"]].sort_values("clinical_share", ascending=False)
    print(f"    Count: {len(clinical_heavy)}")
    if len(clinical_heavy) > 0:
        print(f"    Mean observed_exposure: {clinical_heavy['observed_exposure'].mean():.4f}")
        print(f"    Top 5:")
        print(clinical_heavy[["soc_code", "soc_title", "admin_share", "clinical_share",
                              "observed_exposure"]].head(5).to_string(index=False, float_format="{:.4f}".format))

    # Pairwise correlations within health (backing the README/memo headline)
    print("\n  Pairwise correlations within health (Pearson, r):")
    corr_sample = h[h["observed_exposure"].notna()].copy()
    pairs = [
        ("admin_share",    "observed_exposure"),
        ("clinical_share", "observed_exposure"),
        ("admin_share",    "theoretical_exposure"),
    ]
    n_corr = len(corr_sample)
    for x, y in pairs:
        r = corr_sample[[x, y]].corr().iloc[0, 1]
        print(f"    r({x}, {y}) = {r:+.3f}   [n = {n_corr}]")


def exposure_by_job_zone(df: pd.DataFrame) -> None:
    section("EXPOSURE BY JOB ZONE (education proxy)")
    jz = df[df["job_zone"].notna()].groupby("job_zone").agg(
        n=("soc_code", "count"),
        mean_theoretical=("theoretical_exposure", "mean"),
        mean_observed=("observed_exposure", "mean"),
        mean_gap=("diffusion_gap", "mean"),
    ).reset_index()
    print(jz.to_string(index=False, float_format="{:.4f}".format))


def main() -> None:
    df = load_mart()
    print(f"AI Labor Impact Observatory — Descriptive Statistics")
    print(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Mart rows: {len(df)}")

    coverage_report(df)
    summary_stats(df)
    top_bottom(df, "theoretical_exposure", "Theoretical Exposure (Eloundou β)")
    top_bottom(df, "observed_exposure", "Observed Exposure (AEI)")
    health_sector(df)
    exposure_by_job_zone(df)

    print(f"\n{'=' * 70}")
    print("  Done.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
