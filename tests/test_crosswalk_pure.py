"""
Pure-function tests for the O*NET-SOC → 6-digit SOC crosswalk.

These tests exercise map_onet_to_soc against a synthetic in-memory
crosswalk. They run in CI without needing the warehouse to be built.
The integration tests in test_crosswalk.py cover the real data.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from crosswalk import map_onet_to_soc  # noqa: E402


def _synthetic_crosswalk() -> pd.DataFrame:
    """A tiny crosswalk covering the shapes the mapper must handle:
    - many-to-one collapse (15-1252.00/.01/.02 → 15-1252)
    - single-variant SOC (29-1141.00 → 29-1141)
    """
    return pd.DataFrame(
        {
            "onet_soc_code": [
                "11-1011.00",
                "15-1252.00",
                "15-1252.01",
                "15-1252.02",
                "29-1141.00",
            ],
            "soc_code": [
                "11-1011",
                "15-1252",
                "15-1252",
                "15-1252",
                "29-1141",
            ],
            "onet_title": ["Chief Executives", "SW Dev", "SW Dev A", "SW Dev B", "RN"],
            "soc_title": ["Chief Executives", "SW Dev", "SW Dev", "SW Dev", "RN"],
        }
    )


class TestMapOnetToSoc:
    def test_maps_official_codes(self):
        xwalk = _synthetic_crosswalk()
        result = map_onet_to_soc(["29-1141.00", "11-1011.00"], xwalk)
        assert result == {"29-1141.00": "29-1141", "11-1011.00": "11-1011"}

    def test_collapses_many_to_one(self):
        xwalk = _synthetic_crosswalk()
        result = map_onet_to_soc(
            ["15-1252.00", "15-1252.01", "15-1252.02"], xwalk
        )
        assert set(result.values()) == {"15-1252"}

    def test_falls_back_to_naive_truncation_for_unknown(self, caplog):
        xwalk = _synthetic_crosswalk()
        # 99-9999.00 is not in the synthetic crosswalk
        result = map_onet_to_soc(["99-9999.00"], xwalk)
        assert result == {"99-9999.00": "99-9999"}
        assert any(
            "not in official crosswalk" in rec.message for rec in caplog.records
        )

    def test_preserves_all_inputs(self):
        xwalk = _synthetic_crosswalk()
        inputs = ["11-1011.00", "15-1252.01", "99-9999.00"]
        result = map_onet_to_soc(inputs, xwalk)
        assert list(result.keys()) == inputs

    def test_strips_whitespace(self):
        xwalk = _synthetic_crosswalk()
        result = map_onet_to_soc(["  11-1011.00  "], xwalk)
        assert result == {"11-1011.00": "11-1011"}

    def test_soc_output_is_7_chars(self):
        xwalk = _synthetic_crosswalk()
        result = map_onet_to_soc(["11-1011.00", "29-1141.00"], xwalk)
        for soc in result.values():
            assert len(soc) == 7, f"Expected 7-char SOC, got '{soc}'"
