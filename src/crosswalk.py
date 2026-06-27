"""
crosswalk.py — O*NET-SOC to 6-digit 2018 SOC crosswalk.

The canonical join key across all datasets is the 6-digit 2018 SOC code
(e.g., '29-1141'). O*NET uses 8-digit codes with a decimal suffix
(e.g., '29-1141.00'), and a single SOC can have multiple O*NET-SOC variants
(e.g., '15-1252.00', '15-1252.01', '15-1252.02' → SOC '15-1252').

This module:
  1. Uses the official O*NET-SOC 2019 → 2018 SOC crosswalk as the authority.
  2. Falls back to naive truncation (first 7 chars) only when a code is absent
     from the crosswalk, and logs a warning.
  3. Reports unmatched codes so no occupations silently drop.

Judgment calls documented here:
  - As of O*NET 30.3, naive truncation and the official crosswalk agree on all
    1,016 codes. Zero mismatches. But the official crosswalk is preferred so
    that any future divergence is caught.
  - When aggregating from O*NET-SOC to SOC, multiple variants are collapsed.
    For task-level data, this means averaging (importance-weighted) across
    variants. For exposure scores, this means averaging.
"""

import logging
from pathlib import Path

import duckdb
import pandas as pd

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "warehouse" / "aei.duckdb"


def load_crosswalk(con: duckdb.DuckDBPyConnection | None = None) -> pd.DataFrame:
    """
    Load the official O*NET-SOC → 6-digit SOC crosswalk from DuckDB.

    Returns a DataFrame with columns:
      - onet_soc_code: str (e.g. '11-1011.00')
      - soc_code: str (e.g. '11-1011')
      - onet_title: str
      - soc_title: str
    """
    close_con = False
    if con is None:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        close_con = True

    try:
        df = con.execute("""
            SELECT
                TRIM(onet_soc_2019_code) AS onet_soc_code,
                TRIM("2018_soc_code") AS soc_code,
                TRIM(onet_soc_2019_title) AS onet_title,
                TRIM("2018_soc_title") AS soc_title
            FROM raw_onet_soc_crosswalk
        """).fetchdf()
    finally:
        if close_con:
            con.close()

    return df


def map_onet_to_soc(
    onet_codes: list[str],
    crosswalk_df: pd.DataFrame | None = None,
) -> dict[str, str]:
    """
    Map a list of O*NET-SOC codes to 6-digit SOC codes.

    Uses the official crosswalk. Falls back to naive truncation for codes
    not found, and logs warnings for those.

    Returns: dict mapping onet_soc_code -> soc_code
    """
    if crosswalk_df is None:
        crosswalk_df = load_crosswalk()

    # Build lookup dict from official crosswalk
    official = dict(
        zip(crosswalk_df["onet_soc_code"], crosswalk_df["soc_code"])
    )

    result = {}
    unmatched = []

    for code in onet_codes:
        code = code.strip()
        if code in official:
            result[code] = official[code]
        else:
            # Fallback: naive truncation
            naive_soc = code[:7]
            result[code] = naive_soc
            unmatched.append(code)

    if unmatched:
        log.warning(
            f"Crosswalk: {len(unmatched)} O*NET-SOC codes not in official "
            f"crosswalk, fell back to naive truncation: {unmatched[:20]}"
        )
    else:
        log.info(
            f"Crosswalk: all {len(result)} O*NET-SOC codes matched "
            f"via official crosswalk"
        )

    return result


def validate_crosswalk(con: duckdb.DuckDBPyConnection | None = None) -> dict:
    """
    Run validation checks on the crosswalk and return a report dict.

    Checks:
      1. All O*NET-SOC codes in task_statements exist in the crosswalk
      2. All O*NET-SOC codes in Eloundou exist in the crosswalk
      3. Naive truncation matches official for all codes
      4. No duplicate O*NET-SOC codes in the crosswalk
      5. Row counts before/after collapsing
    """
    close_con = False
    if con is None:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        close_con = True

    try:
        crosswalk = load_crosswalk(con)
        report = {}

        # 1. Crosswalk basics
        report["crosswalk_rows"] = len(crosswalk)
        report["unique_onet_soc"] = crosswalk["onet_soc_code"].nunique()
        report["unique_soc"] = crosswalk["soc_code"].nunique()

        # 2. Check for duplicate O*NET-SOC codes
        dupes = crosswalk[crosswalk["onet_soc_code"].duplicated(keep=False)]
        report["duplicate_onet_codes"] = len(dupes)
        if len(dupes) > 0:
            report["duplicate_examples"] = dupes["onet_soc_code"].unique().tolist()[:5]

        # 3. Naive truncation vs official
        crosswalk["naive_soc"] = crosswalk["onet_soc_code"].str[:7]
        mismatches = crosswalk[crosswalk["naive_soc"] != crosswalk["soc_code"]]
        report["naive_vs_official_mismatches"] = len(mismatches)

        # 4. Coverage: task_statements
        task_codes = set(
            r[0].strip()
            for r in con.execute(
                "SELECT DISTINCT onet_soc_code FROM raw_onet_task_statements"
            ).fetchall()
        )
        xwalk_codes = set(crosswalk["onet_soc_code"])
        missing_from_xwalk = task_codes - xwalk_codes
        report["task_codes_total"] = len(task_codes)
        report["task_codes_missing_from_crosswalk"] = len(missing_from_xwalk)
        if missing_from_xwalk:
            report["task_codes_missing_examples"] = sorted(missing_from_xwalk)[:10]

        # 5. Coverage: Eloundou
        elo_codes = set(
            r[0].strip()
            for r in con.execute(
                "SELECT DISTINCT onet_soc_code FROM raw_eloundou"
            ).fetchall()
        )
        elo_missing = elo_codes - xwalk_codes
        report["eloundou_codes_total"] = len(elo_codes)
        report["eloundou_codes_missing_from_crosswalk"] = len(elo_missing)

        # 6. Many-to-one mapping stats
        soc_groups = crosswalk.groupby("soc_code").size()
        report["soc_with_multiple_onet"] = int((soc_groups > 1).sum())
        report["max_onet_per_soc"] = int(soc_groups.max())

        return report

    finally:
        if close_con:
            con.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("=== Crosswalk Validation Report ===\n")
    report = validate_crosswalk()
    for key, value in report.items():
        print(f"  {key}: {value}")

    # Quick sanity check
    crosswalk = load_crosswalk()
    mapping = map_onet_to_soc(["29-1141.00", "15-1252.00", "99-9999.00"], crosswalk)
    print(f"\nSample mappings: {mapping}")
