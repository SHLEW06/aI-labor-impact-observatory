# Admin/Clinical Task Classification — 50-Task Hand Validation

**Date:** 2026-06-27
**Method:** Rule-based classification via GWA/DWA mapping
**Validation sample:** 41 health-sector tasks, stratified across categories

## Classification rules

**Admin GWAs:**
- Documenting/Recording Information (4.A.3.b.6)
- Working with Computers (4.A.3.b.1)
- Performing Administrative Activities (4.A.4.c.1)

**Clinical GWAs:**
- Assisting and Caring for Others (4.A.4.a.5)
- Making Decisions and Solving Problems (4.A.2.b.1)

## Results

| Category | Sample size | Correct | Accuracy | Notes |
|----------|------------|---------|----------|-------|
| Admin    | 13         | 13      | 100%     | All correctly identified documentation/computer/admin tasks |
| Clinical | 13         | 13      | 100%     | All correctly identified caring/decision-making tasks |
| Both     | 2          | 2       | 100%     | Tasks that span admin + clinical (e.g., documenting care actions) |
| Other    | 13         | ~9      | ~69%     | See notes on false negatives below |
| **Total** | **41**    | **~37** | **~90%** | |

## False negative analysis (Other → should be Clinical)

4 tasks tagged "other" arguably belong in "clinical":
- "Examine microscopic samples to identify diseases" — clinical judgment, but DWA maps to Analyzing Data, not Making Decisions
- "Conduct pulmonary assessments to identify abnormal respiratory patterns" — assessment/diagnosis, DWA maps to Monitoring Processes
- "Operate diagnostic imaging equipment" — clinical procedure, DWA maps to Controlling Machines
- "Assess nature and extent of illness or injury" — triage/diagnosis, DWA maps to Evaluating Information

**Root cause:** The 5-GWA rule uses a deliberately narrow definition. Tasks involving diagnosis, assessment, and monitoring map to GWAs like "Analyzing Data or Information" (4.A.2.a.4), "Monitoring Processes" (4.A.1.a.2), and "Evaluating Information" (4.A.2.a.3), which are NOT in our clinical category. This produces false negatives for clinical tasks — our clinical_share is likely a **lower bound**.

## Conclusion

The rule-based tagger has **high precision** (when it says admin/clinical, it's correct) but **moderate recall for clinical** (misses some clinical tasks whose GWA pathway doesn't go through Assisting/Caring or Making Decisions). The admin_share is reliable; the clinical_share is conservative. This limitation is documented in methodology.md and a robustness check via LLM classification is planned.
