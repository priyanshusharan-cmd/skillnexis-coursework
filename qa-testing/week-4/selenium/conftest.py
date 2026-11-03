"""Reuse the week 3 fixtures and page objects so both weeks run against the same framework."""
import importlib.util
import sys
from pathlib import Path

WEEK3 = Path(__file__).resolve().parents[2] / "week-3" / "selenium"
sys.path.insert(0, str(WEEK3))  # makes `import pages` work

_spec = importlib.util.spec_from_file_location("week3_conftest", WEEK3 / "conftest.py")
_w3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w3)

base_url = _w3.base_url
driver = _w3.driver
pytest_runtest_makereport = _w3.pytest_runtest_makereport
