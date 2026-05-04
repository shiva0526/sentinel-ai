"""
test_pipeline.py — Integration test for the orchestrator pipeline.
"""

import requests
import sys


def test_health():
    """Test that the orchestrator is running."""
    try:
        resp = requests.get("http://localhost:8000/health", timeout=5)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        print("  [PASS] Health check")
    except Exception as e:
        print(f"  [FAIL] Health check: {e}")
        return False
    return True


def test_hunt_endpoint():
    """Test the /hunt endpoint with a simulated repo URL."""
    try:
        resp = requests.post(
            "http://localhost:8000/hunt",
            json={"repo_url": "https://example.com/test"},
            timeout=120,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "vulnerability_found" in data
        print(f"  [PASS] Hunt endpoint — found: {data.get('vulnerability_found')}")
    except Exception as e:
        print(f"  [FAIL] Hunt endpoint: {e}")
        return False
    return True


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Orchestrator Integration Tests")
    print("=" * 50 + "\n")

    results = [test_health(), test_hunt_endpoint()]
    passed = sum(results)
    total = len(results)

    print(f"\n{'=' * 50}")
    print(f"  Results: {passed}/{total} passed")
    print(f"{'=' * 50}\n")

    sys.exit(0 if all(results) else 1)
