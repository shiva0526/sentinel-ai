"""
test_detector.py — Unit tests for the SentinelAI detection engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sentinel_core import DetectorService


def test_sql_injection():
    svc = DetectorService()
    findings = svc.detect("user_id = input()\nquery = 'SELECT * FROM users WHERE id = ' + user_id\nexecute(query)")
    types = [f.vuln_type for f in findings]
    assert "SQL Injection" in types, f"Expected SQL Injection, got {types}"
    print("  [PASS] SQL Injection detected")


def test_command_injection():
    svc = DetectorService()
    findings = svc.detect("import os\ncmd = input()\nos.system(cmd)")
    types = [f.vuln_type for f in findings]
    assert "Command Injection" in types, f"Expected Command Injection, got {types}"
    print("  [PASS] Command Injection detected")


def test_code_injection():
    svc = DetectorService()
    findings = svc.detect("expr = input()\neval(expr)")
    types = [f.vuln_type for f in findings]
    assert "Code Injection" in types, f"Expected Code Injection, got {types}"
    print("  [PASS] Code Injection detected")


def test_hardcoded_secret():
    svc = DetectorService()
    findings = svc.detect('api_key = "AIzaSyBzRg7rlHVi43nsSOo2maVOpvM2N1g_9Ps"')
    types = [f.vuln_type for f in findings]
    assert "Hardcoded Secret" in types, f"Expected Hardcoded Secret, got {types}"
    print("  [PASS] Hardcoded Secret detected")


def test_safe_code():
    svc = DetectorService()
    findings = svc.detect("def add(a, b):\n    return a + b\nresult = add(1, 2)")
    assert len(findings) == 0, f"Expected 0 findings on safe code, got {len(findings)}"
    print("  [PASS] Safe code returns zero findings")


def test_detector_service_interface():
    svc = DetectorService()
    # Test with a code pattern where input is assigned first
    assert svc.has_findings("x = input()\neval(x)")
    assert not svc.has_findings("print('hello')")
    findings = svc.detect("x = input()\neval(x)")
    assert svc.get_primary_cwe(findings) == "CWE-94"
    print("  [PASS] DetectorService interface works")


def test_json_output():
    svc = DetectorService()
    json_str = svc.detect_json("x = input()\neval(x)")
    assert '"CWE-94"' in json_str
    print("  [PASS] JSON output contains CWE-94")


def test_llm_format():
    svc = DetectorService()
    findings = svc.detect("x = input()\neval(x)")
    prompt = svc.format_for_llm(findings)
    assert "Code Injection" in prompt
    assert "CWE-94" in prompt
    print("  [PASS] LLM format contains structured data")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Sentinel Core - Detection Engine Tests")
    print("=" * 50 + "\n")

    tests = [
        test_sql_injection,
        test_command_injection,
        test_code_injection,
        test_hardcoded_secret,
        test_safe_code,
        test_detector_service_interface,
        test_json_output,
        test_llm_format,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] {test_fn.__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}\n")
    sys.exit(1 if failed > 0 else 0)
