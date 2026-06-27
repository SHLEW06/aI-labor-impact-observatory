"""
03_figures.py — Six publication-quality figures for the AI Labor Impact Observatory.

Figures:
  1. Top 15 / bottom 15 exposed occupations (horizontal bar)
  2. Theoretical vs. observed scatter, 45° line, healthcare highlighted
  3. Exposure by wage decile (requires OEWS data)
  4. Exposure by Job Zone (education proxy)
  5. Healthcare: admin_share vs observed_exposure
  6. Diffusion gap ranked within healthcare

All saved to figures/ as PNG.
"""

from pathlib import Path

import duckdb
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "warehouse" / "aei.duckdb"
FIG_DIR = Path(__file__).resolve().parent.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# Consistent style
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
})

HEALTH_COLOR = "#D64550"
OTHER_COLOR = "#4A90D9"
ADMIN_COLOR = "#E8A838"
CLINICAL_COLOR = "#5CB85C"


def load_mart() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_occupation_exposure").fetchdf()
    con.close()
    return df


def shorten_title(title: str, max_len: int = 40) -> str:
    if len(title) <= max_len:
        return title
    return title[: max_len - 3].rsplit(" ", 1)[0] + "..."


def fig1_top_bottom_exposure(df: pd.DataFrame) -> None:
    """Top 15 / bottom 15 theoretically exposed occupations."""
    valid = df[df["theoretical_exposure"].notna()].copy()
    valid["short_title"] = valid["soc_title"].apply(shorten_title)
    valid = valid.sort_values("theoretical_exposure")

    top15 = valid.tail(15)
    bot15 = valid.head(15)
    combined = pd.concat([bot15, top15])

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = [HEALTH_COLOR if h else OTHER_COLOR for h in combined["is_health"]]
    ax.barh(range(len(combined)), combined["theoretical_exposure"], color=colors)
    ax.set_yticks(range(len(combined)))
    ax.set_yticklabels(combined["short_title"], fontsize=8)
    ax.set_xlabel("Theoretical Exposure (Eloundou β)")
    ax.set_title("Top 15 & Bottom 15 Occupations by Theoretical AI Exposure")
    ax.axhline(y=14.5, color="gray", linestyle="--", linewidth=0.8)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=HEALTH_COLOR, label="Healthcare"),
                       Patch(facecolor=OTHER_COLOR, label="Other")]
    ax.legend(handles=legend_elements, loc="lower right")

    fig.savefig(FIG_DIR / "fig1_top_bottom_exposure.png")
    plt.close(fig)
    print("  [+] fig1_top_bottom_exposure.png")


def fig2_theoretical_vs_observed(df: pd.DataFrame) -> None:
    """Theoretical vs. observed scatter with 45° line."""
    valid = df[df["theoretical_exposure"].notna() & df["observed_exposure"].notna()].copy()
    health = valid[valid["is_health"]]
    other = valid[~valid["is_health"]]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(other["theoretical_exposure"], other["observed_exposure"],
               alpha=0.3, s=15, color=OTHER_COLOR, label=f"Other (n={len(other)})", zorder=2)
    ax.scatter(health["theoretical_exposure"], health["observed_exposure"],
               alpha=0.7, s=30, color=HEALTH_COLOR, label=f"Healthcare (n={len(health)})",
               edgecolors="white", linewidth=0.5, zorder=3)

    # 45° line
    lim = max(valid["theoretical_exposure"].max(), valid["observed_exposure"].max()) * 1.05
    ax.plot([0, lim], [0, lim], "k--", linewidth=0.8, alpha=0.5, label="45° line (full diffusion)")

    ax.set_xlabel("Theoretical Exposure (Eloundou β)")
    ax.set_ylabel("Observed Exposure (AEI)")
    ax.set_title("Theoretical vs. Observed AI Exposure by Occupation")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)

    # Annotate a few interesting health occupations
    for _, row in health.nlargest(3, "diffusion_gap").iterrows():
        ax.annotate(shorten_title(row["soc_title"], 30),
                    (row["theoretical_exposure"], row["observed_exposure"]),
                    fontsize=7, alpha=0.8,
                    xytext=(5, 5), textcoords="offset points")

    fig.savefig(FIG_DIR / "fig2_theoretical_vs_observed.png")
    plt.close(fig)
    print("  [+] fig2_theoretical_vs_observed.png")


def fig3_exposure_by_wage_decile(df: pd.DataFrame) -> None:
    """Exposure by wage decile (requires OEWS a_median)."""
    valid = df[df["a_median"].notna() & df["theoretical_exposure"].notna()].copy()
    if len(valid) < 20:
        print("  [SKIP] fig3 — OEWS wages not loaded (download manually from bls.gov)")
        return

    valid["wage_decile"] = pd.qcut(valid["a_median"], 10, labels=False, duplicates="drop") + 1

    grouped = valid.groupby("wage_decile").agg(
        mean_theoretical=("theoretical_exposure", "mean"),
        mean_observed=("observed_exposure", "mean"),
        n=("soc_code", "count"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    x = grouped["wage_decile"]
    w = 0.35
    ax.bar(x - w / 2, grouped["mean_theoretical"], w, label="Theoretical", color=OTHER_COLOR)
    ax.bar(x + w / 2, grouped["mean_observed"], w, label="Observed", color=HEALTH_COLOR)
    ax.set_xlabel("Wage Decile (1 = lowest)")
    ax.set_ylabel("Mean Exposure")
    ax.set_title("AI Exposure by Wage Decile")
    ax.legend()
    ax.set_xticks(range(1, 11))

    fig.savefig(FIG_DIR / "fig3_exposure_by_wage_decile.png")
    plt.close(fig)
    print("  [+] fig3_exposure_by_wage_decile.png")


def fig4_exposure_by_job_zone(df: pd.DataFrame) -> None:
    """Exposure by Job Zone (education proxy)."""
    valid = df[df["job_zone"].notna() & df["theoretical_exposure"].notna()].copy()

    grouped = valid.groupby("job_zone").agg(
        mean_theoretical=("theoretical_exposure", "mean"),
        mean_observed=("observed_exposure", "mean"),
        n=("soc_code", "count"),
    ).reset_index()

    jz_labels = {
        2: "Zone 2\nHS + Training",
        3: "Zone 3\nVocational/\nAssociate's",
        4: "Zone 4\nBachelor's",
        5: "Zone 5\nGraduate/\nProfessional",
    }

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(grouped))
    w = 0.35
    ax.bar(x - w / 2, grouped["mean_theoretical"], w, label="Theoretical", color=OTHER_COLOR)
    ax.bar(x + w / 2, grouped["mean_observed"], w, label="Observed", color=HEALTH_COLOR)
    ax.set_xlabel("O*NET Job Zone (Education Proxy)")
    ax.set_ylabel("Mean Exposure")
    ax.set_title("AI Exposure by Education Level (Job Zone)")
    ax.set_xticks(x)
    ax.set_xticklabels([jz_labels.get(int(jz), str(int(jz))) for jz in grouped["job_zone"]], fontsize=9)
    ax.legend()

    # Add count labels
    for i, row in grouped.iterrows():
        ax.text(x[i], max(row["mean_theoretical"], row["mean_observed"]) + 0.005,
                f"n={int(row['n'])}", ha="center", fontsize=8, color="gray")

    fig.savefig(FIG_DIR / "fig4_exposure_by_job_zone.png")
    plt.close(fig)
    print("  [+] fig4_exposure_by_job_zone.png")


def fig5_health_admin_vs_observed(df: pd.DataFrame) -> None:
    """Healthcare: admin_share vs observed_exposure."""
    h = df[df["is_health"] & df["observed_exposure"].notna()].copy()

    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(h["admin_share"], h["observed_exposure"],
                         c=h["clinical_share"], cmap="RdYlGn", s=40,
                         edgecolors="gray", linewidth=0.5, zorder=2)
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label("Clinical Share")

    # Fit line
    mask = h["admin_share"].notna() & h["observed_exposure"].notna()
    if mask.sum() > 2:
        z = np.polyfit(h.loc[mask, "admin_share"], h.loc[mask, "observed_exposure"], 1)
        p = np.poly1d(z)
        x_fit = np.linspace(h["admin_share"].min(), h["admin_share"].max(), 100)
        ax.plot(x_fit, p(x_fit), "--", color="gray", alpha=0.7, linewidth=1)

    ax.set_xlabel("Admin Task Share (importance-weighted)")
    ax.set_ylabel("Observed AI Exposure (AEI)")
    ax.set_title("Healthcare Occupations: Administrative Task Share vs. Observed AI Usage")

    # Annotate outliers
    for _, row in h.nlargest(3, "observed_exposure").iterrows():
        ax.annotate(shorten_title(row["soc_title"], 28),
                    (row["admin_share"], row["observed_exposure"]),
                    fontsize=7, alpha=0.8,
                    xytext=(5, 5), textcoords="offset points")
    for _, row in h.nlargest(3, "admin_share").iterrows():
        if row["soc_title"] not in h.nlargest(3, "observed_exposure")["soc_title"].values:
            ax.annotate(shorten_title(row["soc_title"], 28),
                        (row["admin_share"], row["observed_exposure"]),
                        fontsize=7, alpha=0.8,
                        xytext=(5, -10), textcoords="offset points")

    fig.savefig(FIG_DIR / "fig5_health_admin_vs_observed.png")
    plt.close(fig)
    print("  [+] fig5_health_admin_vs_observed.png")


def fig6_health_diffusion_gap(df: pd.DataFrame) -> None:
    """Diffusion gap ranked within healthcare."""
    h = df[df["is_health"] & df["diffusion_gap"].notna()].copy()
    h = h.sort_values("diffusion_gap", ascending=True)
    h["short_title"] = h["soc_title"].apply(lambda t: shorten_title(t, 45))

    fig, ax = plt.subplots(figsize=(10, max(6, len(h) * 0.18)))
    colors = [ADMIN_COLOR if row["admin_share"] > row["clinical_share"]
              else CLINICAL_COLOR for _, row in h.iterrows()]
    ax.barh(range(len(h)), h["diffusion_gap"], color=colors)
    ax.set_yticks(range(len(h)))
    ax.set_yticklabels(h["short_title"], fontsize=7)
    ax.set_xlabel("Diffusion Gap (theoretical − observed)")
    ax.set_title("Healthcare Occupations: AI Diffusion Gap\n(gap = unrealized theoretical potential)")
    ax.axvline(x=0, color="black", linewidth=0.5)

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=ADMIN_COLOR, label="Admin-heavy (admin > clinical share)"),
        Patch(facecolor=CLINICAL_COLOR, label="Clinical-heavy (clinical > admin share)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9)

    fig.savefig(FIG_DIR / "fig6_health_diffusion_gap.png")
    plt.close(fig)
    print("  [+] fig6_health_diffusion_gap.png")


def main() -> None:
    print("Generating figures...")
    df = load_mart()
    fig1_top_bottom_exposure(df)
    fig2_theoretical_vs_observed(df)
    fig3_exposure_by_wage_decile(df)
    fig4_exposure_by_job_zone(df)
    fig5_health_admin_vs_observed(df)
    fig6_health_diffusion_gap(df)
    print("Done.")


if __name__ == "__main__":
    main()
