import csv
import os
import tempfile
import pytest
from models.schemas import ResumeFile, ContactInfo, Scores, ResumeResult
from output.csv_writer import write_results_to_csv, CSV_COLUMNS


def make_result(name, total, error=None):
    scores_map = {100: Scores(25, 25, 25, 25), 80: Scores(20, 20, 20, 20), 60: Scores(15, 15, 15, 15)}
    s = scores_map.get(total, Scores())
    return ResumeResult(
        file=ResumeFile(f"id_{name}", f"{name}.pdf", "application/pdf", f"url_{name}"),
        contact=ContactInfo(name=name, email=f"{name}@test.com"),
        scores=s,
        error=error,
    )


def test_csv_writer_creates_file():
    results = [make_result("Alice", 80), make_result("Bob", 60)]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name
    try:
        write_results_to_csv(results, path)
        assert os.path.exists(path)
    finally:
        os.unlink(path)


def test_csv_writer_sorted_by_score():
    results = [make_result("Low", 60), make_result("High", 100), make_result("Mid", 80)]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    try:
        write_results_to_csv(results, path)
        with open(path) as f:
            reader = list(csv.DictReader(f))
        assert reader[0]["name"] == "High"
        assert reader[1]["name"] == "Mid"
        assert reader[2]["name"] == "Low"
    finally:
        os.unlink(path)


def test_csv_writer_correct_columns():
    results = [make_result("Alice", 80)]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    try:
        write_results_to_csv(results, path)
        with open(path) as f:
            reader = csv.DictReader(f)
            assert list(reader.fieldnames) == CSV_COLUMNS
    finally:
        os.unlink(path)


def test_csv_writer_error_column():
    results = [make_result("Broken", 0, error="Parse failed")]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        path = f.name
    try:
        write_results_to_csv(results, path)
        with open(path) as f:
            reader = list(csv.DictReader(f))
        assert reader[0]["error"] == "Parse failed"
    finally:
        os.unlink(path)
