# AI Labor Impact Observatory

[![CI](https://github.com/SHLEW06/aI-labor-impact-observatory/actions/workflows/ci.yml/badge.svg)](https://github.com/SHLEW06/aI-labor-impact-observatory/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Where does AI capability meet actual AI adoption across U.S. occupations — and within healthcare, does adoption concentrate on administrative tasks rather than clinical ones?**

The project joins four datasets — Eloundou et al.'s theoretical LLM exposure scores, the Anthropic Economic Index's observed usage measure, O*NET's task and job-zone data, and BLS OEWS wages/employment — into a dbt/DuckDB warehouse covering 798 U.S. occupations. Within healthcare (SOC major groups 29 and 31, n = 81), we decompose each occupation's tasks into administrative vs. clinical shares and test which explains observed AI usage.

## Key finding

Within healthcare, AI adoption concentrates on administrative work, not clinical judgment. The Pearson correlation between an occupation's administrative task share and its observed AI usage is **+0.76** (traceable in [`reports/descriptives.txt`](reports/descriptives.txt)). Admin-heavy healthcare occupations — medical transcriptionists, medical records specialists — show observed AI usage roughly five times higher than clinical-heavy ones (mean 0.101 vs. 0.021).

In the canonical regression (WLS employment-weighted, HC1 robust SEs, n = 81), a 10-percentage-point increase in admin task share associates with a **5.2-percentage-point** increase in observed AI usage (p = 0.033, R² = 0.42). Neither job zone (β = 0.015, p = 0.45) nor log(median wage) (β = 0.020, p = 0.49) is significant. Under unweighted OLS the same coefficient is larger (6.2pp, p < 0.001, R² = 0.58); the attenuation under WLS is the employment-weighting effect, not the wage control (full 2×2 decomposition in [`reports/regressions.txt`](reports/regressions.txt)). Healthcare as a whole is under-adopting relative to its theoretical potential: mean diffusion gap 0.27 vs. 0.25 for the full economy.

![Healthcare: administrative share vs. observed AI usage](figures/fig5_health_admin_vs_observed.png)

*Within healthcare, observed AI usage tracks administrative task share. Medical Records Specialists and Medical Transcriptionists are the clearest outliers; clinical-heavy occupations cluster near zero.*

The full policy memo is at [`reports/policy_memo.md`](reports/policy_memo.md); an interactive dashboard covering all 798 occupations at [`dashboard/index.html`](dashboard/index.html).

## Data

| Source | Version pinned | Records | License |
|---|---|---|---|
| [O\*NET Task Statements, Ratings, Job Zones, DWA/GWA crosswalks](https://www.onetcenter.org/database.html) | 30.3 (June 2026) | 923 O\*NET-SOC codes | CC-BY |
| [BLS OEWS](https://www.bls.gov/oes/tables.htm) | May 2025, national | 830 SOC-6 wage/employment rows | Public domain |
| [Anthropic Economic Index](https://huggingface.co/datasets/Anthropic/EconomicIndex) | `labor_market_impacts/` (stable dir); `release_2026_03_24` for robustness | 771 O\*NET-SOC job-exposure rows | CC-BY |
| [Eloundou et al. (2024) — "GPTs are GPTs"](https://doi.org/10.1126/science.adj0998) | `occ_level.csv` at `openai/gpts-are-gpts` | 923 O\*NET-SOC codes | Public repo |
| [Felten/Raj/Seamans AIOE](https://doi.org/10.1002/smj.3286) *(robustness only)* | `AIOE_DataAppendix.xlsx` | 774 SOC-6 codes | Public repo |

Canonical join key is the six-digit 2018 SOC code, derived from O\*NET-SOC via the official crosswalk. Suppressed OEWS cells (`*`, `#`, `~`) are flagged with a boolean, never silently dropped or coerced to zero. Data files live in `data_raw/` (gitignored); provenance and SHA-256 hashes in [`data_raw/SOURCES.md`](data_raw/SOURCES.md).

## Method

Task-level administrative and clinical shares come from O\*NET Generalized Work Activity (GWA) codes mapped to task ratings; the rule-based classification is documented and reproducible. Regressions are OLS and WLS (weighted by `tot_emp`) with HC1 robust standard errors. The canonical spec is WLS with `log_wage` added — reported alongside the no-wage WLS and both OLS variants so the wage-control delta is visible. See [`reports/methodology.md`](reports/methodology.md) for every judgment call (crosswalk rules, suppressed cells, importance weighting, admin/clinical classification).

## Reproduce

```bash
git clone https://github.com/SHLEW06/aI-labor-impact-observatory.git
cd aI-labor-impact-observatory
make setup && source .venv/bin/activate
make all
```

`make all` runs the full pipeline: `download → build (dbt) → analyze → figures → dashboard`. Runtime on a laptop: ~2–3 minutes end-to-end after data is downloaded. One manual step: BLS OEWS blocks automated requests, so `national_M2025_dl.xlsx` must be downloaded via browser to `data_raw/oews/`. The pipeline runs without it, but wage and employment columns will be NULL and the WLS regressions will skip.

Unit tests (crosswalk + SOC-code validation, 18 tests) run in CI on every push:

```bash
pytest -q
```

## Repository map

```
data_raw/           Immutable source pulls (gitignored; manifest in SOURCES.md)
warehouse/dbt/      dbt-core: staging → intermediate → mart, with 10 tests
src/                Ingest, SOC crosswalk, task classification
analysis/           01_descriptives · 02_regressions · 03_figures · 04_dashboard
figures/            Six publication PNGs
reports/            policy_memo · methodology · descriptives · regressions · data_dictionary
dashboard/          Self-contained static HTML companion to the memo
docs/               Planning documents (project brief, v2 research design)
tests/              pytest unit tests
```

## Limitations

Exposure is *potential capability*, not realized job loss — Eloundou et al. and the Anthropic Economic Index both state this explicitly; this project does too. Cross-sectional exposure scores do not imply causal employment effects. The observed-usage measure captures Claude usage specifically; occupations that rely on other AI systems will show artificially lower scores. The GWA-based admin/clinical tagger has moderate recall, likely biasing `clinical_share` downward. Findings are associations between task composition and where AI is currently used, not predictions about where jobs will disappear.

## Citations

- Eloundou, T., Manning, S., Mishkin, P., & Rock, D. (2024). GPTs are GPTs: Labor market impact potential of LLMs. *Science*, 384, 1306–1308. [doi:10.1126/science.adj0998](https://doi.org/10.1126/science.adj0998)
- Handa, K., et al. (2025). Which Economic Tasks are Performed with AI? Evidence from Millions of Claude Conversations. *arXiv:2503.04761*. [Anthropic Economic Index dataset](https://huggingface.co/datasets/Anthropic/EconomicIndex).
- Felten, E., Raj, M., & Seamans, R. (2021). Occupational, industry, and geographic exposure to artificial intelligence: A novel dataset and its potential uses. *Strategic Management Journal*, 42(12), 2195–2217.
- O\*NET 30.3. National Center for O\*NET Development. Downloaded June 2026 from [onetcenter.org](https://www.onetcenter.org/database.html).
- BLS OEWS May 2025. U.S. Bureau of Labor Statistics. [bls.gov/oes](https://www.bls.gov/oes/tables.htm).

## License

Analysis code: MIT (see [LICENSE](LICENSE)). Data files retain their original licenses; see [`data_raw/SOURCES.md`](data_raw/SOURCES.md).
