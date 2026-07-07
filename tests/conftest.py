"""
Test configuration.

The integration tests in test_crosswalk.py need the DuckDB warehouse
(warehouse/aei.duckdb), which is built by `make download build` from
data that is not tracked in git. When the warehouse is missing (e.g.
in CI without the raw data), those tests are skipped so the suite still
runs the pure-function tests in test_crosswalk_pure.py.
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "warehouse" / "aei.duckdb"


def pytest_collection_modifyitems(config, items):
    if DB_PATH.exists():
        return
    skip_marker = pytest.mark.skip(
        reason=f"warehouse not built ({DB_PATH.name} missing); "
        "run `make download build` to enable integration tests"
    )
    for item in items:
        if item.module.__name__ == "test_crosswalk":
            item.add_marker(skip_marker)
