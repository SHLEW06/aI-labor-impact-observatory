"""
ingest.py — Download, verify, and load all raw data sources into DuckDB.

Sources:
  1. O*NET 30.3 — Task Statements, Task Ratings, Occupation Data, Work Activities,
     Tasks to DWAs, GWAs to IWAs to DWAs, Job Zones, SOC Crosswalk
  2. BLS OEWS May 2025 — National wages & employment (requires manual download)
  3. Anthropic Economic Index — job_exposure.csv, task_penetration.csv
  4. Eloundou et al. — occ_level.csv (theoretical exposure β)
  5. AIOE (optional) — Felten/Raj/Seamans robustness measure

Usage:
    python src/ingest.py            # Download all sources and load into DuckDB
    python src/ingest.py --skip-download  # Only load existing files into DuckDB
"""

import argparse
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data_raw"
WAREHOUSE = PROJECT_ROOT / "warehouse"
DB_PATH = WAREHOUSE / "aei.duckdb"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# O*NET 30.3 files
# ---------------------------------------------------------------------------
ONET_BASE = "https://www.onetcenter.org/dl_files/database/db_30_3_excel"
ONET_CROSSWALK_URL = (
    "https://www.onetcenter.org/taxonomy/2019/soc/2019_to_SOC_Crosswalk.xlsx?fmt=xlsx"
)

ONET_FILES = {
    "Task Statements.xlsx": f"{ONET_BASE}/Task%20Statements.xlsx",
    "Task Ratings.xlsx": f"{ONET_BASE}/Task%20Ratings.xlsx",
    "Occupation Data.xlsx": f"{ONET_BASE}/Occupation%20Data.xlsx",
    "Work Activities.xlsx": f"{ONET_BASE}/Work%20Activities.xlsx",
    "Tasks to DWAs.xlsx": f"{ONET_BASE}/Tasks%20to%20DWAs.xlsx",
    "GWAs to IWAs to DWAs.xlsx": f"{ONET_BASE}/GWAs%20to%20IWAs%20to%20DWAs.xlsx",
    "Job Zones.xlsx": f"{ONET_BASE}/Job%20Zones.xlsx",
    "2019_to_SOC_Crosswalk.xlsx": ONET_CROSSWALK_URL,
}

# ---------------------------------------------------------------------------
# Eloundou et al. — theoretical exposure
# ---------------------------------------------------------------------------
ELOUNDOU_URL = (
    "https://raw.githubusercontent.com/OPENAI/gpts-are-gpts/main/data/occ_level.csv"
)

# ---------------------------------------------------------------------------
# BLS OEWS — must be downloaded manually (BLS blocks automated requests)
# ---------------------------------------------------------------------------
BLS_MANUAL_INSTRUCTIONS = """
╔══════════════════════════════════════════════════════════════════════════╗
║  BLS OEWS: Manual download required                                    ║
║                                                                        ║
║  BLS blocks automated downloads. Please download manually:             ║
║                                                                        ║
║  1. Go to: https://www.bls.gov/oes/tables.htm                         ║
║  2. Under "May 2025", download "All data" (XLSX format)                ║
║     - Or go to: https://www.bls.gov/oes/special-requests/oesm25nat.zip║
║  3. Save/extract the file to:                                          ║
║     data_raw/oews/national_M2025_dl.xlsx                               ║
║                                                                        ║
║  The file should contain columns: OCC_CODE, OCC_TITLE, TOT_EMP,       ║
║  A_MEAN, A_MEDIAN, H_MEAN, etc.                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

OEWS_EXPECTED_PATH = DATA_RAW / "oews" / "national_M2025_dl.xlsx"


def sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(url: str, dest: Path, label: str) -> bool:
    """Download a file, return True on success."""
    if dest.exists():
        log.info(f"  [skip] {label} already exists at {dest.name}")
        return True
    log.info(f"  [download] {label} ...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=120, stream=True)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        size_mb = dest.stat().st_size / 1e6
        log.info(f"  [done] {label} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        log.error(f"  [FAIL] {label}: {e}")
        if dest.exists():
            dest.unlink()
        return False


# ---------------------------------------------------------------------------
# Download functions
# ---------------------------------------------------------------------------
def download_onet() -> bool:
    """Download all O*NET 30.3 files."""
    log.info("=== O*NET 30.3 ===")
    onet_dir = DATA_RAW / "onet"
    onet_dir.mkdir(parents=True, exist_ok=True)
    ok = True
    for filename, url in ONET_FILES.items():
        if not download_file(url, onet_dir / filename, filename):
            ok = False
    return ok


def download_eloundou() -> bool:
    """Download Eloundou et al. occupation-level exposure data."""
    log.info("=== Eloundou et al. (theoretical exposure) ===")
    exp_dir = DATA_RAW / "exposure"
    exp_dir.mkdir(parents=True, exist_ok=True)
    return download_file(
        ELOUNDOU_URL, exp_dir / "occ_level.csv", "occ_level.csv"
    )


def download_aei() -> bool:
    """Download Anthropic Economic Index files via huggingface_hub."""
    log.info("=== Anthropic Economic Index ===")
    aei_dir = DATA_RAW / "aei"
    aei_dir.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download

        for fname in ["job_exposure.csv", "task_penetration.csv"]:
            dest = aei_dir / fname
            if dest.exists():
                log.info(f"  [skip] {fname} already exists")
                continue
            log.info(f"  [download] {fname} via huggingface_hub ...")
            path = hf_hub_download(
                repo_id="Anthropic/EconomicIndex",
                repo_type="dataset",
                filename=f"labor_market_impacts/{fname}",
                local_dir=str(aei_dir),
            )
            # hf_hub_download stores in a subdirectory; move to expected location
            downloaded = Path(path)
            if downloaded != dest:
                downloaded.rename(dest)
            log.info(f"  [done] {fname}")
        return True
    except Exception as e:
        log.error(f"  [FAIL] AEI download: {e}")
        return False


def check_bls() -> bool:
    """Check if BLS OEWS file exists (manual download required)."""
    log.info("=== BLS OEWS May 2025 ===")
    # Also check for common alternate names
    candidates = [
        OEWS_EXPECTED_PATH,
        DATA_RAW / "oews" / "national_M2025_dl.csv",
        DATA_RAW / "oews" / "oesm25nat.zip",
    ]
    for p in candidates:
        if p.exists():
            log.info(f"  [found] {p.name}")
            return True

    # Check if any file exists in oews/
    oews_dir = DATA_RAW / "oews"
    oews_dir.mkdir(parents=True, exist_ok=True)
    existing = list(oews_dir.glob("*"))
    existing = [f for f in existing if f.name != ".gitkeep"]
    if existing:
        log.info(f"  [found] {existing[0].name} (non-standard name)")
        return True

    log.warning("  BLS OEWS file not found.")
    print(BLS_MANUAL_INSTRUCTIONS)
    return False


# ---------------------------------------------------------------------------
# Update SOURCES.md with checksums
# ---------------------------------------------------------------------------
def update_sources_md():
    """Rewrite SOURCES.md with actual checksums and download dates."""
    log.info("=== Updating SOURCES.md ===")
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Data Sources Manifest\n",
        "",
        "> Every dataset used in this project is listed here with its exact URL,",
        "> release/version, download date, license, and SHA-256 checksum.",
        "",
        "---",
        "",
        "## O*NET 30.3",
        "",
        "- **Source:** https://www.onetcenter.org/database.html",
        "- **Version:** 30.3 (production release, pinned)",
        "- **License:** CC-BY 4.0 (Creative Commons Attribution)",
        "- **Files:**",
    ]

    onet_dir = DATA_RAW / "onet"
    for filename, url in ONET_FILES.items():
        filepath = onet_dir / filename
        if filepath.exists():
            checksum = sha256(filepath)
            lines.append(
                f"  - [x] {filename} — URL: `{url}` | "
                f"SHA-256: `{checksum}` | Downloaded: `{today}`"
            )
        else:
            lines.append(
                f"  - [ ] {filename} — URL: `{url}` | SHA-256: `TBD` | Downloaded: `TBD`"
            )

    lines.extend([
        "",
        "## BLS OEWS (May 2025)",
        "",
        "- **Source:** https://www.bls.gov/oes/tables.htm",
        "- **Bulk archive:** https://www.bls.gov/oes/special-requests/oesm25nat.zip",
        "- **Reference period:** May 2025 (survey reference month)",
        "- **Release date:** 2026-05-15 (BLS announcement)",
        "- **License:** Public domain (U.S. Government work)",
        "- **Files:**",
    ])

    oews_files = list((DATA_RAW / "oews").glob("*"))
    oews_files = [f for f in oews_files if f.name != ".gitkeep"]
    if oews_files:
        for f in oews_files:
            checksum = sha256(f)
            lines.append(
                f"  - [x] {f.name} — URL: `https://www.bls.gov/oes/special-requests/oesm25nat.zip` "
                f"(extracted from `oesm25nat.zip`) | Reference period: May 2025 | "
                f"SHA-256: `{checksum}` | Downloaded: `{today}`"
            )
    else:
        lines.append(
            "  - [ ] national_M2025_dl.xlsx — Manual download required from "
            "`https://www.bls.gov/oes/special-requests/oesm25nat.zip` | "
            "SHA-256: `TBD` | Downloaded: `TBD`"
        )

    lines.extend([
        "",
        "## Anthropic Economic Index",
        "",
        "- **Source:** https://huggingface.co/datasets/Anthropic/EconomicIndex",
        "- **Release:** labor_market_impacts (occupation + task exposure scores)",
        "- **License:** CC-BY 4.0",
        "- **Files:**",
    ])

    aei_dir = DATA_RAW / "aei"
    for fname in ["job_exposure.csv", "task_penetration.csv"]:
        filepath = aei_dir / fname
        if filepath.exists():
            checksum = sha256(filepath)
            lines.append(
                f"  - [x] {fname} — SHA-256: `{checksum}` | Downloaded: `{today}`"
            )
        else:
            lines.append(
                f"  - [ ] {fname} — SHA-256: `TBD` | Downloaded: `TBD`"
            )

    lines.extend([
        "",
        "## Eloundou et al. (2024) — Theoretical Exposure",
        "",
        "- **Paper:** GPTs are GPTs, Science 384:1306-1308 (2024)",
        "- **Source repo:** https://github.com/OPENAI/gpts-are-gpts",
        "- **License:** Public (academic repo)",
        "- **Files:**",
    ])

    eloundou_path = DATA_RAW / "exposure" / "occ_level.csv"
    if eloundou_path.exists():
        checksum = sha256(eloundou_path)
        lines.append(
            f"  - [x] occ_level.csv — URL: `{ELOUNDOU_URL}` | "
            f"SHA-256: `{checksum}` | Downloaded: `{today}`"
        )
    else:
        lines.append(
            f"  - [ ] occ_level.csv — URL: `{ELOUNDOU_URL}` | "
            f"SHA-256: `TBD` | Downloaded: `TBD`"
        )

    lines.extend([
        "",
        "## Felten/Raj/Seamans AIOE (Optional — Robustness)",
        "",
        "- **Paper:** SMJ 2021",
        "- **Status:** Deferred (robustness check only)",
        "- **Files:**",
        "  - [ ] AIOE_DataAppendix.xlsx — SHA-256: `TBD` | Downloaded: `TBD`",
    ])

    sources_path = DATA_RAW / "SOURCES.md"
    sources_path.write_text("\n".join(lines) + "\n")
    log.info(f"  SOURCES.md updated at {sources_path}")


# ---------------------------------------------------------------------------
# Load raw data into DuckDB
# ---------------------------------------------------------------------------
def load_into_duckdb():
    """Load all downloaded raw files into DuckDB as raw_* tables."""
    log.info("=== Loading raw data into DuckDB ===")
    WAREHOUSE.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    # --- O*NET ---
    onet_dir = DATA_RAW / "onet"

    # (table_name, filename, header_row)
    # Most O*NET Excel files have headers in row 0; the SOC crosswalk has 3
    # preamble rows before the actual header.
    onet_excel_tables = [
        ("raw_onet_task_statements", "Task Statements.xlsx", 0),
        ("raw_onet_task_ratings", "Task Ratings.xlsx", 0),
        ("raw_onet_occupation_data", "Occupation Data.xlsx", 0),
        ("raw_onet_work_activities", "Work Activities.xlsx", 0),
        ("raw_onet_tasks_to_dwas", "Tasks to DWAs.xlsx", 0),
        ("raw_onet_gwas_to_iwas_to_dwas", "GWAs to IWAs to DWAs.xlsx", 0),
        ("raw_onet_job_zones", "Job Zones.xlsx", 0),
        ("raw_onet_soc_crosswalk", "2019_to_SOC_Crosswalk.xlsx", 3),
    ]

    for table_name, filename, header_row in onet_excel_tables:
        filepath = onet_dir / filename
        if not filepath.exists():
            log.warning(f"  [skip] {filename} not found")
            continue
        try:
            df = pd.read_excel(filepath, header=header_row)
            # Normalize column names: lowercase, replace spaces with underscores
            df.columns = [c.strip().lower().replace(" ", "_").replace("*", "")
                          .replace("-", "_") for c in df.columns]
            # Drop any fully-null rows (from preamble)
            df = df.dropna(how="all")
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            log.info(f"  [loaded] {table_name}: {len(df):,} rows, {len(df.columns)} cols")
        except Exception as e:
            log.error(f"  [FAIL] loading {filename}: {e}")

    # --- BLS OEWS ---
    oews_dir = DATA_RAW / "oews"
    oews_files = [f for f in oews_dir.glob("*.xlsx") if f.name != ".gitkeep"]
    if not oews_files:
        oews_files = [f for f in oews_dir.glob("*.csv") if f.name != ".gitkeep"]

    if oews_files:
        filepath = oews_files[0]
        try:
            if filepath.suffix == ".xlsx":
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            con.execute("DROP TABLE IF EXISTS raw_oews")
            con.execute("CREATE TABLE raw_oews AS SELECT * FROM df")
            log.info(f"  [loaded] raw_oews: {len(df):,} rows, {len(df.columns)} cols")
        except Exception as e:
            log.error(f"  [FAIL] loading OEWS: {e}")
    else:
        log.warning("  [skip] No OEWS file found — download manually first")

    # --- AEI ---
    aei_dir = DATA_RAW / "aei"

    for fname, table_name in [
        ("job_exposure.csv", "raw_aei_job_exposure"),
        ("task_penetration.csv", "raw_aei_task_penetration"),
    ]:
        filepath = aei_dir / fname
        if not filepath.exists():
            log.warning(f"  [skip] {fname} not found")
            continue
        try:
            df = pd.read_csv(filepath)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            con.execute(f"DROP TABLE IF EXISTS {table_name}")
            con.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")
            log.info(f"  [loaded] {table_name}: {len(df):,} rows, {len(df.columns)} cols")
        except Exception as e:
            log.error(f"  [FAIL] loading {fname}: {e}")

    # --- Eloundou ---
    eloundou_path = DATA_RAW / "exposure" / "occ_level.csv"
    if eloundou_path.exists():
        try:
            df = pd.read_csv(eloundou_path)
            df.columns = [c.strip().lower().replace(" ", "_").replace("*", "")
                          .replace("-", "_") for c in df.columns]
            con.execute("DROP TABLE IF EXISTS raw_eloundou")
            con.execute("CREATE TABLE raw_eloundou AS SELECT * FROM df")
            log.info(f"  [loaded] raw_eloundou: {len(df):,} rows, {len(df.columns)} cols")
        except Exception as e:
            log.error(f"  [FAIL] loading Eloundou: {e}")
    else:
        log.warning("  [skip] Eloundou occ_level.csv not found")

    # --- Summary ---
    tables = con.execute(
        "SELECT table_name, estimated_size "
        "FROM duckdb_tables() ORDER BY table_name"
    ).fetchall()
    log.info("=== DuckDB tables ===")
    for name, size in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        log.info(f"  {name}: {count:,} rows")

    con.close()
    log.info(f"Database: {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Download and load raw data sources")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloads, only load existing files into DuckDB",
    )
    args = parser.parse_args()

    if not args.skip_download:
        log.info("Starting data acquisition...")
        results = {}
        results["onet"] = download_onet()
        results["eloundou"] = download_eloundou()
        results["aei"] = download_aei()
        results["bls"] = check_bls()

        update_sources_md()

        failed = [k for k, v in results.items() if not v]
        if failed:
            log.warning(f"Some sources need attention: {', '.join(failed)}")
            if "bls" in failed:
                log.warning(
                    "BLS OEWS requires manual download. "
                    "The pipeline will proceed without it but the mart will be incomplete."
                )

    load_into_duckdb()
    log.info("Done.")


if __name__ == "__main__":
    main()
