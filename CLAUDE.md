# CLAUDE.md — AI Labor Impact Observatory

## Who is the user

Econ + Human Health double major (Emory), pursuing a Master's in Economics. Currently
interning at the IRC doing grant-compliance data work (Excel automation, pandas/openpyxl,
record matching). Ships real apps (Next.js/TS/React/Firebase/Python). ~10-15 discretionary
hrs/week — time is the binding constraint. Favor the simplest thing that clears the bar.

## Target audience for this project

- **Anthropic Economics & Policy Fellows** (north star — labor-market research is the workstream)
- **Data Analyst / Data Engineer roles** (the pipeline demonstrates dbt/SQL/DuckDB competence)
- **HEOR / economic consulting** (health-econ domain + rigor)

## Quality bar

A labor economist recognizes the framework and doesn't wince at the method. A data engineer
sees clean staging/marts, real data-quality tests, and `make all` reproducibility. The headline
finding is defensible. The limitations section is honest. Exposure is framed as potential,
never realized job loss.

## Research question

> Across U.S. occupations — and the health-sector workforce in particular — how does
> *theoretical* LLM exposure compare to *observed* AI usage, and which tasks are being
> complemented vs. substituted?

Healthcare angle: does AI concentrate on the *administrative* layer (documentation,
prior-auth, scheduling, coding) while *clinical judgment* tasks stay human?

## Non-negotiable framing & integrity rules

1. **Exposure = potential capability, not realized job loss.** Never imply causal employment
   effects from cross-sectional exposure. Say so prominently and repeatedly.
2. **Handle suppressed OEWS cells explicitly** (`*`, `#`, `~`). Flag with `suppressed` bool —
   never silently drop or coerce to zero.
3. **Handle low-response / unrated O*NET tasks explicitly.** Decide a rule, document it.
4. **Use only open, properly-licensed datasets** (O*NET CC-BY, BLS public domain, AEI CC-BY,
   academic exposure files via their repos). No scraping against ToS.
5. **Cite sources properly** in memo and methodology.
6. **Don't over-claim novelty.** The method is well-trodden. My value is clean execution +
   the healthcare diffusion angle.
7. **Never fabricate, mock, or "fill in" data.** If a download fails or a file is misshapen,
   STOP and show the actual error. No synthetic stand-ins.

## Canonical join key

**6-digit 2018 SOC** (e.g., `29-1141`). Derived from O*NET-SOC via the official crosswalk,
preferring it over naive truncation where they differ. The `.0X` collapsing rule and every
unmatched key must be logged.

## Repo conventions

- **Makefile-driven**: `make all` = download -> build -> analyze -> figures. No manual steps.
- **DuckDB** as warehouse; **dbt-core** (dbt-duckdb adapter) for staging/intermediate/marts.
- **data_raw/** is gitignored; tracked via `data_raw/SOURCES.md` (URL + date + sha256).
- **Notebooks** are exploration only — never the source of truth.
- **Small, logical commits** with clear messages.
- **Test the risky things first**: crosswalk + every join get tests. Assert row counts.

## Data sources (pinned versions)

| Source | Pin | Key file(s) |
|--------|-----|-------------|
| O*NET | 30.3 | Task Statements, Task Ratings, Occupation Data, DWA/GWA crosswalks, Job Zones |
| BLS OEWS | May 2025 | National all-data |
| Anthropic Economic Index | TBD (decision pending) | job_exposure.csv, task_penetration.csv |
| Eloundou et al. | gptsRgpts_occ_lvl.csv | beta = E1 + 0.5*E2 |
| AIOE (robustness) | AIOE_DataAppendix.xlsx | Felten/Raj/Seamans |

## Corrections to spec (verified June 2026)

- O*NET 30.3 is current production; pin it even if 30.4 drops mid-build.
- **Job Zones are now 1-4** (not 1-5) as of O*NET 30.2. Set `accepted_values` test accordingly.

## Build milestones

- **M0**: Scaffold, env, dbt, README, CLAUDE.md, Makefile, SOURCES.md
- **M1**: Data acquisition + crosswalk (riskiest piece). GATE: present open decisions.
- **M2**: dbt pipeline (staging -> intermediate -> marts) + admin/clinical tagging
- **M3**: Analysis — 6 figures, 3 regressions, robustness battery
- **M4**: Write-up — policy memo, methodology.md, data dictionary, dashboard

## Open decisions (present at M1 gate)

1. AEI release: `release_2026_03_24` vs `release_2026_06_26`
2. Primary angle: health-sector (recommended) vs alternative
3. Wage measure: mean vs median as primary
4. Admin/clinical tagging: rule-based (GWA/DWA) vs LLM-classification for headline
5. Geographic cut: now vs stretch goal

## Decisions log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-27 | Pin O*NET 30.3 | Current production release; spec §2A |
| 2026-06-27 | Job Zone range 1-4 | O*NET 30.2+ moved from 5-level to 4-level framework |
| 2026-06-27 | DuckDB + dbt-duckdb | Zero-config warehouse; lightest path to real analytics engineering |
| 2026-06-27 | Python 3.12 (not 3.14) | dbt-common/mashumaro incompatible with 3.14; 3.12 is the stable choice |

## Running this project

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
make all
```
