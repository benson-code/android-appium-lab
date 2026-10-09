"""Data-driven cases from testdata/cases/*.csv: one row per case; case_id, marks and is_run are data."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

CASES_DIR = Path(__file__).resolve().parent / "cases"


def load(filename: str) -> list:
    out = []
    with (CASES_DIR / filename).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["is_run"].strip().upper() != "Y":
                continue
            marks = [getattr(pytest.mark, m) for m in row["marks"].split("|") if m]
            out.append(pytest.param(row, id=row["case_id"], marks=marks))
    return out
