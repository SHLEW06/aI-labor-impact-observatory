"""
02_regressions.py — Three regressions for the AI Labor Impact Observatory.

Specifications (per spec §4):
  R1: observed_exposure ~ log(wage) + job_zone + is_health + admin_share
  R2: diffusion_gap     ~ is_health + log(wage) + job_zone
  R3: health-only: observed_exposure ~ admin_share + log(wage) + job_zone

Canonical estimator (§4): **WLS with employment (tot_emp) weights**, robust
**HC1** standard errors. The canonical sample is the wage-non-null
subsample (so weighting and the log-wage covariate share the same support).

To isolate the *wage covariate* effect from the *weighting* effect, we
run a 2x2 decomposition per spec on a single common sample:

       │ no log_wage │ + log_wage
  ─────┼─────────────┼───────────
  OLS  │   (a)       │   (b)
  WLS  │   (c)       │   (d)

  Wage effect (estimator fixed): a→b under OLS, c→d under WLS.
  Weighting effect (covariates fixed): a→c without wage, b→d with wage.

The canonical headline comparison the memo will cite is (c) vs (d).

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

# Canonical estimator settings (per §4)
CANONICAL_WEIGHTS = "tot_emp"   # employment weights
CANONICAL_COV = "HC1"           # robust SEs
CANONICAL_ESTIMATOR = "WLS"     # weighted least squares


def load_mart() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_occupation_exposure").fetchdf()
    con.close()
    return df


def section(title: str) -> None:
    print(f"\n{'=' * 78}")
    print(f"  {title}")
    print(f"{'=' * 78}\n")


def fit_one(y: pd.Series, X: pd.DataFrame, weights: pd.Series | None,
            label: str) -> sm.regression.linear_model.RegressionResultsWrapper | None:
    """Fit OLS or WLS with HC1 robust SEs. Returns None if too few obs."""
    if len(y) < X.shape[1] + 5:
        print(f"  [SKIP] {label} — insufficient obs ({len(y)})")
        return None
    Xc = sm.add_constant(X)
    if weights is None:
        model = sm.OLS(y, Xc)
    else:
        model = sm.WLS(y, Xc, weights=weights)
    return model.fit(cov_type=CANONICAL_COV)


def print_result(label: str, res) -> None:
    if res is None:
        return
    print(f"  {label}")
    print(f"  N = {int(res.nobs)}, R² = {res.rsquared:.4f}, "
          f"Adj R² = {res.rsquared_adj:.4f}")
    print(f"  SEs: {CANONICAL_COV} (robust)")
    print()
    print(res.summary2().tables[1].to_string(float_format="{:.4f}".format))
    print()


def decompose(df: pd.DataFrame, *, y_col: str, covars: list[str],
              spec_label: str, restrict_to_health: bool = False) -> dict:
    """Run the 2x2 (OLS/WLS) x (no-wage/+wage) decomposition on a single
    common sample, then print and return the four fits."""

    section(spec_label)

    base = df[df[y_col].notna()].copy()
    if restrict_to_health:
        base = base[base["is_health"]]
    # admin_share is fillna(0) for non-health where it's structurally absent;
    # job_zone, is_health are not nullable in the mart by design but enforce here.
    for c in covars:
        if c == "admin_share":
            base["admin_share"] = base["admin_share"].fillna(0)
        base = base[base[c].notna()]

    # Build common sample = covariates valid AND wage valid AND weight valid
    sample = base[
        base["a_median"].notna() & (base["a_median"] > 0)
        & base["tot_emp"].notna() & (base["tot_emp"] > 0)
    ].copy()
    sample["log_wage"] = np.log(sample["a_median"])

    print(f"Common sample (covariates + wage + tot_emp all valid): n = {len(sample)}")
    print(f"  y = {y_col}; covars (no wage) = {covars}")
    print()

    y = sample[y_col].astype(float)
    w = sample["tot_emp"].astype(float)

    X_no  = sample[covars].copy()
    if "is_health" in X_no.columns:
        X_no["is_health"] = X_no["is_health"].astype(int)
    X_yes = X_no.copy()
    X_yes["log_wage"] = sample["log_wage"]

    fits = {
        "a) OLS, no log_wage":  fit_one(y, X_no,  None, "(a) OLS, no log_wage"),
        "b) OLS, + log_wage":   fit_one(y, X_yes, None, "(b) OLS, + log_wage"),
        "c) WLS, no log_wage":  fit_one(y, X_no,  w,    "(c) WLS [tot_emp], no log_wage"),
        "d) WLS, + log_wage":   fit_one(y, X_yes, w,    "(d) WLS [tot_emp], + log_wage"),
    }
    for k, r in fits.items():
        print(f"--- {k} ---")
        print_result(k, r)
    return {"spec": spec_label, "n": len(sample), "fits": fits, "covars": covars}


def fmt(x: float | None, digits: int = 4) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return " "
    return f"{x:.{digits}f}"


def comparison_table(rows: list[dict]) -> None:
    section("2x2 DECOMPOSITION: coefficient table")
    print("Cells: coef (SE) [p]. Sample is common across (a)-(d) within each spec.")
    print(f"Estimator: OLS or WLS (employment-weighted, weights={CANONICAL_WEIGHTS}).")
    print(f"SEs: {CANONICAL_COV} (robust).")
    print(f"Canonical spec for memo: (c) → (d) — both WLS.\n")

    for rec in rows:
        spec = rec["spec"]
        fits = rec["fits"]
        n = rec["n"]
        all_terms = []
        for key, res in fits.items():
            if res is None:
                continue
            for t in res.params.index:
                if t not in all_terms:
                    all_terms.append(t)

        print(f"--- {spec}  (common sample n = {n}) ---")
        header = f"{'term':<14}" + "".join(f"{k[:1]+': coef (SE) [p]':>34}" for k in fits.keys())
        print(header)
        for t in all_terms:
            cells = [f"{t:<14}"]
            for key, res in fits.items():
                if res is None or t not in res.params.index:
                    cells.append(f"{'':>34}")
                else:
                    coef = res.params[t]
                    se = res.bse[t]
                    p = res.pvalues[t]
                    cells.append(f"{f'{coef:+.4f} ({se:.4f}) [{p:.3f}]':>34}")
            print("".join(cells))

        r2_row = [f"{'R²':<14}"]
        for key, res in fits.items():
            r2_row.append(f"{(f'{res.rsquared:.4f}' if res is not None else ''):>34}")
        print("".join(r2_row))
        print()


def headline_check(rows: list[dict]) -> None:
    """Pin the canonical R3 admin_share coefficient and flag README impact."""
    section("CANONICAL R3 (health) under WLS — c→d wage-control delta")
    r3 = next(r for r in rows if r["spec"].startswith("R3"))
    fc = r3["fits"]["c) WLS, no log_wage"]
    fd = r3["fits"]["d) WLS, + log_wage"]
    n = r3["n"]
    if fc is None or fd is None:
        print("  [SKIP] missing fits")
        return
    coef_c = fc.params["admin_share"]; se_c = fc.bse["admin_share"]; p_c = fc.pvalues["admin_share"]
    coef_d = fd.params["admin_share"]; se_d = fd.bse["admin_share"]; p_d = fd.pvalues["admin_share"]
    print(f"  n = {n}  (all health SOCs with observed_exposure, a_median, tot_emp)")
    print(f"  (c) WLS no-wage : admin_share = {coef_c:+.4f}  (SE {se_c:.4f}, p {p_c:.4f})  R²={fc.rsquared:.4f}")
    print(f"  (d) WLS + wage  : admin_share = {coef_d:+.4f}  (SE {se_d:.4f}, p {p_d:.4f})  R²={fd.rsquared:.4f}")
    delta = coef_d - coef_c
    pct = 100 * delta / coef_c if coef_c else float("nan")
    print(f"  c → d delta     : {delta:+.4f}  ({pct:+.1f}%)")
    if "log_wage" in fd.params.index:
        print(f"  log_wage in (d) : {fd.params['log_wage']:+.4f}  "
              f"(SE {fd.bse['log_wage']:.4f}, p {fd.pvalues['log_wage']:.4f})")


def main() -> None:
    print("AI Labor Impact Observatory — Regression Analysis")
    print(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Canonical estimator: {CANONICAL_ESTIMATOR} weighted by `{CANONICAL_WEIGHTS}`; "
          f"robust SEs: {CANONICAL_COV}.")
    print("NOTE: These are cross-sectional associations, NOT causal estimates.")

    df = load_mart()

    rows = []
    rows.append(decompose(
        df, y_col="observed_exposure",
        covars=["job_zone", "is_health", "admin_share"],
        spec_label="R1: observed_exposure (full sample)",
    ))
    rows.append(decompose(
        df, y_col="diffusion_gap",
        covars=["is_health", "job_zone"],
        spec_label="R2: diffusion_gap (full sample)",
    ))
    rows.append(decompose(
        df, y_col="observed_exposure",
        covars=["admin_share", "job_zone"],
        spec_label="R3: observed_exposure (health-sector only)",
        restrict_to_health=True,
    ))

    # is_health is a 0/1 indicator — cast on the fly inside decompose's frame
    # by mapping bool→int after sample is built. Patch the X frames here.

    comparison_table(rows)
    headline_check(rows)

    print(f"\n{'=' * 78}")
    print("  Done.")
    print(f"{'=' * 78}")


if __name__ == "__main__":
    main()
