"""
04_dashboard.py — Generate a self-contained static dashboard from the mart.

Writes dashboard/index.html: an interactive companion to the policy memo.
Two plotly scatters (all-occupation and health-only) plus a searchable
table of every occupation. No build step, no server — one HTML file.
"""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import plotly.io as pio

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "warehouse" / "aei.duckdb"
OUT = ROOT / "dashboard" / "index.html"


def load() -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute(
        """
        SELECT soc_code, soc_title, major_group, is_health,
               theoretical_exposure, observed_exposure, diffusion_gap,
               admin_share, clinical_share, job_zone,
               tot_emp, a_median
        FROM mart_occupation_exposure
        """
    ).fetchdf()
    con.close()
    return df


def fig_all_occupations(df: pd.DataFrame) -> str:
    sub = df.dropna(subset=["theoretical_exposure", "observed_exposure"]).copy()
    sub["sector"] = sub["is_health"].map({True: "Healthcare", False: "Other"})
    fig = px.scatter(
        sub,
        x="theoretical_exposure",
        y="observed_exposure",
        color="sector",
        hover_data={"soc_code": True, "soc_title": True, "admin_share": ":.2f"},
        color_discrete_map={"Healthcare": "#c0392b", "Other": "#2c3e50"},
        opacity=0.7,
        labels={
            "theoretical_exposure": "Theoretical exposure (Eloundou β)",
            "observed_exposure": "Observed AI usage (Anthropic Economic Index)",
        },
        title="Theoretical vs. observed AI exposure — 756 U.S. occupations",
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=1, y1=1, line=dict(dash="dot", color="#888"))
    fig.update_layout(height=520, template="simple_white", legend_title_text="")
    return pio.to_html(fig, include_plotlyjs="cdn", full_html=False, div_id="fig-all")


def fig_health(df: pd.DataFrame) -> str:
    h = df[df["is_health"]].dropna(subset=["admin_share", "observed_exposure"]).copy()
    fig = px.scatter(
        h,
        x="admin_share",
        y="observed_exposure",
        size=h["tot_emp"].fillna(1000).clip(lower=100),
        hover_data={"soc_code": True, "soc_title": True, "clinical_share": ":.2f"},
        labels={
            "admin_share": "Administrative task share (0–1)",
            "observed_exposure": "Observed AI usage",
        },
        title="Healthcare occupations (n = 81): admin share vs. observed AI usage",
    )
    fig.update_traces(marker=dict(color="#c0392b", line=dict(color="#7f2418", width=0.5)))
    fig.update_layout(height=520, template="simple_white")
    return pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id="fig-health")


def table_html(df: pd.DataFrame) -> str:
    t = df.copy()
    t = t.sort_values("observed_exposure", ascending=False, na_position="last")
    t = t.rename(columns={
        "soc_code": "SOC",
        "soc_title": "Occupation",
        "theoretical_exposure": "Theoretical β",
        "observed_exposure": "Observed",
        "diffusion_gap": "Gap",
        "admin_share": "Admin",
        "clinical_share": "Clinical",
        "job_zone": "Zone",
        "tot_emp": "Employment",
    })
    cols = ["SOC", "Occupation", "Theoretical β", "Observed", "Gap",
            "Admin", "Clinical", "Zone", "Employment"]
    return t[cols].to_html(
        index=False,
        classes="occtable",
        float_format=lambda x: f"{x:.3f}" if pd.notna(x) else "",
        na_rep="",
        border=0,
    )


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>AI Labor Impact Observatory — Dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ font: 15px/1.5 system-ui, -apple-system, sans-serif;
         max-width: 1100px; margin: 2rem auto; padding: 0 1rem; color: #222; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 0.2rem; }}
  h2 {{ font-size: 1.15rem; margin-top: 2.5rem; }}
  .lede {{ color: #555; margin-top: 0; }}
  .note {{ background: #f6f8fa; border-left: 3px solid #888; padding: 0.6rem 0.9rem;
          font-size: 0.9rem; margin: 1rem 0; }}
  input.filter {{ padding: 0.4rem 0.6rem; width: 300px; margin-bottom: 0.5rem;
                 font-size: 0.95rem; }}
  table.occtable {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  table.occtable th, table.occtable td {{ padding: 4px 8px; border-bottom: 1px solid #eee;
                                          text-align: right; }}
  table.occtable th:nth-child(1), table.occtable th:nth-child(2),
  table.occtable td:nth-child(1), table.occtable td:nth-child(2) {{ text-align: left; }}
  table.occtable thead th {{ position: sticky; top: 0; background: #fff;
                              border-bottom: 2px solid #333; }}
  .tablewrap {{ max-height: 520px; overflow-y: auto; border: 1px solid #ddd; }}
  footer {{ margin-top: 3rem; color: #777; font-size: 0.85rem; }}
</style></head><body>
<h1>AI Labor Impact Observatory</h1>
<p class="lede">Theoretical LLM exposure vs. observed AI usage across 798 U.S. occupations,
with a healthcare admin-vs-clinical decomposition.</p>
<p class="note"><strong>Interpretation.</strong> Exposure is <em>potential capability</em>,
not realized job loss. Cross-sectional exposure scores do not imply causal employment effects.
See <a href="../reports/policy_memo.md">policy_memo.md</a> for the full write-up and
<a href="../reports/methodology.md">methodology.md</a> for methods.</p>
<h2>Full economy</h2>
{fig1}
<h2>Healthcare only</h2>
{fig2}
<h2>All 798 occupations</h2>
<input class="filter" type="text" id="q" placeholder="Filter by SOC code or occupation…"
       oninput="filterTable()">
<div class="tablewrap">{table}</div>
<footer>Data: O*NET 30.3, BLS OEWS May 2025, Anthropic Economic Index,
Eloundou et al. (2024). Regenerate: <code>make dashboard</code>.</footer>
<script>
function filterTable() {{
  const q = document.getElementById('q').value.toLowerCase();
  document.querySelectorAll('table.occtable tbody tr').forEach(row => {{
    const soc = row.cells[0]?.textContent.toLowerCase() || '';
    const occ = row.cells[1]?.textContent.toLowerCase() || '';
    row.style.display = (soc.includes(q) || occ.includes(q)) ? '' : 'none';
  }});
}}
</script>
</body></html>
"""


def main() -> None:
    df = load()
    f1 = fig_all_occupations(df)
    f2 = fig_health(df)
    tbl = table_html(df)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(PAGE.format(fig1=f1, fig2=f2, table=tbl))
    kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(ROOT)}  ({kb:.0f} KB, {len(df)} occupations)")


if __name__ == "__main__":
    main()
