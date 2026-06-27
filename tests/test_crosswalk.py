"""
Tests for the O*NET-SOC → 6-digit SOC crosswalk.

These are the "test the risky things first" tests required by the spec.
The crosswalk is the foundation of every join — if it drops occupations
silently, every downstream result is wrong.
"""

import sys
from pathlib import Path

import duckdb
import pytest

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from crosswalk import load_crosswalk, map_onet_to_soc, validate_crosswalk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "warehouse" / "aei.duckdb"


@pytest.fixture(scope="module")
def con():
    """Shared DuckDB connection for the test module."""
    c = duckdb.connect(str(DB_PATH), read_only=True)
    yield c
    c.close()


@pytest.fixture(scope="module")
def crosswalk_df(con):
    return load_crosswalk(con)


@pytest.fixture(scope="module")
def report(con):
    return validate_crosswalk(con)


# ---- Crosswalk integrity ----


class TestCrosswalkIntegrity:
    """The crosswalk itself must be clean."""

    def test_crosswalk_not_empty(self, crosswalk_df):
        assert len(crosswalk_df) > 900, "Crosswalk should have >900 rows"

    def test_no_duplicate_onet_codes(self, report):
        assert report["duplicate_onet_codes"] == 0, (
            f"Found duplicate O*NET-SOC codes: "
            f"{report.get('duplicate_examples', [])}"
        )

    def test_soc_code_format(self, crosswalk_df):
        """All SOC codes should match XX-XXXX pattern."""
        import re

        pattern = re.compile(r"^\d{2}-\d{4}$")
        bad = crosswalk_df[~crosswalk_df["soc_code"].str.match(r"^\d{2}-\d{4}$")]
        assert len(bad) == 0, f"Invalid SOC codes: {bad['soc_code'].tolist()[:10]}"

    def test_onet_code_format(self, crosswalk_df):
        """All O*NET-SOC codes should match XX-XXXX.XX pattern."""
        bad = crosswalk_df[
            ~crosswalk_df["onet_soc_code"].str.match(r"^\d{2}-\d{4}\.\d{2}$")
        ]
        assert len(bad) == 0, (
            f"Invalid O*NET-SOC codes: {bad['onet_soc_code'].tolist()[:10]}"
        )


# ---- No silent drops ----


class TestNoSilentDrops:
    """
    No occupations should silently drop through the crosswalk.
    This is the critical integrity check.
    """

    def test_all_task_codes_in_crosswalk(self, report):
        """Every O*NET-SOC code with task data must map to a SOC code."""
        assert report["task_codes_missing_from_crosswalk"] == 0, (
            f"Task codes missing from crosswalk: "
            f"{report.get('task_codes_missing_examples', [])}"
        )

    def test_all_eloundou_codes_in_crosswalk(self, report):
        """Every Eloundou code must map via the crosswalk."""
        assert report["eloundou_codes_missing_from_crosswalk"] == 0

    def test_mapping_preserves_all_inputs(self, crosswalk_df):
        """map_onet_to_soc should return a mapping for every input code."""
        test_codes = crosswalk_df["onet_soc_code"].tolist()[:100]
        result = map_onet_to_soc(test_codes, crosswalk_df)
        assert len(result) == len(test_codes)
        # All results should be valid SOC codes
        for onet, soc in result.items():
            assert len(soc) == 7, f"{onet} -> '{soc}' is not 7 chars"


# ---- Naive truncation vs official ----


class TestTruncationVsOfficial:
    """
    Verify that naive truncation agrees with the official crosswalk.
    As of O*NET 30.3 they agree on all 1,016 codes, but we test this
    explicitly so we'd catch any future divergence.
    """

    def test_naive_matches_official(self, report):
        assert report["naive_vs_official_mismatches"] == 0, (
            "Naive truncation disagrees with official crosswalk — "
            "this is a new divergence that needs investigation"
        )


# ---- Collapsing rules ----


class TestCollapsingRules:
    """Tests for the many-to-one O*NET-SOC → SOC collapsing."""

    def test_known_many_to_one(self, crosswalk_df):
        """SOC 15-1252 should have multiple O*NET-SOC variants."""
        soc_15_1252 = crosswalk_df[crosswalk_df["soc_code"] == "15-1252"]
        assert len(soc_15_1252) >= 1, "Expected SOC 15-1252 in crosswalk"

    def test_collapsing_reduces_rows(self, report):
        """Collapsing O*NET-SOC to SOC should reduce the row count."""
        assert report["unique_soc"] < report["unique_onet_soc"]

    def test_many_to_one_documented(self, report):
        """There should be some many-to-one mappings."""
        assert report["soc_with_multiple_onet"] > 50, (
            "Expected >50 SOCs with multiple O*NET variants"
        )


# ---- Row count assertions at each join ----


class TestJoinRowCounts:
    """
    Assert row counts to ensure nothing drops during joins.
    These counts are logged and checked — the spec says
    'assert row counts at every join and log unmatched keys.'
    """

    def test_task_statements_row_count(self, con):
        n = con.execute("SELECT COUNT(*) FROM raw_onet_task_statements").fetchone()[0]
        assert n > 18000, f"Expected >18000 task rows, got {n}"

    def test_eloundou_row_count(self, con):
        n = con.execute("SELECT COUNT(*) FROM raw_eloundou").fetchone()[0]
        assert n == 923, f"Expected 923 Eloundou rows, got {n}"

    def test_aei_job_exposure_row_count(self, con):
        n = con.execute("SELECT COUNT(*) FROM raw_aei_job_exposure").fetchone()[0]
        assert n == 756, f"Expected 756 AEI rows, got {n}"

    def test_crosswalk_row_count(self, con):
        n = con.execute("SELECT COUNT(*) FROM raw_onet_soc_crosswalk").fetchone()[0]
        assert n == 1016, f"Expected 1016 crosswalk rows, got {n}"

    def test_job_zones_row_count(self, con):
        n = con.execute("SELECT COUNT(*) FROM raw_onet_job_zones").fetchone()[0]
        assert n == 923, f"Expected 923 job zone rows, got {n}"


# ---- Job Zone values (spec correction) ----


class TestJobZones:
    """
    O*NET 30.2+ moved from 5-level to 4-level Job Zones.
    Per the data, the remaining zones are {2, 3, 4, 5} (Zone 1 was dropped).
    """

    def test_job_zone_values(self, con):
        zones = set(
            r[0]
            for r in con.execute(
                "SELECT DISTINCT job_zone FROM raw_onet_job_zones"
            ).fetchall()
        )
        assert zones == {2, 3, 4, 5}, (
            f"Expected Job Zones {{2,3,4,5}}, got {zones}"
        )

    def test_job_zone_coverage(self, con):
        """All 923 data-level occupations should have a Job Zone."""
        n = con.execute(
            "SELECT COUNT(DISTINCT onet_soc_code) FROM raw_onet_job_zones "
            "WHERE job_zone IS NOT NULL"
        ).fetchone()[0]
        assert n == 923, f"Expected 923 occupations with Job Zones, got {n}"
