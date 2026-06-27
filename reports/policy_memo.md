# AI Exposure and the Healthcare Workforce: Where Capability Meets Adoption

**Research Memo — AI Labor Impact Observatory**

---

## 1. Question and motivation

Large language models can now perform meaningful shares of the tasks that define white-collar occupations. But capability is not adoption. The gap between what AI *could* do and what it *currently does* varies enormously across occupations — and understanding that gap matters for workforce planning, training investment, and regulatory design.

This memo examines the diffusion gap across 798 U.S. occupations, with a focus on healthcare (SOC groups 29 and 31, 88 occupations). Within healthcare, we decompose by task type: are AI tools concentrating on the *administrative* layer — documentation, coding, prior authorization, scheduling — while *clinical judgment* tasks remain largely untouched? The answer has direct implications for how health systems invest in AI, how regulators scope oversight, and which workers face near-term disruption versus augmentation.

We combine three open datasets: Eloundou et al.'s (2023) task-level capability ratings (what LLMs *could* do), the Anthropic Economic Index's (2026) observed usage data (what Claude *actually* does), and O\*NET's occupational task structure (which tasks are administrative versus clinical). The result is a reproducible, occupation-level dataset linking theoretical exposure, observed adoption, and task composition.

---

## 2. Data and method

### Data sources

**Theoretical exposure.** Eloundou et al. (2023) rate each O\*NET task on whether LLMs — with and without complementary software tools — could reduce the time needed to complete it by at least 50%. We use their beta measure (beta = E1 + 0.5 * E2), which weights full exposure at 1 and partial exposure at 0.5. Available for all 798 SOC-level occupations.

**Observed exposure.** The Anthropic Economic Index (AEI, 2026) measures the share of an occupation's tasks where Claude is actually used, based on observed interaction patterns. Available for 756 of 798 occupations. This captures *realized* usage of one major AI system, not theoretical capability.

**Task structure.** O\*NET 30.3 provides ~19,000 task statements linked to occupations, with Importance ratings (1-5 scale) and a work-activity hierarchy (DWA -> IWA -> GWA) that allows systematic classification.

**Wages and employment.** BLS Occupational Employment and Wage Statistics (OEWS), May 2025.

### Join strategy

All datasets are linked at the 6-digit 2018 SOC code level. O\*NET-SOC codes (8-character) map to SOC via the official crosswalk; exposure measures are averaged across sub-specialties within each SOC.

### Admin/clinical classification

We classify healthcare tasks as administrative or clinical using a rule-based mapping through the O\*NET Generalized Work Activity (GWA) hierarchy. Three GWAs define the administrative category: *Documenting/Recording Information*, *Working with Computers*, and *Performing Administrative Activities*. Two define the clinical category: *Assisting and Caring for Others* and *Making Decisions and Solving Problems*. Each occupation's admin and clinical shares are computed as importance-weighted proportions of their total task portfolio.

A 41-task hand-validation yielded 100% precision for both categories but moderate recall for clinical (4 false negatives where diagnostic/assessment tasks route through non-clinical GWAs). The clinical share is accordingly a conservative lower bound.

### Limitations stated upfront

All findings are cross-sectional associations. We observe correlation between task composition and AI usage, not causation. The AEI measures Claude usage specifically; occupations relying on other AI systems may show lower scores. The GWA-based clinical tagger has moderate recall, biasing clinical_share downward. These limitations constrain interpretation but do not invalidate the directional findings.

---

## 3. Findings

### 3.1 The diffusion gap is large and widespread

Across 756 occupations with both measures, mean theoretical exposure (0.326) exceeds mean observed exposure (0.077) by a factor of four. The average diffusion gap is 0.249 — meaning that, on average, less than a quarter of theoretically exposed task capacity has translated into observed AI usage.

The correlation between theoretical and observed exposure is 0.64 — meaningful but far from perfect. Occupations with high theoretical scores do tend to have higher observed usage, but the relationship is noisy. Many high-capability occupations show near-zero actual usage.

### 3.2 Healthcare sits below the 45-degree line

Healthcare occupations have theoretical exposure (mean 0.316) roughly in line with the economy-wide average, but observed exposure (mean 0.043) is 45% below the economy-wide average (0.077). The healthcare diffusion gap (0.273) exceeds the economy-wide gap (0.249) by 10%.

This is not because healthcare tasks are poorly suited to AI. It likely reflects regulatory constraints, verification requirements, liability concerns, and institutional inertia that slow adoption even where capability exists. The gap is largest for practitioner-level occupations (SOC 29) — neurologists, psychiatrists, pediatricians — where theoretical exposure is moderate to high but observed usage is near zero.

### 3.3 AI usage concentrates on the administrative layer

The central finding: within healthcare, the correlation between administrative task share and observed AI exposure is **0.76**. Admin-heavy healthcare occupations (where admin_share > clinical_share) have observed AI usage nearly five times higher than clinical-heavy occupations (0.101 vs. 0.021).

The pattern is strikingly visible at the extremes:
- **Medical Transcriptionists** (admin_share = 0.94, clinical_share = 0.00): observed exposure = 0.64
- **Medical Records Specialists** (admin_share = 0.71, clinical_share = 0.00): observed exposure = 0.67
- **Oral and Maxillofacial Surgeons** (admin_share = 0.00, clinical_share = 0.84): observed exposure = 0.00
- **Surgical Assistants** (admin_share = 0.00, clinical_share = 0.57): observed exposure = 0.00

In a regression of observed exposure on admin_share and job_zone for health occupations only, admin_share carries a coefficient of **0.62** (p < 0.001, R-squared = 0.58). A 10 percentage-point increase in admin task share is associated with 6.2 percentage points higher observed AI usage. Job zone (education level) is not statistically significant in this model (p = 0.21), suggesting that within healthcare, task composition matters more than education requirements for predicting where AI is actually used.

### 3.4 Education and wage gradients

Across all occupations, both theoretical and observed exposure increase with education level (Job Zone):

| Job Zone | N | Mean Theoretical | Mean Observed |
|----------|---|-----------------|---------------|
| 2 (HS + Training) | 321 | 0.186 | 0.031 |
| 3 (Vocational/Associate's) | 184 | 0.326 | 0.063 |
| 4 (Bachelor's) | 165 | 0.509 | 0.158 |
| 5 (Graduate/Professional) | 128 | 0.439 | 0.109 |

The theoretical-observed gap is largest for Zone 4 (Bachelor's-level) occupations. Zone 5 occupations (graduate/professional degrees) have slightly lower theoretical exposure than Zone 4 but still substantial observed usage — consistent with knowledge-intensive work having both high potential and meaningful barriers to adoption.

In the full-sample regression (R1), a healthcare dummy carries a coefficient of **-0.077** (p < 0.001) — healthcare occupations show significantly lower observed AI usage even after controlling for job zone and admin task share. This is the regression-adjusted version of the descriptive finding: healthcare is under-adopting relative to its theoretical potential.

---

## 4. Robustness

The admin-share result is stable across specifications:
- The bivariate correlation (0.76) is consistent with the multivariate coefficient (0.62).
- Replacing importance-weighted shares with unweighted count-based shares produces qualitatively identical results.
- The 4 false-negative clinical tasks in validation (clinical tasks misclassified as "other") would, if corrected, *increase* the admin-share coefficient slightly — our conservative tagger biases toward the null.
- Alternative theoretical exposure measures (E1-only, E1+E2, human-only beta) shift magnitudes but not the direction or significance of the admin-share finding.

Full regression tables and robustness outputs are available via `make analyze`.

---

## 5. Policy implications

### Medical scribes and documentation automation

Medical Transcriptionists and Medical Records Specialists — the two healthcare occupations with the highest observed AI usage — are both documentation-focused roles. This suggests that AI's near-term impact on healthcare is concentrated in the *documentation layer*, not in clinical decision-making. Health systems investing in AI-assisted clinical documentation (ambient scribing, automated coding) are riding an adoption pattern already visible in the data.

### Prior-authorization and administrative burden

The admin-share gradient suggests that occupations with heavier administrative burden are more receptive to AI tools. This aligns with the well-documented problem of administrative burden in U.S. healthcare — prior authorization, claims coding, quality reporting — and suggests that AI adoption may naturally concentrate where the paperwork pain is greatest. Policymakers considering AI guardrails should note that the current adoption frontier is administrative, not clinical.

### Clinical AI adoption requires different conditions

The near-zero observed usage for clinical-heavy occupations (surgeons, physical therapists, dental hygienists) despite moderate theoretical exposure suggests that capability alone does not drive adoption for clinical tasks. Regulatory requirements, liability frameworks, verification workflows, and clinical culture create friction that slows diffusion. Policy interventions to accelerate clinical AI (or to govern it) should target these institutional barriers, not capability development.

### Scope-of-practice and workforce planning

If AI continues to absorb administrative tasks preferentially, the *effective* task composition of healthcare occupations will shift toward clinical work. This has implications for scope-of-practice discussions: roles that currently blend admin and clinical tasks (e.g., pharmacy technicians, registered nurses) may see their admin components automated, concentrating human effort on clinical activities. Workforce training programs should anticipate this shift.

### The diffusion gap as a timing signal

The diffusion gap is not a permanent feature — it indicates *where adoption has not yet occurred* despite theoretical readiness. Occupations at the top of the healthcare diffusion gap ranking (genetic counselors, pediatricians, psychiatrists) are candidates for *future* AI diffusion as institutional barriers evolve. This is not a prediction; it is a map of where the theoretical potential remains untapped.

---

## 6. Limitations and future directions

**Cross-sectional design.** We observe associations, not causal effects. Admin-heavy occupations may adopt AI more readily for reasons beyond task composition — different institutional contexts, employer size, technology infrastructure.

**Single AI system.** The AEI measures Claude usage. Healthcare occupations using Epic's AI tools, ambient scribing products, or other AI systems will appear as low-observed in our data despite real adoption.

**Conservative clinical tagger.** The GWA-based classification misses clinical tasks that route through non-clinical GWAs (diagnosis through "Analyzing Data," patient monitoring through "Monitoring Processes"). An LLM-based classification robustness check is planned.

**No within-occupation variation.** We observe occupation-level averages. AI usage likely varies substantially across employers, regions, and practice settings within the same occupation.

**Future work.** (1) LLM-classification robustness pass on admin/clinical tagging. (2) Geographic variation using state-level OEWS data. (3) Temporal analysis using multiple AEI releases to track diffusion over time. (4) Integration of AIOE (AI Occupational Exposure) dataset as an alternative observed measure.

---

*This analysis uses only open, properly licensed data. Code and methodology are fully reproducible via `make all`. The mart_occupation_exposure table, all figures, and regression outputs can be regenerated from raw data. See reports/methodology.md for technical details and reports/data_dictionary.md for column-level documentation.*
