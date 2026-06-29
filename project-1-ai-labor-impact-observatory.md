# Project 1 — AI Labor Impact Observatory

**What this file is.** The complete build spec for my flagship summer project, with verified data sources, the join strategy, the pipeline design, the analysis plan, and a week-by-week breakdown. Drop it into a dedicated Claude project and start each work session against it. Everything here is current as of June 2026 and uses only **open, properly licensed** data.

**Companion doc:** the master plan (`summer-2026-portfolio-plan.md`) explains *why* this project leads and how it serves the Anthropic Economics & Policy Fellow + Data Analyst/Engineer + HEOR/consulting targets. This file is the *how*.

---

## 1. The research question

> **Across U.S. occupations — and the health-sector workforce in particular — how does *theoretical* LLM exposure compare to *observed* AI usage, and which tasks are being complemented vs. substituted?**

The sharpest, most defensible framing borrows Anthropic's own distinction:

- **Theoretical exposure** — what LLMs *could* do, from task-level capability ratings (Eloundou et al.'s β). This is the "blue area" in Anthropic's labor-market work.
- **Observed exposure** — what Claude *actually* does, from the Anthropic Economic Index usage data. The "red area."
- **The diffusion gap** — theoretical minus observed. Where is exposure high but usage low (regulatory friction, verification steps, missing software), and where has adoption already caught up?

**My contribution (the angle that's mine alone):** run this for **healthcare occupations** (SOC major groups 29 Healthcare Practitioners & Technical, and 31 Healthcare Support), and decompose by **task type** — does AI concentrate on the *administrative* layer (documentation, prior-authorization, scheduling, coding — exactly the grant-compliance automation I do at IRC) while *clinical judgment* tasks stay human? Then tie it to a workforce-policy memo (scribes, prior-auth automation, telehealth, scope-of-practice).

**Why this is Anthropic-shaped AND differentiated:** it uses their exact framework, datasets, and citations, and extends in a direction their public reports gesture at but don't fully work out (sector-specific diffusion). A CS applicant won't frame it this way; a health-economics student who *also* ships a clean pipeline will.

---

## 2. Data sources (verified — links, files, licenses)

> All open. O*NET is CC-BY; BLS is public domain (U.S. Government work); the Anthropic Economic Index is CC-BY; the academic exposure datasets are public via their accompanying repos. Pin specific releases for reproducibility.

### A. O*NET 30.3 — occupational tasks (the spine)
- **Page:** `https://www.onetcenter.org/database.html` (current production release is **30.3**; flat text + Excel; CC license).
- **Files I need:**
  - **Task Statements** — columns: `O*NET-SOC Code, Title, Task ID, Task, Task Type (Core/Supplemental), Incumbents Responding, Date, Domain Source`. ~19,000+ rows.
  - **Task Ratings** — Importance and Frequency ratings per task (lets me weight tasks, not just count them).
  - **Occupation Data** — O*NET-SOC code ↔ title.
  - **Detailed/Generalized Work Activities (DWA/GWA) + the Tasks-to-DWA crosswalk** — used to tag tasks as admin- vs. clinical-leaning.
  - **The O\*NET-SOC → 2018 SOC crosswalk** (in the DB or the Crosswalks section) — needed to join to wages/exposure.
- **Direct-download pattern** (confirm the version folder on the page): `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Task Statements.xlsx` (Anthropic's own pipeline used the `db_20_1_excel/Task Statements.xlsx` form — same pattern, just bump the version).
- **Taxonomy note:** 1,016 O*NET-SOC titles, **923 data-level** occupations, aligned to **2018 SOC**.

### B. BLS OEWS — May 2025 wages & employment
- **Page:** `https://www.bls.gov/oes/tables.htm` → grab **"All data (XLSX)"** (national, by detailed SOC). National-only is also at `https://www.bls.gov/oes/current/oes_nat.htm`.
- **Coverage:** ~830 occupations, **2018 SOC**, 2022 NAICS, latest reference period **May 2025** (released May 15, 2026).
- **Fields I need:** `OCC_CODE` (6-digit SOC), `OCC_TITLE`, `TOT_EMP`, `A_MEAN`, `A_MEDIAN`, `H_MEAN`. Watch for suppressed cells (`*`, `#`, `~`) — handle explicitly.
- **Healthcare anchor:** group 29 (Healthcare Practitioners & Technical) had ~9.8M employment in May 2025 — big enough for a real sector analysis.

### C. Anthropic Economic Index — observed usage (the differentiator)
- **Repo:** `https://huggingface.co/datasets/Anthropic/EconomicIndex` (**CC-BY**). Releases: `2025-02-10`, `2025-03-27`, `2025-09-15`, `2026-01-15`, `2026-03-24`, `2026-06-26`. **Pin one** — `release_2026_03_24` ("Learning curves") or `release_2026_06_26` ("Cadences").
- **Key files (recent releases):**
  - `job_exposure.csv` — AI exposure scores for **756 O\*NET occupations** (their occupation-level observed measure).
  - `task_penetration.csv` — AI penetration scores for **~18K O\*NET tasks**.
  - `aei_raw_claude_ai_*.csv` / `aei_raw_1p_api_*.csv` — **long format**: one row per `geography × facet × variable`; variables follow `{prefix}_{suffix}` (`*_count`, `*_pct`; enrichment adds `*_per_capita`, `*_per_capita_index`). Facets include `onet_task`, `request`, `soc`, `collaboration`, and their intersections.
  - `SOC_Structure.csv` — SOC hierarchy. `automation_vs_augmentation*.csv` — interaction types (`directive, feedback loop, task iteration, learning, validation`).
- **Download (robust):** `huggingface_hub.snapshot_download(repo_id="Anthropic/EconomicIndex", repo_type="dataset", allow_patterns="release_2026_03_24/*")`, then browse the folder. Reference implementation that pulls these files: `github.com/nikolascoimbra/anthropic-economic-index-analysis` (`scripts/download_data.py`).
- **Methodology to cite:** Handa et al. (2025), *Which Economic Tasks are Performed with AI?* — arXiv:2503.04761. Clio (privacy pipeline): Tamkin et al. (2024) — arXiv:2412.13678.

### D. Eloundou et al. — theoretical exposure (β)
- **Paper:** *GPTs are GPTs*, Science 384:1306–1308 (2024); arXiv:2303.10130; DOI 10.1126/science.adj0998.
- **File:** `gptsRgpts_occ_lvl.csv` (occupation-level, keyed by **SOC**). Cleanest source: the aggregator repo `github.com/EIG-Research/AI-unemployment` (also bundles the originals), or Eloundou's own accompanying GitHub.
- **Measure:** task labels **E1** (exposed as-is) and **E2** (exposed with software/tools). Occupation scores: share E1; **β = E1 + 0.5·E2** (the standard headline measure); and E1 + E2 (full software complement). Already SOC-aggregated.

### E. Optional robustness / extension
- **Felten/Raj/Seamans AIOE** — `AIOE_DataAppendix.xlsx` (same EIG repo; SMJ 2021). Alternative exposure measure → robustness.
- **ACS/Census (IPUMS)** — demographics by occupation if I want an equity cut.
- **BLS Employment Projections** — forward-looking growth by occupation.

---

## 3. The join strategy (the genuinely hard part — get this right first)

The granularity mismatch is the thing that trips people up, so handle it deliberately:

- **O\*NET-SOC** codes are 8-digit + suffix (e.g., `29-1141.00` Registered Nurses, `15-1252.00` Software Developers). One 6-digit SOC can split into several O\*NET-SOC variants (`.00/.01/.02`).
- **OEWS** and **Eloundou** use **6-digit SOC** (`29-1141`).
- **AEI** `job_exposure.csv` / `task_penetration.csv` are at **O\*NET occupation/task** level.

**Canonical key = 6-digit SOC.** Pipeline:
1. From O\*NET-SOC, derive 6-digit SOC = first 7 chars before the dot (`29-1141.00` → `29-1141`). Prefer the official **O\*NET-SOC → 2018 SOC crosswalk** over naive truncation where they differ.
2. **Aggregate O\*NET tasks to SOC**, weighting by **Importance** (and optionally employment across `.0X` variants). This yields a per-SOC task set + my own theoretical-exposure roll-up.
3. Join **Eloundou β** on SOC.
4. Join **OEWS** (wages/employment) on SOC.
5. Join **AEI observed** measures (collapse AEI's O\*NET occupations to SOC the same way).
6. Result: one **occupation-level (SOC) mart** carrying theoretical exposure, observed exposure, wages, employment, education/job-zone, sector flags, and the diffusion gap.

Document every judgment call (suppressed cells, `.0X` collapsing rule, tasks with no rating) in `methodology.md` — "judgment calls at every step" is literally how Anthropic describes their own version, so showing mine is a feature.

---

## 4. Methodology

**Core measures (occupation level):**
- `theoretical_exposure` = importance-weighted mean of Eloundou β over the occupation's tasks (and a simple unweighted version for comparison).
- `observed_exposure` = AEI `job_exposure` (their usage-based measure).
- `diffusion_gap` = `theoretical_exposure` − rescaled `observed_exposure` (normalize to a common scale; state the transform).
- `admin_share` / `clinical_share` (health subset) = importance-weighted share of an occupation's tasks tagged admin- vs. clinical-leaning, via GWA/DWA mapping (e.g., *Documenting/Recording Information*, *Interacting With Computers*, *Performing Administrative Activities* → admin; *Assisting and Caring for Others*, *Making Decisions and Solving Problems* → clinical). Validate the rule on a hand-labeled sample of ~50 tasks; optional LLM-classification robustness pass (reuses Project 2 skills).

**Descriptive analysis:**
- Top/bottom exposed occupations (overall and within healthcare).
- Theoretical vs. observed scatter, with the 45° line — which health occupations sit far below it (latent, not-yet-diffused exposure)?
- Exposure by wage decile and by O\*NET Job Zone (education proxy).
- Within healthcare: `admin_share` vs `observed_exposure` — is usage concentrated on the admin layer?

**Regressions (statsmodels / linearmodels), employment-weighted with robust SEs:**
1. `observed_exposure ~ log(wage) + job_zone + health_dummy + admin_share + controls`
2. `diffusion_gap ~ health_dummy + log(wage) + job_zone + regulatory_proxy` (proxy: licensure intensity / share of "validation"-type interactions).
3. Health-only: `observed_exposure ~ admin_share + log(wage) + job_zone`.

**Robustness checks (this is what makes it credible, not a dashboard):**
- Swap exposure measure: Eloundou β vs E1-only vs E1+E2 vs **AIOE**.
- Swap wage: mean vs median; weight by employment vs unweighted.
- Drop suppressed/low-`Incumbents Responding` cells.
- Pin a different AEI release; check stability.
- Alternative admin/clinical tagging (rule vs LLM).

**Framing discipline:** exposure is *potential*, not realized job loss. Eloundou and Anthropic both say so — I say so prominently and never imply causal employment effects from cross-sectional exposure.

---

## 5. Repo structure

```
ai-labor-impact-observatory/
  README.md                  # leads with the question + headline finding
  Makefile                   # `make all` = download -> build -> analyze -> figures
  pyproject.toml             # or requirements.txt
  data_raw/                  # immutable pulls; never edited (gitignored, with a manifest)
    onet/  oews/  aei/  exposure/
    SOURCES.md               # exact URLs + release dates + license + sha256
  warehouse/
    aei.duckdb               # the analytical DB
    dbt/                     # dbt-core (duckdb adapter)
      models/
        staging/             # stg_onet_tasks, stg_onet_ratings, stg_oews, stg_eloundou, stg_aei_*
        intermediate/        # int_tasks_by_soc, int_exposure_by_soc
        marts/               # mart_occupation_exposure  <- the deliverable table
      tests/                 # not_null, unique, accepted_values, relationships, freshness
      dbt_project.yml
  src/
    ingest.py                # download + checksum + load raw -> duckdb
    crosswalk.py             # O*NET-SOC -> SOC, .0X collapsing
    classify_tasks.py        # admin/clinical tagging (rule + optional LLM)
  analysis/
    01_descriptives.py
    02_regressions.py
    03_figures.py
  figures/
  reports/
    methodology.md
    policy_memo.md           # the 5-8 page research memo
    data_dictionary.md
  dashboard/                 # static (Observable/Plotly export) or Streamlit
  notebooks/                 # exploration only — NOT the source of truth
```

---

## 6. Environment & setup

```bash
# Python env
python -m venv .venv && source .venv/bin/activate
pip install duckdb dbt-duckdb pandas numpy statsmodels linearmodels \
            matplotlib plotly huggingface_hub openpyxl pyarrow pytest

# Pull AEI (pin the release)
python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(repo_id="Anthropic/EconomicIndex", repo_type="dataset",
                  allow_patterns="release_2026_03_24/*", local_dir="data_raw/aei")
PY

# O*NET, OEWS, Eloundou: download into data_raw/ and record URL + date + sha256 in SOURCES.md
```

**dbt sketch (DuckDB), `models/intermediate/int_tasks_by_soc.sql`:**
```sql
-- Collapse O*NET tasks to 6-digit SOC, importance-weighted
with tasks as (
  select * from {{ ref('stg_onet_tasks') }}
), ratings as (
  select * from {{ ref('stg_onet_ratings') }} where scale_id = 'IM'  -- Importance
)
select
  left(t.onet_soc_code, 7)                         as soc_code,   -- '29-1141.00' -> '29-1141'
  count(*)                                         as n_tasks,
  avg(r.data_value)                                as mean_importance
from tasks t
left join ratings r using (task_id)
group by 1
```

**A test, `tests/assert_soc_unique.sql`** (returns rows = failures):
```sql
select soc_code, count(*) n from {{ ref('mart_occupation_exposure') }}
group by 1 having count(*) > 1
```

---

## 7. The mart table (`data_dictionary.md` preview)

| column | type | source | notes |
|---|---|---|---|
| `soc_code` | text | derived | 6-digit 2018 SOC (PK) |
| `soc_title` | text | OEWS | |
| `major_group` | text | SOC_Structure | e.g. `29-0000` |
| `is_health` | bool | derived | major group 29 or 31 |
| `n_tasks` | int | O*NET | tasks rolled to SOC |
| `mean_importance` | float | O*NET | weighting input |
| `theoretical_exposure` | float | Eloundou | β = E1 + 0.5·E2 |
| `observed_exposure` | float | AEI | `job_exposure` |
| `diffusion_gap` | float | derived | theoretical − observed (rescaled) |
| `admin_share` | float | O*NET DWA/GWA | health subset |
| `clinical_share` | float | O*NET DWA/GWA | health subset |
| `tot_emp` | int | OEWS | employment |
| `a_mean` / `a_median` | float | OEWS | annual wage |
| `job_zone` | int | O*NET | education/training proxy |
| `suppressed` | bool | OEWS | wage cell suppressed |

---

## 8. Figures & memo

**Figures (`figures/`):**
1. Top 15 / bottom 15 exposed occupations (overall).
2. Theoretical vs. observed scatter, 45° line, healthcare highlighted.
3. Exposure by wage decile.
4. Exposure by Job Zone.
5. Healthcare: `admin_share` vs `observed_exposure`.
6. Diffusion gap ranked within healthcare.

**Policy memo (`reports/policy_memo.md`, 5–8 pp), section order:**
1. **Question & motivation** (1 para — healthcare workforce, why diffusion ≠ capability).
2. **Data & method** (sources, the SOC join, the three exposure measures, limitations up front).
3. **Findings** — overall exposure landscape; the theoretical-vs-observed gap; the healthcare admin-vs-clinical result; wage/education gradients.
4. **Robustness** (one tight para + an appendix table).
5. **Policy implications** — medical scribes, prior-auth automation, telehealth, scope-of-practice, what the diffusion gap implies for *timing*.
6. **Limitations & what I'd do next.**

Reads like research: real methods section, honest caveats, minimal formatting. Not a listicle, not a blog post.

---

## 9. Four-week plan (this project is Weeks 1–4 of the summer)

| Week | Goal | Concrete output |
|---|---|---|
| **1** | Data + skeleton | Repo scaffolded; all five sources downloaded with `SOURCES.md` checksums; DuckDB loads raw; **crosswalk working and unit-tested** (the riskiest piece, done first); decide health-angle vs. an alternative |
| **2** | Pipeline | `stg_*` → `int_*` → `mart_occupation_exposure` built in dbt with passing data-quality tests; admin/clinical tagging + 50-task hand-validation |
| **3** | Analysis | Descriptives + all six figures; three regressions; full robustness battery |
| **4** | Write-up | `policy_memo.md` (5–8 pp); `methodology.md`; `data_dictionary.md`; README that opens with the finding; static dashboard; `make all` reproduces end-to-end from clean |

**Hard rule:** by end of Week 4 this is a finished, reproducible, written-up repo. It's the non-negotiable spine of the summer; Projects 2–4 come after.

---

## 10. Quality bar & project-specific failure modes

**"Done well" =** a labor economist recognizes the framework and doesn't wince at the method; a data engineer sees clean staging/marts + tests + `make all` reproducibility; the headline finding is defensible; limitations are honest.

**Avoid:**
- Treating exposure as realized job loss (it's *potential* — say so repeatedly).
- The crosswalk silently dropping occupations — assert row counts at each join; log unmatched SOCs.
- Letting a dashboard stand in for an argument — the memo carries the claim.
- A 40-page sprawl — the memo is tight.
- Over-claiming novelty — the *method* is well-trodden (Eloundou; Felten/Raj/Seamans; Webb; Acemoglu & Restrepo; Anthropic's own reports; Massenkoff & McCrory 2026). My value is clean execution + the healthcare diffusion angle.
- Ignoring suppressed OEWS cells or low-response O\*NET tasks — handle explicitly.

---

## 11. Stretch goals (only after the core ships)
- **Geographic cut** using AEI state-level data (Connecticut + Georgia, my two bases).
- **LLM task-classification** robustness pass for admin/clinical (bridges into Project 2's eval work).
- A small interactive (the dashboard becomes a portfolio centerpiece).

---

## 12. Start here (first session checklist)
1. `git init` the repo with the structure in §5; commit a stub README stating the §1 question.
2. Write `src/ingest.py` + `SOURCES.md`; pull O\*NET 30.3 Task Statements/Ratings, OEWS May 2025 all-data, AEI `release_2026_03_24` (`job_exposure.csv`, `task_penetration.csv`), and `gptsRgpts_occ_lvl.csv`.
3. Build and **unit-test the SOC crosswalk first** — nothing else works until this is right.
4. Stand up the dbt project; get `stg_*` models loading from DuckDB.
5. Confirm with me in the project chat: **lock the health-sector angle vs. an alternative, and pick the AEI release to pin.**

**Open decisions to settle in-chat:** which AEI release to pin; mean vs. median wage as primary; rule-based vs. LLM admin/clinical tagging for the headline (keep the other as robustness); whether to add the geographic cut now or as a stretch.
