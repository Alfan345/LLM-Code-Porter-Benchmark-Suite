"""
test_verifier.py

Hint: start with the SIMPLEST possible cases before edge cases:
1. Two identical string outputs -> should pass
2. Two clearly different outputs -> should fail
3. Two numerically-close-but-not-identical outputs (like "3.14159" vs "3.14158") ->
   should pass IF within tolerance, fail if tolerance is too strict

Use pytest's plain `assert` statements (no need for unittest.TestCase classes).
Name each test function `test_<what_it_checks>` so pytest auto-discovers it.
"""

import pytest
from verifier import extract_numbers, compare_outputs, run_python

def test_extract_numbers_standard():
    """Extract integers and floats from a mixed string."""
    text = "Nilai pi adalah 3.14 dalam waktu 2 detik"
    assert extract_numbers(text) == [3.14, 2.0]

def test_extract_numbers_negative():
    """Extract negative numbers."""
    text = "Suhu: -15.5 derajat"
    assert extract_numbers(text) == [-15.5]

def test_extract_numbers_scientific():
    """Extract scientific notation values."""
    text = "Loss value: 1.5e-5 dan 1.5E3"
    assert extract_numbers(text) == [0.000015, 1500.0]

def test_extract_numbers_empty():
    """Return an empty list when no numbers are present."""
    text = "Tidak ada angka di sini"
    assert extract_numbers(text) == []


def test_compare_identical_strings():
    """Exact string matches should pass."""
    assert compare_outputs("Hello World", "Hello World") == {"passed": True, "reason": ""}

def test_compare_different_strings():
    """Different strings without numbers should fail."""
    result = compare_outputs("Success", "Failed")
    assert result["passed"] is False
    assert "Exact string mismatch" in result["reason"]

def test_compare_numeric_within_tolerance():
    """Close numeric values should pass within tolerance."""
    result = compare_outputs("Pi: 3.14159", "Pi: 3.14158", tolerance=1e-4)
    assert result["passed"] is True
    assert "within tolerance" in result["reason"]

def test_compare_numeric_outside_tolerance():
    """Numeric values outside tolerance should fail."""
    result = compare_outputs("Result: 10.5", "Result: 10.8", tolerance=0.1)
    assert result["passed"] is False
    assert "tolerance check failed" in result["reason"]

def test_compare_number_count_mismatch():
    """Mismatched number counts should fail."""
    result = compare_outputs("1.0 2.0", "1.0", tolerance=0.1)
    assert result["passed"] is False
    assert "Number count mismatch" in result["reason"]

def test_compare_tolerance_no_numbers():
    """Tolerance mode should fail when no numbers are present."""
    result = compare_outputs("abc", "def", tolerance=0.1)
    assert result["passed"] is False
    assert "doesn't contain any numbers" in result["reason"]


def test_run_python_success():
    """Running valid Python code should capture stdout."""
    code = "print('Hello dari Python')"
    result = run_python(code)
    
    assert result["success"] is True
    assert result["stdout"].strip() == "Hello dari Python"
    assert result["stderr"] == ""

def test_run_python_crash():
    """Exceptions should be captured instead of crashing the test."""
    code = "print(1 / 0)"
    result = run_python(code)
    
    assert result["success"] is False
    assert result["stdout"] == ""
    assert "ZeroDivisionError" in result["stderr"]
    assert "Traceback" in result["stderr"]