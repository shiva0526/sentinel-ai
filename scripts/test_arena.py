"""
test_arena.py — Quick connectivity test for the Go Arena sandbox.
"""

import requests
import sys


def test_arena():
    print("Testing Arena connectivity...")

    # Test /execute
    try:
        resp = requests.post("http://127.0.0.1:8080/execute", json={
            "language": "python",
            "app_code": "print('Hello from SentinelAI Arena!')",
            "exploit_payload": "raise Exception('BOOM! The exploit crashed the app!')",
        }, timeout=30)

        if resp.status_code == 200:
            result = resp.json()
            import json
            print(f"  [PASS] /execute — Result: {json.dumps(result, indent=2)}")
        else:
            print(f"  [FAIL] /execute — HTTP {resp.status_code}")
    except Exception as e:
        print(f"  [FAIL] /execute — {e}")

    # Test /search
    try:
        resp = requests.post("http://127.0.0.1:8080/search", json={
            "query": "CWE-89 SQL Injection",
        }, timeout=15)

        if resp.status_code == 200:
            print(f"  [PASS] /search — Got results")
        else:
            print(f"  [FAIL] /search — HTTP {resp.status_code}")
    except Exception as e:
        print(f"  [FAIL] /search — {e}")


if __name__ == "__main__":
    test_arena()
