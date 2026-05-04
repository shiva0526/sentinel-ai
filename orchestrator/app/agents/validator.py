"""
validator.py — Sandbox Referee Agent.

Sends the Blue Team patch + Red Team exploit to the Go Arena
and interprets the results.
"""

from ..graph.state import WarRoomState
from ..services.arena_client import execute_in_sandbox
from ..services.execution_builder import build_combined_app

MAX_ITERATIONS = 3

def validator_agent(state: WarRoomState):
    print("\n[4] Validator: Sending to Arena sandbox...")
    iters = state.get("iterations", 0) + 1

    if iters > MAX_ITERATIONS:
        print(f"    [!] MAX ITERATIONS ({MAX_ITERATIONS}) EXCEEDED. Halting loop.")
        return {
            "test_status": "PARTIAL_SUCCESS",
            "iterations": iters,
            "test_logs": "Max iterations reached. Proceeding with best patch.",
        }

    try:
        # Wrap the patch and exploit into a single runnable app
        combined_code = build_combined_app(state["proposed_patch"], state["exploit_payload"])

        result = execute_in_sandbox(
            combined_code=combined_code,
        )

        reason = result.get("reason", "UNKNOWN")

        if reason == "EXPLOIT_FAILED":
            print("    [+] PASS: The patch held! Exploit failed.")
            return {
                "test_status": "PASS",
                "iterations": iters,
                "test_logs": "Exploit successfully blocked.",
            }
        elif reason == "EXPLOIT_SUCCESS":
            print("    [-] FAIL: The exploit broke the patch!")
            return {
                "test_status": "FAIL",
                "iterations": iters,
                "test_logs": "EXPLOIT_SUCCESS detected in stdout. The patch was bypassed.",
            }
        elif reason == "RUNTIME_ERROR":
            print("    [-] FAIL: The patched code crashed!")
            return {
                "test_status": "FAIL",
                "iterations": iters,
                "test_logs": f"RUNTIME_ERROR:\n{result.get('error', 'Unknown runtime error')}",
            }
        else:
            print(f"    [-] FAIL: Sandbox returned reason: {reason}")
            return {
                "test_status": "FAIL",
                "iterations": iters,
                "test_logs": f"Sandbox Reason: {reason}\nStdout: {result.get('output')}\nStderr: {result.get('error')}",
            }

    except Exception as e:
        print(f"    [!] Arena connection failed: {e}")
        return {
            "test_status": "FAIL",
            "iterations": iters,
            "test_logs": str(e),
        }

