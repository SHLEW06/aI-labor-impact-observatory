# Data Dictionary: `mart_occupation_exposure`

One row per 6-digit 2018 SOC code. The deliverable analytical table combining theoretical AI exposure, observed AI usage, occupation characteristics, and task-level decomposition.

**Row count:** 798 occupations
**Primary key:** `soc_code`

## Columns

| Column | Type | Nullable | Source | Description |
|--------|------|----------|--------|-------------|
| `soc_code` | VARCHAR | No | O\*NET crosswalk | 6-digit 2018 SOC code (e.g., `29-1141`). Primary key. |
| `soc_title` | VARCHAR | No | O\*NET crosswalk | Occupation title (e.g., "Registered Nurses"). |
| `major_group` | VARCHAR | No | Derived | SOC major group, formatted as `XX-0000` (e.g., `29-0000`). |
| `is_health` | BOOLEAN | No | Derived | True for SOC major groups 29 (Healthcare Practitioners) and 31 (Healthcare Support). |
| `n_tasks` | BIGINT | Yes | O\*NET Task Statements | Count of distinct O\*NET task statements for this SOC (aggregated across O\*NET-SOC variants). |
| `n_rated_tasks` | BIGINT | Yes | O\*NET Task Ratings | Count of tasks with Importance (IM scale) ratings. |
| `mean_importance` | DOUBLE | Yes | O\*NET Task Ratings | Mean Importance rating across all rated tasks. IM scale: 1 (not important) to 5 (extremely important). |
| `theoretical_exposure` | DOUBLE | Yes | Eloundou et al. (2023) | Eloundou beta = E1 + 0.5\*E2, averaged across O\*NET-SOC variants. Scale: [0, 1]. |
| `observed_exposure` | DOUBLE | Yes | AEI `job_exposure.csv` | Anthropic Economic Index AI usage score. Available for 756 of 798 occupations. Scale: [0, 1]. |
| `diffusion_gap` | DOUBLE | Yes | Derived | `theoretical_exposure - observed_exposure`. Positive = unrealized theoretical potential. NULL when either input is NULL. |
| `admin_share` | DOUBLE | Yes | O\*NET GWA/DWA hierarchy | Importance-weighted share of tasks tagged as administrative via GWA mapping. See methodology.md for GWA definitions. |
| `clinical_share` | DOUBLE | Yes | O\*NET GWA/DWA hierarchy | Importance-weighted share of tasks tagged as clinical via GWA mapping. Conservative lower bound (see validation). |
| `tot_emp` | INTEGER | Yes | BLS OEWS May 2025 | Total employment. NULL until OEWS data is loaded. |
| `a_mean` | DOUBLE | Yes | BLS OEWS May 2025 | Mean annual wage ($). NULL if suppressed or OEWS not loaded. |
| `a_median` | DOUBLE | Yes | BLS OEWS May 2025 | Median annual wage ($). NULL if suppressed or OEWS not loaded. |
| `h_mean` | DOUBLE | Yes | BLS OEWS May 2025 | Mean hourly wage ($). NULL if suppressed or OEWS not loaded. |
| `job_zone` | BIGINT | Yes | O\*NET Job Zones | O\*NET Job Zone (education proxy). Values: {2, 3, 4, 5}. Mode across O\*NET-SOC variants. |
| `suppressed` | BOOLEAN | No | BLS OEWS / Derived | True if any OEWS wage or employment cell is suppressed (`*`, `#`, `~`). Defaults to false when OEWS is absent. |
| `theoretical_e1` | DOUBLE | Yes | Eloundou et al. (2023) | E1-only exposure (direct LLM, no tools). Robustness alternative. |
| `theoretical_e1_e2` | DOUBLE | Yes | Eloundou et al. (2023) | E1 + E2 exposure (full LLM + tools). Robustness alternative. |
| `theoretical_human_beta` | DOUBLE | Yes | Eloundou et al. (2023) | Human-annotator-only beta (no GPT-4 ratings). Robustness alternative. |
| `n_onet_variants` | BIGINT | Yes | O\*NET crosswalk | Number of O\*NET-SOC codes that map to this SOC. Higher values indicate more sub-specialties. |
| `n_admin_tasks` | BIGINT | Yes | O\*NET GWA/DWA | Count of tasks classified as admin (including "both"). |
| `n_clinical_tasks` | BIGINT | Yes | O\*NET GWA/DWA | Count of tasks classified as clinical (including "both"). |
| `n_both_tasks` | BIGINT | Yes | O\*NET GWA/DWA | Count of tasks classified as both admin and clinical. |
| `n_other_tasks` | BIGINT | Yes | O\*NET GWA/DWA | Count of tasks classified as neither admin nor clinical. |

## Coverage notes

- **theoretical_exposure**: 798/798 (100%) — all occupations in Eloundou dataset.
- **observed_exposure**: 756/798 (94.7%) — AEI covers 756 occupations. 42 occupations have NULL.
- **diffusion_gap**: 756/798 — NULL when observed_exposure is NULL.
- **Wage/employment fields**: 0/798 until BLS OEWS is manually downloaded and loaded. The pipeline handles this gracefully.
- **admin_share / clinical_share**: 798/798 (100%) — all occupations have task classifications. 7 occupations use count-based (unweighted) shares due to missing Importance ratings.

## Key relationships

- `admin_share + clinical_share` does **not** sum to 1.0. Tasks can be "both" or "other." The two shares are independent proportions.
- `diffusion_gap` is a simple arithmetic difference. Both inputs are on [0, 1] scales, so direct subtraction is meaningful without rescaling.
- `is_health = true` identifies 88 occupations across SOC groups 29 and 31.
