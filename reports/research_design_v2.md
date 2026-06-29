# Research Design v2 — Elevating the AI Labor Impact Observatory to Working-Paper Standard

**Status:** design memo only. No pipeline code, no commits. Drafted 2026-06-29 against the M4 cross-section (`make all` passes; canonical WLS spec pinned at R3 admin_share = +0.519, p = 0.033, R² = 0.42, n = 81).

**Audience:** the next reader is a labor economist refereeing this for the Anthropic Economics & Policy Fellows pool. The bar is a credible grad-seminar / NBER WP-grade paper, not a polished journal submission.

---

## TL;DR

- **GO on a temporal panel — but only under a defensible transform.** The Anthropic Economic Index (AEI) has shipped six releases (Feb 2025 → Jun 2026). The headline metric is a *within-AI compositional share* (denominator = total Claude activity), whose levels are not panel-comparable because the model, the user base, the sampling cadence, and even the chat-vs-API channel mix all shift between releases. A naive levels panel would conflate genuine occupational diffusion with Claude-userbase growth. A two-way FE specification on *within-wave normalized share* (rank or share/wave-mean) cleanly isolates relative movement across occupations and is the right vehicle for the β-convergence and admin×time tests.
- **CONDITIONAL-GO on a healthcare-vs-economy differential.** Healthcare-specific trends, relative to the economy-wide trend, are robust to the common Claude-userbase shock (it differences out). This is the strongest causal-feeling claim the data can support — "healthcare's diffusion gap is [closing / persistent / widening] relative to the rest of the economy."
- **NO-GO on an OEWS employment-trajectory analysis as the centerpiece.** The 3-year rolling sample, the 2010→2018 SOC break, suppression discontinuities, and BLS's own warnings collectively make this a fragile add-on, not a load-bearing finding. Keep it as **one** descriptive figure with explicit framing, or drop it.
- **Referee fixes that matter (in priority order):** (1) cluster SEs by SOC major group; (2) bootstrap CIs on the diffusion gap and the healthcare aggregate; (3) LLM cross-validation of the admin/clinical rule; (4) routine-task intensity (RTI) control to ground the admin/clinical split in the Autor-Levy-Murnane framework. Each is a few-hour fix and each closes a real referee objection.

The roadmap at the end stages this as **three** focused additions, not ten. Depth on the temporal panel + robustness battery, not breadth across new figures.

---

## Part A — Temporal feasibility (the centerpiece)

### A.1 AEI release inventory

The Anthropic Economic Index has shipped six dated releases on the HuggingFace dataset `Anthropic/EconomicIndex`, plus the stable `labor_market_impacts/` directory the M4 pipeline currently uses. The flagship paper (Handa et al. 2025, arXiv:2503.04761) accompanied the first release.

| Wave | Release | Underlying model(s) | What changed | Reference |
|------|---------|---------------------|--------------|-----------|
| T1 | `release_2025_02_10` | Claude 3.5 family | Initial: O\*NET task mappings, automation-vs-augmentation, occupation-level shares | [1st report](https://www.anthropic.com/news/the-anthropic-economic-index); arXiv 2503.04761 |
| T2 | `release_2025_03_27` | Claude 3.7 Sonnet | Cluster-level insights; ~6 weeks after T1 | [2nd report](https://www.anthropic.com/news/anthropic-economic-index-insights-from-claude-sonnet-3-7) |
| T3 | `release_2025_09_15` | Sonnet 4 | Geographic disaggregation; first-party API channel added | [3rd report](https://www.anthropic.com/research/anthropic-economic-index-september-2025-report) |
| T4 | `release_2026_01_15` | Sonnet 4.5 | Economic primitives | [4th report](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report) |
| T5 | `release_2026_03_24` | Opus 4.5 / 4.6 | "Learning curves" longitudinal cut by user tenure | [5th report](https://www.anthropic.com/research/economic-index-march-2026-report) |
| T6 | `release_2026_06_26` | Mixed (Opus / Sonnet / Claude Code) | Hourly sampling; output-classifier artifacts; chat / Cowork / 1P-API split | [6th report](https://www.anthropic.com/research/economic-index-june-2026-report) |

The stable `labor_market_impacts/` directory the project currently reads (`job_exposure.csv`, `task_penetration.csv`) is the cross-sectional reduction Anthropic maintains for downstream use; it does **not** version-stamp to one wave.

### A.2 What is the metric, exactly?

This is the make-or-break question. Reading the dataset cards and the March/June 2026 reports carefully:

**The headline `job_exposure` figure is a within-AI compositional share.** The denominator is total Claude activity in the sampling window; the numerator is the share of that activity classified (via Clio + O\*NET task mapping) to occupation *i*. Anthropic is explicit in the June 2026 report that Figure 2.3 examines *"the share of conversations…coming from the specified wage quartile"*, not penetration across workers. It is **not** an adoption rate over the underlying labor force — there is no employment denominator.

There is also `task_penetration.csv` (task-level), which is structurally the same compositional share at finer granularity.

Practical consequence: if Claude's user base doubles between T1 and T6 (it has), an occupation's *level* of compositional share can fall even when its absolute usage grows. Levels are denominator-contaminated; only relative position within a wave is shock-free.

### A.3 Cross-release comparability — what Anthropic itself says

The March 2026 report ("Learning Curves") is the most useful primary source. Verbatim and paraphrased highlights:

- "Almost all tasks in this sample appeared in at least one of our previous samples" — the **task taxonomy** is stable enough for occupation-level matching across waves. This is the foundation for any panel at all.
- "Many fewer novel O\*NET tasks than in our previous report" — sampling is saturating, not exploding.
- **Explicitly NOT comparable**: "Coding tasks migrated from Claude.ai to API between reports, making platform-level task concentration harder to interpret as pure usage change." This is a structural break in the chat-only series and is why T6's channel-split data matters.
- **Stated as more comparable**: task concentration (Herfindahl-style), education years required, personal-vs-work usage, geographic indices.
- Confounders Anthropic flags: Super Bowl 2026 ads brought a wave of first-time users into T5's sampling window; T5 also overlapped winter break, dropping coursework conversations by ~7 points. These are *sampling-period* artifacts, not real adoption shifts.
- Survivorship bias in the "learning curves" tenure cut: longer-tenure users "may be seeing positive results from their usage."

The clean inference: **cross-release levels of share are contaminated** by (a) model substrate (3.5 → 3.7 → 4 → 4.5 → 4.6), (b) user-base composition (technical early adopters → mainstream), (c) sampling-period events, (d) platform mix (chat vs API vs Claude Code). **Within-wave relative position** of occupations is the cleanest comparable quantity across waves; **wave-mean-normalized share** is the second-cleanest. **Raw share-level differences** are the most contaminated.

### A.4 Defensible panel construction

**Retained waves: T1, T3, T4, T5, T6** (drop T2 — only 6 weeks after T1, same window for noise purposes). This gives 5 waves over 16 months with roughly quarterly spacing after T1→T3.

**Unit of analysis:** occupation × wave at the 6-digit 2018 SOC level. Keep only occupations present in all 5 retained waves (this is the panel-balance restriction; Anthropic's claim of taxonomic stability suggests the loss is small — likely under 5%, but quantify before committing).

**Dependent variable construction — three choices, in increasing robustness to denominator drift:**

1. **Raw share** `s_{i,t}` — what's already in `job_exposure.csv`. Fragile to userbase growth. Acceptable *only* with two-way FE.
2. **Wave-mean-normalized share** `s_{i,t} / mean_t(s)` — divides out the common scale. Multiplicative version of wave FE.
3. **Within-wave rank** `r_{i,t} = rank(s_{i,t}) / N_t` — non-parametric, throws away level info but is the most robust to denominator drift and to non-uniform userbase shifts (e.g., if Claude's userbase tilts toward coders, that shifts the levels of high-coding occupations but their *ranks* should change less).

**Recommended primary specification:** (2) wave-mean-normalized share with two-way FE. **Robustness:** (1) raw share with two-way FE, and (3) rank-rank panel. If the three give qualitatively the same answer, the headline is robust; if they diverge, that's itself the finding (denominator drift is doing real work, and the levels panel cannot be defended).

### A.5 Estimating equations

Let *i* index occupation, *t* index wave (T1, T3, T4, T5, T6). Let `y_{i,t}` denote the chosen dependent variable (default: wave-mean-normalized share). Let `H_i = 1` if occupation *i* is in SOC 29 or 31 (healthcare). Let `admin_i` and `clinical_i` be the time-invariant admin/clinical task shares from the existing M2 mart.

**Eq. 1 — Two-way FE baseline.**
```
y_{i,t} = α_i + λ_t + ε_{i,t}
```
- `α_i`: occupation fixed effects absorb time-invariant occupation traits (task structure, regulatory environment, education requirement).
- `λ_t`: wave fixed effects absorb the common Claude-userbase / model-capability shock at each release.
- Identifying variation: deviation of `y_{i,t}` from its occupation mean, net of the common wave shift.
- This spec by itself is a *test* — if R² is dominated by `α_i` and `λ_t` (i.e., the residual after two-way demeaning is tiny), then there is essentially no idiosyncratic within-occupation movement to explain, and the project should pivot back to cross-sectional depth.

**Eq. 2 — Healthcare differential trend.**
```
y_{i,t} = α_i + λ_t + γ·(H_i × t) + ε_{i,t}
```
where `t` is wave index (0, 1, 2, 3, 4) or wave fraction of a year. `γ` answers the headline question: *is healthcare's share trending differently from the rest of the economy?* `γ < 0` says healthcare is falling behind; `γ > 0` says it is catching up. This is **the strongest causal-feeling claim the data can support**: a differential trend cleanly differences out the common shock if the shock affects healthcare and non-healthcare proportionally. If the Claude userbase shift is non-uniform (it likely is — coding tilts non-health), `γ` is biased; report it bounded by the three DV variants in A.4 to show the result isn't a wave-mix artifact.

**Eq. 3 — β-convergence (catch-up).**
```
Δy_{i, T1→T6} = α + β·y_{i, T1} + δ·H_i + θ·(H_i × y_{i, T1}) + Z_i'·η + ε_i
```
- A negative `β` is the canonical β-convergence finding: high-initial-share occupations are losing relative share (saturation / regression to the mean). A positive `β` is divergence (winner-take-all).
- `δ` is the healthcare-level shift; `θ` is the headline: *does healthcare converge at a different rate than the rest of the economy?*
- `Z_i` includes `admin_share`, `job_zone`, `log(a_median)` from the existing mart.
- Identifying variation: cross-occupation differences in initial share predicting subsequent change. Standard β-convergence assumes the underlying process is mean-reverting around a common steady state; healthcare may have a *different* steady state, which is what `δ` captures.

**Eq. 4 — Admin × time interaction (within healthcare).**
```
y_{i,t} = α_i + λ_t + π·(admin_i × t) + ρ·(clinical_i × t) + ε_{i,t}   [i ∈ healthcare]
```
- Restricted to the 81 health-sector SOCs.
- `π > ρ`: admin-heavy health occupations are pulling away from clinical-heavy ones over time — the diffusion hypothesis writ longitudinally.
- `π ≈ ρ`: the cross-sectional admin gradient is *not* widening over time. Adoption is moving uniformly across health tasks.
- `π < ρ`: clinical adoption is catching up — would be the most surprising / interesting finding.

**What these equations do NOT support causally:**
None of A.5 identifies a causal effect of AI on labor outcomes, and none identifies a causal effect of task composition on AI adoption. They identify **conditional associations of within-occupation share movement with task composition, after netting out a common time shock**. The right language in the writeup is "associated with," "consistent with," and "co-moves with." Never "caused by." A referee will pounce on causal slippage here — this is the central rhetorical discipline of Part C.

**Cluster SEs by SOC major group** (2-digit SOC) for all four equations — see Part C.

### A.6 Fallback if A.5 fails

If the panel-balance restriction loses too many occupations (>10%), or if Anthropic restructures the file layout between releases so reliable matching at 6-digit SOC becomes impossible, fall back to a **two-snapshot framing**: T1 (Feb 2025) vs T6 (Jun 2026) only, framed as "a first-vs-latest snapshot comparison with explicit cross-release caveats." The β-convergence and admin×time tests collapse to first-differences. This is weaker — five waves give power to estimate `λ_t` separately — but it is still publishable as a descriptive finding with the right framing.

---

## Part B — Outcome trajectories (OEWS), secondary, HIGH-caveat

### B.1 OEWS vintages and the 3-year rolling sample

OEWS publishes annually as of the May reference period. Vintages from May 2019 through May 2025 are available. The current OEWS file the project uses is `national_M2025_dl.xlsx` (May 2025).

**The 3-year rolling sample is the central methodological hazard.** From BLS's own documentation (paraphrasing the technical notes and the FAQ summary captured via the CDC mirror and Monthly Labor Review):

> *Each set of OEWS estimates is produced by combining six semiannual panels of survey data collected over a three-year period. … Each year, the two oldest survey panels drop out of the sample and two new survey panels are added.*

> *Sudden changes in occupational employment or wages in the population, as well as some types of methodological and classification changes, will show up in the OEWS estimates only gradually.*

> *Classification systems, data collection methods, survey reference periods, and estimation methodology have changed over time. Because of these changes, caution should be used in trend analysis.*

**What this means for the project:** two adjacent OEWS vintages share ~4 of 6 underlying panels. Year-over-year "change" from May 2024 to May 2025 is mostly the same data twice, with one fresh panel added at the front and one stale panel rolling off the back. The effective independent time spacing is closer to **three years**, not one.

### B.2 SOC taxonomy break

- May 2019 and earlier: **2010 SOC**.
- May 2020 and May 2021: hybrid 2010/2018 SOC (BLS implemented the 2018 SOC over the 3-year rolling window, so transitional vintages are mixed).
- May 2022 onward: **fully 2018 SOC**.

For a stable post-2019 panel with our existing 2018-SOC join key, only **May 2022, 2023, 2024, 2025** are clean. That's 4 vintages spanning 3 years of effectively-independent data given the rolling sample — at best **two** effectively-independent snapshots.

### B.3 Suppression and wage-deflator issues

- Confidentiality suppression varies year to year for the same SOC (an occupation that crosses the suppression threshold in one year may not in another). A balanced panel requires dropping any SOC suppressed in *any* vintage, which can lose 5-15% of the sample asymmetrically (suppression concentrates in small occupations).
- Wage deflator: BLS does not publish a real-wage OEWS series. CPI-U is the conventional choice but is contested (PCE for cross-occupation consumption baskets; ECI for wage-specific deflation). Use **CPI-U** for transparency, footnote the alternatives.

### B.4 Recommendation — single descriptive figure, heavy caveats

A descriptive employment / wage trajectory analysis (do higher-AI-exposure occupations show different employment growth between 2022 and 2025?) is **defensible only as a descriptive figure with explicit framing**, not as a core finding. The recommendation:

- **One figure**: 2022→2025 log-employment change on the y-axis, theoretical exposure (or observed AEI exposure) on the x-axis, points colored by `is_health`. A simple binscatter with a fitted line and the caveat that ~3 of the 3-year window is shared sample.
- **No regression as a headline.** A single OLS slope from this figure is fine to report in a footnote, with SEs clustered by major group, but it cannot bear the weight of the paper.
- **Framing language, verbatim**: *"Higher-exposure occupations have grown / shrunk at a [faster / slower / indistinguishable] rate between 2022 and 2025. This association is consistent with [augmentation / substitution / no effect] but the OEWS 3-year rolling sample, suppression continuity, and the 2018-SOC transition (May 2022 was the first fully-2018-SOC vintage) preclude causal interpretation. We make no claim about AI-induced employment change."*
- **If unwilling to write the caveat in that strength, drop the figure entirely.** A weakly-framed employment-trajectory figure invites a referee to dismiss the whole paper.

**Verdict on Part B: RESTRICT.** One footnote-level figure, or skip.

---

## Part C — Referee the existing cross-section

The cross-section is already clean. The fixes below are not bug-fixes; they are the gap between "competent grad-student paper" and "defensible working paper."

### C.1 Standard errors not clustered by SOC major group

**Critique.** Occupations within the same 2-digit SOC major group (all 29-xxxx healthcare practitioners; all 31-xxxx healthcare support) share unobserved regulatory, labor-market, and institutional features. HC1 robust SEs assume independent observations; clustering at the major-group level is the standard adjustment in labor-economics applications of the SOC structure (see Acemoglu-Autor 2011 conventions).

**Fix.** Refit all three regressions with `cluster=major_group`. In statsmodels: `model.fit(cov_type='cluster', cov_kwds={'groups': df['major_group']})`. The number of clusters is ~22 — adequate for the standard asymptotic, but for healthcare-only (R3) the effective cluster count is 2 (SOC 29 and 31), which is **too few for clustered SEs**. For R3 use either (a) HC1 (status quo) with a footnote, or (b) wild-cluster bootstrap with the 2 clusters (Cameron-Gelbach-Miller). Practically: report both R3 numbers and call out the small-cluster issue.

**Cost.** One afternoon. May inflate full-sample SEs by 20-50%. Likely flips the R1 `is_health` coefficient's significance from "p<0.001" to "p<0.05" range; admin_share will survive.

### C.2 Diffusion gap reported without CIs

**Critique.** "Healthcare diffusion gap = 0.27 vs economy-wide 0.25" is reported as a point estimate. A referee asks: is the 0.02 difference statistically distinguishable from zero?

**Fix.** Block bootstrap (1000 reps) the diffusion gap distribution at the SOC major-group level. Report 95% CIs on the healthcare and economy aggregates, and on the difference. The cluster level for the bootstrap matters — bootstrap individual SOCs and you'll get artificially tight CIs.

**Cost.** Half a day. Likely shows healthcare-vs-economy difference is *not* significant at conventional levels in unweighted means but is significant in employment-weighted means; that itself is a finding.

### C.3 Admin/clinical classification has no LLM cross-validation

**Critique.** The current rule-based GWA classifier has a 41-task hand-validation by one rater (presumably the author) showing 100% precision and moderate clinical recall. A referee will ask: (a) inter-rater reliability with at least one second human rater on a random subsample, (b) LLM cross-validation against an independent classifier (e.g., GPT-4 / Claude classifying the same tasks from raw text, blinded to the rule output).

**Fix.** Two passes.
- (i) **LLM classification** of all ~19k O\*NET task statements via a small Claude API call ("classify this task as admin / clinical / both / other; brief reasoning"). Report agreement rate with the rule-based classifier (Cohen's κ), the disagreement cases, and which direction disagreements run.
- (ii) **Rerun R3** with the LLM classification as the `admin_share` source. If the coefficient is within ±20% of the rule-based estimate, the rule is robust. If it's wildly different, the headline needs revision.

The methodology already says this is "planned" — execute it.

**Cost.** ~$15 of API calls + half a day of code. **High-value fix** — turns a vulnerable point into a strength.

### C.4 Unweighted descriptives vs weighted regressions inconsistency

**Critique.** The descriptives report unweighted occupation means (each SOC weighted equally, regardless of employment). The regressions are WLS employment-weighted. A reader comparing the two will see different "average" exposure values and be confused. The Education Section 3.4 table is unweighted; the headline coefficient is weighted.

**Fix.** Add weighted versions of the descriptives in parentheses or as a parallel column. Specifically the by-job-zone table should show both unweighted occupation-mean and employment-weighted means. The healthcare aggregate ("0.27 vs 0.25") should also be reported both ways.

**Cost.** One hour.

### C.5 Measurement error in exposure proxies

**Critique.** Eloundou β is a noisy proxy for "true" exposure. Classical errors-in-variables biases coefficients **toward zero** (attenuation). The headline 0.519 / 0.624 is therefore a *lower bound* on the true admin-share gradient — but this is not currently said.

**Fix.** Two options.
- (a) **Add a footnote** stating "Eloundou β and admin_share are both measured with error; coefficients reported are attenuation-biased lower bounds on the true population parameter." Cheapest, zero new code.
- (b) **IV-style robustness**: use AIOE (Felten-Raj-Seamans 2021) as an instrument for Eloundou β, or vice versa. The two proxies share the same construct ("AI-relevant task content") but have measurement errors from different sources (Eloundou from human + GPT-4 raters; AIOE from word-vector similarity to AI patent abstracts). Errors are unlikely to be perfectly correlated, so each is a partial instrument for the other. Run as 2SLS in R1; report the IV estimate alongside OLS/WLS. The IV will likely be larger than OLS, confirming attenuation.

**Cost.** (a) is free. (b) is half a day including downloading Felten et al.'s data file. Recommend (a) for the writeup + (b) as a robustness appendix.

### C.6 Missing routine-task intensity (RTI) control

**Critique.** The admin/clinical distinction in healthcare maps almost perfectly onto the Autor-Levy-Murnane (2003) routine / non-routine distinction: admin tasks are predominantly *routine cognitive* (documentation, coding, scheduling); clinical tasks are predominantly *non-routine cognitive analytic* (diagnosis) or *non-routine manual* (procedures). A referee will say: "Your admin_share coefficient is just picking up routine-task intensity. The ALM framework already predicts that automation hits routine tasks first. What's new?"

**Fix.** Construct a Routine Task Intensity score per SOC from O\*NET work activities, following the standard literature mapping (Autor-Dorn 2013; Acemoglu-Autor 2011 handbook). The recipe: RTI = (routine cognitive importance + routine manual importance) − (non-routine analytic + non-routine interpersonal + non-routine manual). Add RTI as a control in R3:
```
observed_exposure ~ admin_share + RTI + log_wage + job_zone   [health-only]
```
- If `admin_share` survives at significant magnitude with RTI controlled, the admin-vs-clinical story is *not* reducible to ALM — there is something specific about administrative healthcare work that AI is targeting beyond routineness. **This is the strongest version of the headline.**
- If `admin_share` collapses to insignificance once RTI is in, the headline becomes "the ALM routine-task pattern holds in healthcare," which is less novel but still solid.

**Cost.** One day (building the RTI mapping is the work; the regression is one line). **Highest-value single fix** — situates the project in the canonical labor-economics framework.

### C.7 Causal-language slippage

Read carefully through `policy_memo.md` and tag any phrase that could be read causally. From the current draft:

- §3.3: *"AI usage concentrates on administrative tasks, not clinical ones"* — OK, descriptive.
- §3.3: *"A 10pp increase in admin task share is associated with 5.2pp higher observed AI usage"* — **good language** ("associated with").
- §5: *"AI adoption may naturally concentrate where the paperwork pain is greatest"* — borderline. "Naturally concentrate" implies a causal mechanism. Rewrite: "Adoption is *correlated with* admin-task share, consistent with…"
- §5: *"AI's near-term impact on healthcare is concentrated in the documentation layer"* — *impact* is causal in feel. Rewrite: "AI usage in healthcare is concentrated in the documentation layer."
- §5: *"AI tools are more receptive"* — "receptive" anthropomorphizes occupations; just say "shows higher usage."
- §5.3: *"capability alone does not drive adoption"* — `drive` is causal. Restrict to "capability alone is insufficient to predict adoption."

These are 10-minute fixes that materially change the tone for a skeptical reader.

### C.8 Other issues a referee might raise

- **The 798-occupation universe** excludes O\*NET-SOC variants where AEI does not report; this is missing-not-at-random (AEI under-reports very small occupations). Briefly note in §6 limitations.
- **Healthcare = SOC 29 + 31 only** excludes SOC 21-1014 (mental health counselors), SOC 25-1071 (health specialties teachers), SOC 11-9111 (medical and health services managers). A robustness check that uses a broader "health" definition (e.g., NAICS 62 industry-of-employment) would strengthen the result. Skip unless time allows.
- **Single AI system caveat** is well-stated. Don't change.

---

## Part D — Situate in the literature

The project's value is **not** novel methodology; it is **clean execution + the health-sector administrative-vs-clinical decomposition**. Position accordingly. The writeup needs to engage with the following:

1. **Eloundou, Manning, Mishkin & Rock (2024). "GPTs are GPTs." *Science*.** The theoretical exposure source. Our finding extends theirs by adding the *observed* counterpart and computing the gap.
2. **Felten, Raj & Seamans (2021). "Occupational, industry, and geographic exposure to AI." *Strategic Management Journal*.** AIOE — the earlier, patent/news-text-based exposure measure. Use as a robustness check on theoretical exposure (Part C.5).
3. **Webb, M. (2020). "The Impact of Artificial Intelligence on the Labor Market." Stanford WP.** Patent-text-based exposure (the original NLP-from-patents approach). Third independent proxy for theoretical exposure. Webb finds AI exposure concentrates on high-skill jobs — broadly consistent with our finding that AI exposure rises with job zone.
4. **Autor, Levy & Murnane (2003). "The Skill Content of Recent Technological Change." *QJE*.** The foundational routine-task framework. Our admin/clinical decomposition is structurally analogous; we should say so and run the RTI control (Part C.6) to demonstrate the relationship.
5. **Acemoglu & Autor (2011). "Skills, Tasks and Technologies." *Handbook of Labor Economics*.** The task-based model under which all task-exposure work operates. Our project is implicitly task-based; cite for the framework.
6. **Acemoglu & Restrepo (2022). "Tasks, Automation, and the Rise in U.S. Wage Inequality." *Econometrica*.** The state-of-the-art mapping from task automation to wage outcomes. Cite to set up *why* the diffusion gap matters (the gap is the gap between potential and realized labor demand shocks).
7. **Brynjolfsson, Li & Raymond (2023). "Generative AI at Work." *QJE* (2025).** The call-center field experiment showing AI augments low-skill workers more than high-skill. Provides micro evidence for the augmentation channel. Our cross-sectional pattern (admin-heavy roles showing the most AI usage in healthcare) is at the *occupation* level what they document at the *worker* level.
8. **Handa, K., et al. (2025). "Which Economic Tasks are Performed with AI?" arXiv:2503.04761.** The AEI source paper. Our project is an externalization of their methodology to the healthcare-decomposition question.
9. **Subsequent AEI reports** — at minimum, the [March 2026 "Learning Curves" report](https://www.anthropic.com/research/economic-index-march-2026-report) and the [June 2026 report](https://www.anthropic.com/research/economic-index-june-2026-report). Cite for the temporal dimension if Part A is executed.
10. **Goldin & Katz (2010, *The Race Between Education and Technology*)** OR **Brynjolfsson, Mitchell & Rock (2018, "What Can Machines Learn?" *AEA P&P*).** Pick one for the broad macro framing of how technological change reshapes labor demand. Brynjolfsson-Mitchell-Rock is closer to the AI-specific question.
11. **For health workforce specifically**: at minimum cite **Topol (2019, *Deep Medicine*)** or **Esteva et al. (2019, "A guide to deep learning in healthcare." *Nature Medicine*)** for clinical AI capability; **Wachter & Cassel (2024 / 2025 commentaries in *JAMA*)** on the administrative-burden problem in U.S. healthcare. The Wachter angle is critical — it grounds our admin-share finding in the well-documented "physicians spend 49% of EHR / documentation time" empirical literature.
12. **Briggs & Hatzius / Goldman Sachs (2023, "The Potentially Large Effects of Artificial Intelligence on Economic Growth.")** Not academic, but the most-cited AI-labor-impact public estimate. Engage in passing to show awareness of the policy-economics conversation.

**Twelve is the upper bound** — pick 8-10 for the actual writeup. Mandatory: 1, 2, 4, 5, 7, 8, and at least one health item (11). Webb (3) and the AEI follow-on reports (9) become mandatory **if** Parts A and C.5 are executed.

---

## GO / NO-GO summary

| Item | Verdict | Reason |
|------|---------|--------|
| Temporal AEI panel (A.5 Eq. 1-2) | **GO** | 5 retained waves, taxonomically stable, wave FE absorbs common shock. Use wave-mean-normalized share + rank robustness. |
| β-convergence + healthcare interaction (A.5 Eq. 3-4) | **GO** | Same data, well-defined estimands. The healthcare differential is the strongest causal-feeling claim available. |
| OEWS employment / wage trajectories (Part B) | **RESTRICT** | One descriptive figure with explicit caveats, or skip. Cannot bear the weight of a headline. |
| Cluster SEs by major group (C.1) | **GO** | Trivial cost, real fix. |
| Bootstrap diffusion-gap CIs (C.2) | **GO** | Half day; the "0.27 vs 0.25" claim is currently unsupported. |
| LLM admin/clinical cross-validation (C.3) | **GO** | Methodology already promises it. ~$15 + half day. |
| RTI control in R3 (C.6) | **GO** | Highest-value single fix. Grounds the headline in ALM. |
| IV-style measurement-error robustness (C.5b) | **OPTIONAL** | Strong appendix item. Skip in v2; add in v3 if time. |
| Broader-health definition (C.8) | **SKIP** | Marginal value; not headline-changing. |

---

## Staged roadmap

**Three additions, in order. Stop at any point if time runs out — each phase is independently shippable.**

### Phase 5 — Robustness battery (≈ 8-12 hours, the highest-value next step)

Execute C.1, C.2, C.3, C.6 in that order. Add C.7 (causal-language tightening) as a 30-minute pass at the end.

Deliverable: updated `reports/regressions.txt` with clustered SEs, a new `reports/robustness.md` documenting the LLM-vs-rule κ, the RTI-augmented R3, and bootstrap CIs for the diffusion gap. Update README headline if R3 admin_share survives RTI; if it doesn't, rewrite the headline as "the routine-task automation pattern holds in healthcare administration."

**This phase alone elevates the paper from cross-section-only to robustness-battery-complete.** A referee who reads only Phase 5 should not be able to dismiss the headline on the four standard objections.

### Phase 6 — Temporal panel (≈ 12-20 hours, the centerpiece extension)

Execute Part A. Stages:
- A.6.1: Download all 6 AEI releases; build occupation × wave panel; compute the three DV variants (raw, wave-normalized, rank).
- A.6.2: Estimate Eq. 1 (two-way FE) on all three DV variants. If they agree, proceed; if they diverge, write that up as the finding.
- A.6.3: Estimate Eq. 2 (healthcare differential trend) — the headline.
- A.6.4: Estimate Eq. 3 (β-convergence with healthcare interaction).
- A.6.5: Estimate Eq. 4 (admin × time within healthcare).

Deliverable: new `reports/panel.md`, new figure `fig7_health_diffusion_trend.png` showing healthcare vs non-healthcare share trajectories over the 5 waves, a regression table with all four equations. Headline update: "healthcare's diffusion gap is [closing / persistent / widening]."

### Phase 7 — OEWS descriptive figure (≈ 3-5 hours, optional, low priority)

Execute Part B as one descriptive figure with the verbatim framing in B.4. If unwilling to commit to that framing language, skip Phase 7 entirely. **Do not do it half-heartedly** — it is more dangerous to ship a weakly-framed employment figure than to omit the topic.

### What is explicitly NOT on the roadmap

- New cross-sectional figures (the 6 we have are enough for the cross-section).
- Geographic disaggregation (out of scope for v2; was already deferred at M1).
- AIOE / Webb full replication (Phase 5's C.5a footnote suffices for v2).
- Worker-level analysis (no microdata).
- Cost-benefit / welfare modeling (out of scope).

The discipline of this roadmap is **depth on two axes** (robustness + temporal) **rather than breadth across ten new figures**. A referee should see a cross-section paper that has been hardened against the standard objections and extended into the temporal dimension that the data uniquely allows. That is the story.

---

## Denominator-drift diagnostic (appended 2026-06-29)

This section answers the single question the Part A verdict rested on: **is the AEI release-to-release drift uniform across occupations, or is it occupation-specific?** Within-wave normalization (rank, wave-mean-normalized share) only rescues *proportional* drift. If Claude's user base shifted differentially toward or away from specific occupations between releases, the wave FE in Eq. 2 will not absorb it, and any "healthcare differential trend" estimate is contaminated.

### D.1 Structural finding — release file formats are heterogeneous

Before computing anything, the HF tree inspection revealed that the dated AEI releases do **not** ship a stable occupation-level usage file directly. They ship raw cluster-level CSVs at the `onet_task` facet level with a `value` column to be pivoted. Worse, the schemas differ across releases:

| Release | Schema family | Sampling window | Format anomaly |
|---------|--------------|-----------------|----------------|
| T1 (Feb 10, 2025) | Flat task-pct files (`onet_task_mappings.csv`, `automation_vs_augmentation.csv`) | not stated in README; conversations sampled in late 2024 per arXiv:2503.04761 | **Different schema** — pre-Clio-v3, no `geography`/`facet` long format |
| T3 (Sep 15, 2025) | `aei_raw_claude_ai_<dates>.csv` long format, facets: collaboration, country, onet_task, request, state_us | **Aug 4-11, 2025** (1 week) | First wave with `onet_task_pct` variable; 7 facets total |
| T4 (Jan 15, 2026) | Same long format, expanded to ~15 facets including `ai_autonomy`, `ai_education_years`, `multitasking`, etc. | **Nov 13-20, 2025** (1 week) | Major facet expansion; new derived metrics |
| T5 (Mar 24, 2026) | Long format, schema closer to T4 | **Feb 5-12, 2026** (1 week) | "Learning curves" added (longitudinal-by-tenure cut) |
| T6 (Jun 26, 2026) | New schema: `category_name`/`hierarchy_level`/`node_name`/`node_external_id`/`metric_id`/`value` | **Monthly** aggregates over Apr 10 – Jun 10, 2026 | **Different schema again** — column names renamed; channel split: claude_ai (chat + Cowork) vs 1p_api (excludes Claude Code) |

The stable `labor_market_impacts/job_exposure.csv` the current pipeline uses is a separate, undated, aggregated product — there is **no dated equivalent that the project can panel directly**. The dated releases also bundle different platform mixes (T3-T5: "Claude AI Free + Pro"; T5+ added Max tier; T6 split chat from Cowork from 1P-API).

**Implication**: any "panel" would require the researcher to reconstruct occupation-level shares from raw cluster data, separately per release, with different preprocessing per schema family. The work is feasible but is non-trivial *pipeline work*, not "just download and pivot." Plan accordingly.

### D.2 Empirical drift diagnostic — T3 → T4 task-level pivot

Where the schema is identical (T3 and T4 share the long format with `onet_task_pct` at global level), the drift diagnostic IS computable on the raw downloaded files without pipeline changes. I downloaded both releases (T3 = 18 MB, T4 = 94 MB) to a scratch directory and ran a one-off Python script. The waves are 13 weeks apart (Aug 4-11 → Nov 13-20, 2025).

**Universe stability:**

| | T3 (Aug 2025) | T4 (Nov 2025) |
|---|---|---|
| Distinct O\*NET task clusters at global level | 2,616 | 3,168 |
| Sum of `onet_task_pct` across non-residual clusters | 91.14% | 91.41% |
| Tasks in T3 only (dropped) | — | 261 |
| Tasks in T4 only (added) | — | 813 |
| Tasks in both | 2,355 | 2,355 |

**The task partition grew ~26% in 13 weeks** (Clio added 813 new clusters and retired 261). Because both waves still sum to ~91% of classified activity, the new clusters mostly absorbed activity from `not_classified`, not from existing clusters — so the *mechanical* dilution of old-cluster shares is small. But the **identification of "the same task" across waves** is now imperfect: 9% of T3's universe and 26% of T4's universe are unmatched.

**Cross-wave correlation (n = 2,355 tasks in both):**

| | Spearman ρ (rank) | Pearson ρ (level) |
|---|---|---|
| All matched tasks | **0.806** | 0.917 |
| Healthcare-matched tasks (n = 190 of 1,984 in O\*NET health universe) | **0.759** | 0.842 |

Rank correlation between adjacent 13-week waves is 0.81 overall and **0.76 within healthcare** — high, but with ~20-25% of rank-position variance attributable to wave-to-wave churn. Healthcare's rank stability is *lower* than the all-task average, which is the first warning sign that healthcare drift is not just the common drift.

**Aggregate share trajectory:**

| | T3 share | T4 share | Ratio T4/T3 |
|---|---|---|---|
| Healthcare task share (sum) | 2.305% | 2.505% | **1.087** |
| Non-healthcare task share (sum) | 88.840% | 88.908% | **1.001** |

**Healthcare's share of total Claude task activity grew 8.7% in 13 weeks; non-healthcare grew 0.08%.** This is the differential trend Eq. 2 was designed to capture, and it is *right-signed* (healthcare is catching up). But the magnitude — a 9% jump in a single quarter — is implausibly fast for genuine labor-market diffusion. The much more plausible explanation is that Claude's **user-base composition** shifted between Aug and Nov 2025 in a way that brought in more healthcare-adjacent users (medical students returning to fall semester, nursing/PA program cohorts).

**Within-healthcare pattern of risers vs fallers (the project's central hypothesis):**

Top T3→T4 healthcare task risers were **communication / patient-education**: "communication assistance," "educate patients about diagnoses, prognoses, or treatments," "explain procedures and discuss test results with patients," "patient education programs." Top fallers were **clinical reasoning**: "analyze and interpret patients' histories…to develop appropriate diagnoses," "interpret diagnostic test results," "develop exercise programs." This pattern is *exactly* the admin/communication-vs-clinical-judgment story the cross-section makes. As a directional signal it is encouraging.

But: the *all-task* (non-health) top risers were dominated by **teaching tasks** ("assist students who need extra help with coursework," "review class material with students," "develop instructional materials") and the top fallers were **coding/debugging tasks**. Aug → Nov is exactly the back-to-school window. This is wave-specific calendar contamination, not labor-market adoption.

### D.3 Verdict — what survives, what doesn't

The drift between adjacent waves is **non-uniform** and is **correlated with the occupational mix of Claude's user base** (back-to-school inflated teaching tasks; fall medical/nursing cohorts plausibly inflated healthcare). This is precisely the differential-drift smoking gun the user asked about. It does **not** kill the temporal panel entirely, but it dictates what claims the panel can support.

**Revised verdict on Part A's specifications:**

| Spec | Original verdict | Revised verdict | Reason |
|------|------------------|-----------------|--------|
| Eq. 1 (two-way FE baseline) | GO | **GO** | Wave FE absorbs the common drift; rank-based DV reduces vulnerability to the non-uniform piece. Treat results as exploratory descriptives, not estimands. |
| Eq. 2 (healthcare × time differential trend) | GO ("strongest causal-feeling claim") | **CONDITIONAL** | The differential is real and right-signed (8.7% vs 0.08% over T3→T4), but the *magnitude* is contaminated by user-base composition shift. Report as "healthcare's share of Claude task activity rose between T3 and T6, in a direction consistent with diffusion. We cannot disentangle genuine occupational adoption from shifts in Claude's user-base composition." NOT a velocity claim. |
| Eq. 3 (β-convergence + healthcare interaction) | GO | **DROP** | β-convergence requires stable rank ordering. Spearman 0.76 within healthcare across 13 weeks means ~24% of within-occupation rank variation across one quarter is taxonomy + composition churn. β-convergence on this data is mostly fitting noise. |
| Eq. 4 (admin × time within healthcare) | GO | **DOWNGRADE to descriptive figure** | The within-healthcare admin-vs-clinical pattern of risers/fallers (D.2 above) is too clean to ignore but too noisy to estimate as a coefficient. Present as a two-panel descriptive figure: top-N admin-task share trajectory vs top-N clinical-task share trajectory across the comparable waves. Label clearly as descriptive. |

**Revised Phase 6 plan (supersedes the §"Staged roadmap" version):**

1. **Reconstruction work (one-time, ~6-10 hours)**: ingest T3, T4, T5, T6 raw CSVs into the warehouse as `raw_aei_release_<date>` tables (skip T1: different schema + uncertain sampling date; skip T2: too close to T1). Build a `stg_aei_panel` model that pivots each release to `(release_date, task_text, share)` long format. Crosswalk task_text → 6-digit SOC via the existing `stg_onet_tasks`-derived map. Document unmatched-task fraction per release.
2. **Eq. 1 + Eq. 2 only**: two-way FE on wave-mean-normalized share and on rank. Report both, side-by-side. Headline: *"Healthcare's share of classified Claude task activity rose from X% to Y% between Aug 2025 and Jun 2026. The same calendar window saw non-healthcare share move from Z% to W%. We interpret the differential as consistent with diffusion but cannot rule out user-base composition shifts (e.g., fall academic-year cohorts of medical students). See Appendix D for the cross-release stability diagnostic."*
3. **A single descriptive trajectory figure** (`fig8_health_admin_vs_clinical_share_trajectory.png`): for the matched-across-all-waves health-task subset, plot the sum-of-shares of admin-tagged tasks vs clinical-tagged tasks at each release. Caveats baked into caption.
4. **Drop**: β-convergence, full Eq. 3 / Eq. 4 specifications, the "velocity-of-diffusion" framing.

This is a smaller Phase 6 than the original memo proposed — perhaps 8-12 hours of work, not 12-20 — and it earns a single, honest, well-scoped headline ("healthcare's share has moved over four AEI waves, in a direction and magnitude consistent with the cross-sectional admin-vs-clinical pattern, with explicit user-base-composition caveats") rather than a fragile causal-trend claim that won't survive a referee.

### D.4 What the diagnostic does NOT cover

- **T1 → T6** correlation (the longest available time window): T1's incompatible schema means matching it to later waves requires significant additional reconstruction. If executed, the rank correlation will almost certainly be **lower** than the T3-T4 value of 0.81 — but should still be meaningfully positive.
- **T5 → T6** correlation: not computed (T6 was not downloaded; its schema change adds another reconstruction step). Worth running before committing to Phase 6.
- **Within-occupation drift at SOC level** (vs at task level): the diagnostic ran at the AEI task-cluster level. Aggregating to 6-digit SOC will average out some of the noise but will introduce its own crosswalk-error. The expected direction is a *higher* Spearman at the SOC level than at the task level — perhaps 0.85-0.90.
- **The 1P API channel**: this diagnostic used Claude.ai (chat) only. The chat-vs-API split that T6 introduces likely shows different occupation mixes (API skews enterprise / coding). Whether to pool channels or hold them separate in the panel is a design choice for Phase 6 reconstruction, not this diagnostic.

### D.5 Bottom line for Phase 6 decision

**Build the panel, but with the smaller, honest ambition of Eq. 1 + Eq. 2 + one descriptive trajectory figure, NOT β-convergence and admin×time interaction estimates.** The cross-wave correlation is high enough that a panel can speak descriptively. It is not high enough — and the user-base shifts not exogenous enough — to support velocity-of-diffusion estimates. The right framing language is *"share has moved in a direction consistent with…"* throughout. Anything stronger will not survive review.

---

## Sources cited in this memo

- Anthropic Economic Index dataset card and file tree: <https://huggingface.co/datasets/Anthropic/EconomicIndex>
- 1st AEI report: <https://www.anthropic.com/news/the-anthropic-economic-index>
- 2nd AEI report: <https://www.anthropic.com/news/anthropic-economic-index-insights-from-claude-sonnet-3-7>
- 3rd AEI report: <https://www.anthropic.com/research/anthropic-economic-index-september-2025-report>
- 4th AEI report: <https://www.anthropic.com/research/anthropic-economic-index-january-2026-report>
- 5th AEI report ("Learning Curves"): <https://www.anthropic.com/research/economic-index-march-2026-report>
- 6th AEI report: <https://www.anthropic.com/research/economic-index-june-2026-report>
- Handa et al. (2025), arXiv:2503.04761
- BLS OEWS FAQ: <https://www.bls.gov/oes/oes_ques.htm>
- BLS OEWS Technical Notes (May 2025): <https://www.bls.gov/oes/current/oes_tec.htm>
- BLS OEWS Overview (3-year rolling sample, SOC transitions): <https://www.bls.gov/oes/oes_emp.htm>
- CDC NCHS reference to OEWS methodology: <https://www.cdc.gov/nchs/hus/sources-definitions/oews.htm>
- Monthly Labor Review on OEWS model-based estimates: <https://www.bls.gov/opub/mlr/2019/article/model-based-estimates-for-the-occupational-employment-statistics-program.htm>
