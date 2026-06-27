"""
02_regressions.py — Three regressions for the AI Labor Impact Observatory.

Regressions (per spec §4):
  R1: observed_exposure ~ log(wage) + job_zone + health_dummy + admin_share
  R2: diffusion_gap     ~ health_dummy + log(wage) + job_zone
  R3: health-only: observed_exposure ~ admin_share + log(wage) + job_zone

All use robust (HC1) standard errors.
Employment-weighted when OEWS data is available.

FRAMING: Exposure is potential capability, not realized job loss.
These regressions describe cross-sectional associations, NOT causal effects.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm

DB_PATH = Path(__file__).resolve().parent.parent / "warehouse" / "aei.duckdb"
REPORT_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)


def load_mart() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_occupation_exposure").fetchdf()
    con.close()
    return df


def section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def run_wls(y: pd.Series, X: pd.DataFrame, weights: pd.Series | None,
            label: str) -> sm.regression.linear_model.RegressionResultsWrapper | None:
    """Run WLS (or OLS if no weights) with HC1 robust SEs."""
    mask = y.notna() & X.notna().all(axis=1)
    if weights is not None:
        mask &= weights.notna() & (weights > 0)
    if mask.sum() < X.shape[1] + 5:
        print(f"  [SKIP] {label} — insufficient observations ({mask.sum()})")
        return None

    y_clean = y[mask]
    X_clean = sm.add_constant(X[mask])
    if weights is not None:
        w_clean = weights[mask]
        model = sm.WLS(y_clean, X_clean, weights=w_clean)
    else:
        model = sm.OLS(y_clean, X_clean)

    result = model.fit(cov_type="HC1")
    print(f"  {label}")
    print(f"  N = {int(result.nobs)}, R² = {result.rsquared:.4f}, "
          f"Adj R² = {result.rsquared_adj:.4f}")
    if weights is not None:
        print(f"  Weighted: employment (tot_emp)")
    else:
        print(f"  Unweighted (OEWS employment not available)")
    print(f"  Robust SEs: HC1")
    print()
    print(result.summary2().tables[1].to_string(float_format="{:.4f}".format))
    return result


def regression1(df: pd.DataFrame) -> None:
    """R1: observed_exposure ~ log(wage) + job_zone + is_health + admin_share"""
    section("REGRESSION 1: Observed Exposure (full sample)")

    has_wages = df["a_median"].notna().any()
    if not has_wages:
        print("  OEWS wages not loaded. Running without log(wage) — partial specification.")
        print("  Download OEWS and re-run for the full model.\n")

    valid = df[df["observed_exposure"].notna()].copy()

    # Build X
    X_cols = {}
    if has_wages:
        valid = valid[valid["a_median"].notna() & (valid["a_median"] > 0)]
        X_cols["log_wage"] = np.log(valid["a_median"])
    X_cols["job_zone"] = valid["job_zone"]
    X_cols["is_health"] = valid["is_health"].astype(int)
    X_cols["admin_share"] = valid["admin_share"].fillna(0)

    X = pd.DataFrame(X_cols, index=valid.index)
    y = valid["observed_exposure"]
    weights = valid["tot_emp"] if has_wages else None

    run_wls(y, X, weights, "observed_exposure ~ " +
            ("log(wage) + " if has_wages else "") +
            "job_zone + is_health + admin_share")


def regression2(df: pd.DataFrame) -> None:
    """R2: diffusion_gap ~ is_health + log(wage) + job_zone"""
    section("REGRESSION 2: Diffusion Gap (full sample)")

    has_wages = df["a_median"].notna().any()
    if not has_wages:
        print("  OEWS wages not loaded. Running without log(wage) — partial specification.\n")

    valid = df[df["diffusion_gap"].notna()].copy()

    X_cols = {}
    X_cols["is_health"] = valid["is_health"].astype(int)
    if has_wages:
        valid = valid[valid["a_median"].notna() & (valid["a_median"] > 0)]
        X_cols["log_wage"] = np.log(valid["a_median"])
    X_cols["job_zone"] = valid["job_zone"]

    X = pd.DataFrame(X_cols, index=valid.index)
    y = valid["diffusion_gap"]
    weights = valid["tot_emp"] if has_wages else None

    run_wls(y, X, weights, "diffusion_gap ~ is_health + " +
            ("log(wage) + " if has_wages else "") +
            "job_zone")


def regression3(df: pd.DataFrame) -> None:
    """R3: Health-only: observed_exposure ~ admin_share + log(wage) + job_zone"""
    section("REGRESSION 3: Observed Exposure (health-sector only)")

    h = df[df["is_health"] & df["observed_exposure"].notna()].copy()
    has_wages = h["a_median"].notna().any()

    if not has_wages:
        print("  OEWS wages not loaded. Running without log(wage) — partial specification.\n")

    X_cols = {}
    X_cols["admin_share"] = h["admin_share"]
    if has_wages:
        h = h[h["a_median"].notna() & (h["a_median"] > 0)]
        X_cols["log_wage"] = np.log(h["a_median"])
    X_cols["job_zone"] = h["job_zone"]

    X = pd.DataFrame(X_cols, index=h.index)
    y = h["observed_exposure"]
    weights = h["tot_emp"] if has_wages else None

    run_wls(y, X, weights, "observed_exposure ~ admin_share + " +
            ("log(wage) + " if has_wages else "") +
            "job_zone  [health only]")


def main() -> None:
    print("AI Labor Impact Observatory — Regression Analysis")
    print("NOTE: These are cross-sectional associations, NOT causal estimates.")
    print(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

    df = load_mart()
    regression1(df)
    regression2(df)
    regression3(df)

    print(f"\n{'=' * 70}")
    print("  Done.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
