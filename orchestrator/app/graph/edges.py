"""
edges.py — Conditional routing logic for the LangGraph pipeline.
"""

from .state import WarRoomState


def check_sandbox_results(state: WarRoomState) -> str:
    """Route based on sandbox test results: pass → review, fail → retry."""
    if state.get("test_status") in ["PASS", "PARTIAL_SUCCESS"]:
        return "review"
    return "retry"


def check_approval(state: WarRoomState) -> str:
    """Check if the user approved the deployment."""
    if state.get("deployment_approved") is True:
        return "deploy"
    return "end"


def check_hunter_mode(state: WarRoomState) -> str:
    """Route after Hunter based on the resolved scan mode.

    Priority: explicit scan_mode > adaptive_mode (auto-detected).
    If Hunter failed, route to end.
    """
    if state.get("test_status") == "FAIL":
        return "end"

    scan_mode = state.get("scan_mode", "auto")
    adaptive_mode = state.get("adaptive_mode")

    # Explicit detect_only always wins
    if scan_mode == "detect_only":
        return "end"

    # Explicit full always wins
    if scan_mode == "full":
        return "triage"

    # Auto mode: use the adaptive decision
    if adaptive_mode == "detect_only":
        return "end"

    return "triage"

