# Methodology

## Research question

Across U.S. occupations — and the health-sector workforce in particular — how does *theoretical* LLM exposure compare to *observed* AI usage, and which tasks are being complemented vs. substituted?

## Data sources

| Source | Version / Release | Coverage | License |
|--------|-------------------|----------|---------|
| O\*NET | 30.3 (Excel) | 1,016 O\*NET-SOC codes, ~19K task statements, task ratings, DWA/GWA hierarchy | CC-BY 4.0 |
| BLS OEWS | May 2025 | ~830 occupations, wages, employment | Public domain |
| Anthropic Economic Index (AEI) | `labor_market_impacts/` | 756 occupations (job exposure), ~18K tasks (task penetration) | CC-BY 4.0 |
| Eloundou et al. (2023) | `gpts-are-gpts` repo | 923 O\*NET-SOC codes, human + GPT-4 exposure ratings | Public |

All data is downloaded via `make download` (src/ingest.py), except BLS OEWS which requires manual browser download due to BLS blocking automated requests (HTTP 403). SHA-256 checksums are recorded in `data_raw/SOURCES.md`.

## Canonical join key

The **6-digit 2018 SOC code** (e.g., `29-1141`) is the canonical join key across all datasets. O\*NET uses 8-character O\*NET-SOC codes (e.g., `29-1141.00`) which map to 2018 SOC via the official O\*NET-SOC to SOC crosswalk. The `.0X` suffix distinguishes sub-specialties within the same SOC; we aggregate to SOC level by averaging exposure measures and summing task counts across variants.

Validation: all 1,016 O\*NET-SOC codes in the crosswalk map correctly to 867 unique 6-digit SOC codes. Naive truncation (dropping the `.XX` suffix) produces identical mappings to the official crosswalk — zero mismatches across 1,016 codes.

## Exposure measures

### Theoretical exposure (Eloundou beta)

From Eloundou et al. (2023), "GPTs are GPTs." The beta measure (`dv_rating_beta`) represents the share of an occupation's tasks that are exposed to LLMs with access to complementary software tools. Computed as E1 + 0.5 * E2, where E1 is direct LLM exposure and E2 is exposure with tool augmentation. Scale: [0, 1]. Higher values indicate greater theoretical capability overlap.

When multiple O\*NET-SOC variants map to the same SOC, we average beta across variants. Alternative measures (E1-only, E1+E2, human-only beta) are preserved for robustness checks.

### Observed exposure (AEI)

From the Anthropic Economic Index (2026). The `job_exposure` score measures the share of an occupation's tasks where Claude is actually used, weighted by task importance. Based on observed Claude usage patterns, not capability assessments. Scale: [0, 1]. Available for 756 of 798 occupations.

### Diffusion gap

Defined as `theoretical_exposure - observed_exposure`. Positive values indicate unrealized theoretical potential — occupations where LLM capability exists but adoption has not yet occurred. This is a descriptive measure of the gap between *what AI could do* and *what it currently does*, not a prediction of future adoption.

## Health-sector definition

Healthcare occupations are defined as SOC major groups **29** (Healthcare Practitioners and Technical Occupations) and **31** (Healthcare Support Occupations). This yields 88 occupations in the mart.

## Admin/clinical task classification

### Method

Tasks are classified as administrative or clinical using a rule-based mapping through the O\*NET GWA (Generalized Work Activity) hierarchy:

1. Each O\*NET task is linked to one or more DWAs (Detailed Work Activities) via the Tasks-to-DWAs crosswalk.
2. Each DWA maps to an IWA (Intermediate Work Activity), which maps to a GWA.
3. Tasks are tagged based on which GWAs they connect to:

**Admin GWAs:**
- Documenting/Recording Information (4.A.3.b.6)
- Working with Computers (4.A.3.b.1)
- Performing Administrative Activities (4.A.4.c.1)

**Clinical GWAs:**
- Assisting and Caring for Others (4.A.4.a.5)
- Making Decisions and Solving Problems (4.A.2.b.1)

A task is tagged `admin` if any of its GWA pathways include an admin GWA; `clinical` if any include a clinical GWA; `both` if both; `other` if neither.

### Aggregation to occupation level

`admin_share` and `clinical_share` are computed per SOC as importance-weighted proportions:

```
admin_share = sum(importance * is_admin) / sum(importance)
```

When O\*NET Importance ratings (IM scale) are available for a task, the rating is used as the weight. For the 7 occupations where no tasks have ratings, we fall back to unweighted count-based proportions.

### Validation

A 41-task hand-validation (stratified across admin, clinical, both, and other categories) yielded:
- **Overall accuracy: ~90%**
- **Admin precision: 100%** (13/13)
- **Clinical precision: 100%** (13/13)
- **Clinical recall: moderate** — 4 false negatives where clinical tasks (diagnosis, assessment, monitoring) map to GWAs outside our clinical set (e.g., "Analyzing Data," "Monitoring Processes")

The classifier has **high precision but moderate recall for clinical tasks**. This means `admin_share` is reliable, while `clinical_share` is a conservative lower bound. Full validation results are in `reports/task_validation.md`.

## Education proxy

O\*NET Job Zone (values 2-5 in O\*NET 30.3) serves as a coarse education proxy:
- Zone 2: High school diploma + some training
- Zone 3: Vocational school or associate's degree
- Zone 4: Bachelor's degree
- Zone 5: Graduate or professional degree

When multiple O\*NET-SOC variants map to the same SOC, we take the modal Job Zone.

## Wage and employment data

BLS Occupational Employment and Wage Statistics (OEWS), May 2025 release. Fields used: `TOT_EMP` (total employment), `A_MEAN` (mean annual wage), `A_MEDIAN` (median annual wage), `H_MEAN` (mean hourly wage). Suppressed cells (marked with `*`, `#`, or `~` in the source) are handled with a boolean `suppressed` flag — never silently coerced to zero or dropped.

## Regressions

Three OLS regressions with HC1 (heteroskedasticity-consistent) robust standard errors. Employment-weighted (WLS) when OEWS data is available, unweighted otherwise.

1. **Full sample:** `observed_exposure ~ log(median_wage) + job_zone + is_health + admin_share`
2. **Full sample:** `diffusion_gap ~ is_health + log(median_wage) + job_zone`
3. **Health-only:** `observed_exposure ~ admin_share + log(median_wage) + job_zone`

These are cross-sectional associations, not causal estimates. We do not claim that admin task composition *causes* higher AI adoption; the relationship may reflect selection effects, task characteristics that facilitate automation, or institutional factors.

## Framing discipline

Throughout this analysis, "exposure" refers to theoretical capability overlap or observed usage patterns — **not** realized or predicted job loss. This follows the explicit framing of both Eloundou et al. (2023) and the Anthropic Economic Index (2026). The diffusion gap measures where potential exceeds current usage; it does not imply that affected occupations will experience employment declines.

## Pipeline and reproducibility

The full pipeline is orchestrated via `make all`:
1. `make download` — fetches raw data via src/ingest.py (BLS requires manual download)
2. `make build` — runs dbt (staging -> intermediate -> marts) with 10 data quality tests
3. `make analyze` — descriptive statistics and regressions
4. `make figures` — 6 publication figures

All transformations use DuckDB as the analytical warehouse with dbt-core + dbt-duckdb adapter. Source code, not notebooks, is the source of truth.

## Limitations

1. **Cross-sectional design.** All relationships are correlational. We cannot identify causal effects of task composition on AI adoption.
2. **Theoretical exposure is a capability measure, not a prediction.** Eloundou beta reflects what LLMs *could* do with software tools, not what they will do given institutional, regulatory, and workflow constraints.
3. **AEI measures Claude usage specifically.** The observed measure reflects usage of one AI system (Claude), not all AI tools. Occupations using other AI systems may show lower AEI scores despite real adoption.
4. **Clinical recall gap.** Our rule-based classifier misses some clinical tasks whose GWA pathways route through non-clinical activities like "Analyzing Data" or "Monitoring Processes." The clinical_share is a lower bound.
5. **No geographic or demographic variation.** All measures are national-level. Local labor markets, demographics, and institutional factors are not captured.
6. **Suppressed OEWS cells.** Some occupations have suppressed wage/employment data, handled with explicit flags rather than imputation.
7. **O\*NET task granularity.** Task statements vary in specificity across occupations. Some occupations have >100 tasks, others <10, affecting the precision of share estimates.
