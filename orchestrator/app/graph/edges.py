"""
edges.py — Conditional routing logic for the LangGraph pipeline.
"""

from .state import WarRoomState


def check_sandbox_results(state: WarRoomState) -> str:
    """Route based on sandbox test results: pass → review, fail → retry."""
    if state["test_status"] in ["PASS", "PARTIAL_SUCCESS"]:
        return "review"
    return "retry"


def check_approval(state: WarRoomState) -> str:
    """Check if the user approved the deployment."""
    if state.get("deployment_approved") is True:
        return "deploy"
    return "end"

