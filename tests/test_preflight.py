import pytest
from agent_lens.core.preflight import PreflightChecker


def test_python_preflight_syntax_error():
    broken_code = """
def broken_fn(a, b):
    print("Missing closing bracket"
"""
    res = PreflightChecker.check_file("broken.py", content=broken_code)
    assert res["valid"] is False
    assert len(res["errors"]) > 0
    assert "SyntaxError" in res["errors"][0]


def test_python_preflight_valid():
    valid_code = """
import os

def clean_fn():
    return os.getcwd()
"""
    res = PreflightChecker.check_file("valid.py", content=valid_code)
    assert res["valid"] is True
    assert len(res["errors"]) == 0


def test_git_conflict_detection():
    conflict_code = """
def calculate():
<<<<<<< HEAD
    return 100
=======
    return 200
>>>>>>> branch-b
"""
    res = PreflightChecker.check_file("conflict.py", content=conflict_code)
    assert res["valid"] is False
    assert any("Git conflict marker" in e for e in res["errors"])


def test_json_preflight():
    valid_json = '{"name": "AgentLens", "version": "1.0.0"}'
    res = PreflightChecker.check_file("test.json", content=valid_json)
    assert res["valid"] is True

    invalid_json = '{"name": "AgentLens", trailing: }'
    res_bad = PreflightChecker.check_file("test.json", content=invalid_json)
    assert res_bad["valid"] is False
