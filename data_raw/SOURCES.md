# Data Sources Manifest


> Every dataset used in this project is listed here with its exact URL,
> release/version, download date, license, and SHA-256 checksum.

---

## O*NET 30.3

- **Source:** https://www.onetcenter.org/database.html
- **Version:** 30.3 (production release, pinned)
- **License:** CC-BY 4.0 (Creative Commons Attribution)
- **Files:**
  - [x] Task Statements.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Task%20Statements.xlsx` | SHA-256: `0860fb680717ce9bd7703c4eb99d28228e43276c147a321e0376d62b6b0643db` | Downloaded: `2026-06-29`
  - [x] Task Ratings.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Task%20Ratings.xlsx` | SHA-256: `47d7e6d53dc711c68a0296b6eaff44ea5edd5a5bf0efcd335f3fc4e3b21988bc` | Downloaded: `2026-06-29`
  - [x] Occupation Data.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Occupation%20Data.xlsx` | SHA-256: `13b2aa4c08e6c9a3708d5e5ac83e13da5cc184e3798313c8942a266d00593ace` | Downloaded: `2026-06-29`
  - [x] Work Activities.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Work%20Activities.xlsx` | SHA-256: `f3db7579be8373f37bdecb34bc14af3f0e0b66ad424c6984a4df1ac5ebb8fda5` | Downloaded: `2026-06-29`
  - [x] Tasks to DWAs.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Tasks%20to%20DWAs.xlsx` | SHA-256: `30ce76cb114d94247c889d7540b942f02bdf9dd88e7307385acd23d994085b8e` | Downloaded: `2026-06-29`
  - [x] GWAs to IWAs to DWAs.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/GWAs%20to%20IWAs%20to%20DWAs.xlsx` | SHA-256: `024d49c7cf172514742d7ba3b6f1174487291fb1dada8a4197a2788f9a39b75a` | Downloaded: `2026-06-29`
  - [x] Job Zones.xlsx — URL: `https://www.onetcenter.org/dl_files/database/db_30_3_excel/Job%20Zones.xlsx` | SHA-256: `adc38541f13dccc387ad2a38facf24c410122c5088473492f7636690b2536f8c` | Downloaded: `2026-06-29`
  - [x] 2019_to_SOC_Crosswalk.xlsx — URL: `https://www.onetcenter.org/taxonomy/2019/soc/2019_to_SOC_Crosswalk.xlsx?fmt=xlsx` | SHA-256: `bfc6722a92c2d607e5a99dee88b7826cf5aa91f7c0453182e0c8268e32a20a19` | Downloaded: `2026-06-29`

## BLS OEWS (May 2025)

- **Source:** https://www.bls.gov/oes/tables.htm
- **Bulk archive:** https://www.bls.gov/oes/special-requests/oesm25nat.zip
- **Reference period:** May 2025 (survey reference month)
- **Release date:** 2026-05-15 (BLS announcement)
- **License:** Public domain (U.S. Government work)
- **Files:**
  - [x] national_M2025_dl.xlsx — URL: `https://www.bls.gov/oes/special-requests/oesm25nat.zip` (extracted from `oesm25nat.zip`) | Reference period: May 2025 | SHA-256: `852250997ceff9b721ff68f63e877d818f9c1ec8b1b69dd367958faedd5282b2` | Downloaded: `2026-06-29`

## Anthropic Economic Index

- **Source:** https://huggingface.co/datasets/Anthropic/EconomicIndex
- **Release:** labor_market_impacts (occupation + task exposure scores)
- **License:** CC-BY 4.0
- **Files:**
  - [x] job_exposure.csv — SHA-256: `4f0a3adf5feeb2ec5f5d02ab18cc5e851a2a4b8470bde84c0c9335017be12d68` | Downloaded: `2026-06-29`
  - [x] task_penetration.csv — SHA-256: `85bee872db1d55d3e9a7f4e89da5ae4a5d59aa8ec875d728fbf4b7d820984616` | Downloaded: `2026-06-29`

## Eloundou et al. (2024) — Theoretical Exposure

- **Paper:** GPTs are GPTs, Science 384:1306-1308 (2024)
- **Source repo:** https://github.com/OPENAI/gpts-are-gpts
- **License:** Public (academic repo)
- **Files:**
  - [x] occ_level.csv — URL: `https://raw.githubusercontent.com/OPENAI/gpts-are-gpts/main/data/occ_level.csv` | SHA-256: `40c74f53de40aec91c0017d80690cbba915f83a8bb414bcf2f884692f1749acb` | Downloaded: `2026-06-29`

## Felten/Raj/Seamans AIOE (Optional — Robustness)

- **Paper:** SMJ 2021
- **Status:** Deferred (robustness check only)
- **Files:**
  - [ ] AIOE_DataAppendix.xlsx — SHA-256: `TBD` | Downloaded: `TBD`
