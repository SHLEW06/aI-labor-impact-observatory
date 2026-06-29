"""
02_regressions.py — Three regressions for the AI Labor Impact Observatory.

Regressions (per spec §4):
  R1: observed_exposure ~ log(wage) + job_zone + health_dummy + admin_share
  R2: diffusion_gap     ~ health_dummy + log(wage) + job_zone
  R3: health-only: observed_exposure ~ admin_share + log(wage) + job_zone

All use robust (HC1) standard errors.
Employment-weighted when OEWS data is available.

When OEWS wages are present we ALSO run the no-wage variant on the same
covariates so old-vs-new comparisons (and the impact of dropped suppressed/
unmatched rows on the sample) are explicit.

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
        print(f"  Unweighted")
    print(f"  Robust SEs: HC1")
    print()
    print(result.summary2().tables[1].to_string(float_format="{:.4f}".format))
    print()
    return result


def regression1(df: pd.DataFrame) -> tuple:
    """R1: observed_exposure ~ [log(wage) +] job_zone + is_health + admin_share

    Always runs the no-wage variant. If OEWS wages are present, also runs
    the with-wage variant on the wage-non-null subsample.
    """
    section("REGRESSION 1: Observed Exposure (full sample)")

    valid = df[df["observed_exposure"].notna()].copy()
    has_wages = valid["a_median"].notna().any()

    # --- OLD (no wage) — full sample, unweighted ---
    print("--- OLD (no log_wage covariate, unweighted) ---")
    X_old = pd.DataFrame({
        "job_zone": valid["job_zone"],
        "is_health": valid["is_health"].astype(int),
        "admin_share": valid["admin_share"].fillna(0),
    }, index=valid.index)
    r_old = run_wls(
        valid["observed_exposure"], X_old, weights=None,
        label="observed_exposure ~ job_zone + is_health + admin_share",
    )

    r_new = None
    if has_wages:
        # --- NEW (with log_wage) — wage-non-null subsample, employment-weighted ---
        print("--- NEW (with log_wage, employment-weighted) ---")
        sub = valid[valid["a_median"].notna() & (valid["a_median"] > 0)].copy()
        X_new = pd.DataFrame({
            "log_wage": np.log(sub["a_median"]),
            "job_zone": sub["job_zone"],
            "is_health": sub["is_health"].astype(int),
            "admin_share": sub["admin_share"].fillna(0),
        }, index=sub.index)
        r_new = run_wls(
            sub["observed_exposure"], X_new, weights=sub["tot_emp"],
            label="observed_exposure ~ log(wage) + job_zone + is_health + admin_share",
        )
    return r_old, r_new


def regression2(df: pd.DataFrame) -> tuple:
    """R2: diffusion_gap ~ is_health + [log(wage) +] job_zone"""
    section("REGRESSION 2: Diffusion Gap (full sample)")

    valid = df[df["diffusion_gap"].notna()].copy()
    has_wages = valid["a_median"].notna().any()

    print("--- OLD (no log_wage covariate, unweighted) ---")
    X_old = pd.DataFrame({
        "is_health": valid["is_health"].astype(int),
        "job_zone": valid["job_zone"],
    }, index=valid.index)
    r_old = run_wls(
        valid["diffusion_gap"], X_old, weights=None,
        label="diffusion_gap ~ is_health + job_zone",
    )

    r_new = None
    if has_wages:
        print("--- NEW (with log_wage, employment-weighted) ---")
        sub = valid[valid["a_median"].notna() & (valid["a_median"] > 0)].copy()
        X_new = pd.DataFrame({
            "is_health": sub["is_health"].astype(int),
            "log_wage": np.log(sub["a_median"]),
            "job_zone": sub["job_zone"],
        }, index=sub.index)
        r_new = run_wls(
            sub["diffusion_gap"], X_new, weights=sub["tot_emp"],
            label="diffusion_gap ~ is_health + log(wage) + job_zone",
        )
    return r_old, r_new


def regression3(df: pd.DataFrame) -> tuple:
    """R3: Health-only: observed_exposure ~ admin_share + [log(wage) +] job_zone"""
    section("REGRESSION 3: Observed Exposure (health-sector only)")

    h = df[df["is_health"] & df["observed_exposure"].notna()].copy()
    has_wages = h["a_median"].notna().any()

    print("--- OLD (no log_wage covariate, unweighted) ---")
    X_old = pd.DataFrame({
        "admin_share": h["admin_share"],
        "job_zone": h["job_zone"],
    }, index=h.index)
    r_old = run_wls(
        h["observed_exposure"], X_old, weights=None,
        label="observed_exposure ~ admin_share + job_zone  [health only]",
    )

    r_new = None
    if has_wages:
        print("--- NEW (with log_wage, employment-weighted) ---")
        sub = h[h["a_median"].notna() & (h["a_median"] > 0)].copy()
        X_new = pd.DataFrame({
            "admin_share": sub["admin_share"],
            "log_wage": np.log(sub["a_median"]),
            "job_zone": sub["job_zone"],
        }, index=sub.index)
        r_new = run_wls(
            sub["observed_exposure"], X_new, weights=sub["tot_emp"],
            label="observed_exposure ~ admin_share + log(wage) + job_zone  [health only]",
        )
    return r_old, r_new


def comparison_table(results: dict) -> None:
    """Print a compact side-by-side comparison of OLD vs NEW coefficients."""
    section("OLD vs NEW: side-by-side comparison")
    print("Note: NEW restricts to OEWS wage-non-null rows AND weights by employment;")
    print("OLD uses the full sample, unweighted. Different samples → not nested tests.\n")

    for spec, (r_old, r_new) in results.items():
        print(f"--- {spec} ---")
        rows = []
        if r_old is not None:
            for name in r_old.params.index:
                rows.append({
                    "term": name,
                    "OLD coef": r_old.params[name],
                    "OLD SE": r_old.bse[name],
                    "OLD p": r_old.pvalues[name],
                })
        if r_new is not None:
            new_terms = {}
            for name in r_new.params.index:
                new_terms[name] = {
                    "NEW coef": r_new.params[name],
                    "NEW SE": r_new.bse[name],
                    "NEW p": r_new.pvalues[name],
                }
            seen = set(r["term"] for r in rows)
            for r in rows:
                if r["term"] in new_terms:
                    r.update(new_terms[r["term"]])
            for term, vals in new_terms.items():
                if term not in seen:
                    row = {"term": term, "OLD coef": None, "OLD SE": None, "OLD p": None}
                    row.update(vals)
                    rows.append(row)

        n_old = int(r_old.nobs) if r_old is not None else None
        n_new = int(r_new.nobs) if r_new is not None else None
        tbl = pd.DataFrame(rows)
        cols = ["term", "OLD coef", "OLD SE", "OLD p", "NEW coef", "NEW SE", "NEW p"]
        tbl = tbl.reindex(columns=cols)
        print(tbl.to_string(index=False, float_format=lambda x: f"{x:.4f}" if pd.notna(x) else " "))
        print(f"  n_old = {n_old}    n_new = {n_new}\n")


def main() -> None:
    print("AI Labor Impact Observatory — Regression Analysis")
    print("NOTE: These are cross-sectional associations, NOT causal estimates.")
    print(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

    df = load_mart()
    results = {}
    results["R1: observed_exposure (full)"]   = regression1(df)
    results["R2: diffusion_gap (full)"]       = regression2(df)
    results["R3: observed_exposure (health)"] = regression3(df)

    comparison_table(results)

    print(f"\n{'=' * 70}")
    print("  Done.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
