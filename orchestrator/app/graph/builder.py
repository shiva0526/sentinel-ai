"""
builder.py — Constructs and compiles the LangGraph workflow.
"""

from langgraph.graph import StateGraph, END

from .state import WarRoomState
from .edges import check_sandbox_results, check_approval
from ..agents.hunter import hunter_agent
from ..agents.triage import triage_agent
from ..agents.mechanic import mechanic_agent
from ..agents.hacker import hacker_agent
from ..agents.validator import validator_agent
from ..agents.reviewer import reviewer_agent
from ..agents.deployer import deployer_agent
from ..agents.cleanup import cleanup_agent


def build_pipeline(checkpointer=None):
    """Build and compile the SentinelAI LangGraph workflow.

    Returns:
        Compiled LangGraph application ready for .invoke()
    """
    workflow = StateGraph(WarRoomState)

    # Register nodes
    workflow.add_node("Hunter", hunter_agent)
    workflow.add_node("Triage", triage_agent)
    workflow.add_node("Mechanic", mechanic_agent)
    workflow.add_node("Hacker", hacker_agent)
    workflow.add_node("Validator", validator_agent)
    workflow.add_node("Review", reviewer_agent)
    workflow.add_node("Deployer", deployer_agent)
    workflow.add_node("Cleanup", cleanup_agent)

    # Define edges
    workflow.set_entry_point("Hunter")
    workflow.add_edge("Hunter", "Triage")
    workflow.add_edge("Triage", "Mechanic")
    workflow.add_edge("Mechanic", "Hacker")
    workflow.add_edge("Hacker", "Validator")

    # Conditional: retry on failure or go to review
    workflow.add_conditional_edges(
        "Validator",
        check_sandbox_results,
        {"review": "Review", "retry": "Mechanic"},
    )

    # Conditional: push to GitHub if approved
    workflow.add_conditional_edges(
        "Review",
        check_approval,
        {"deploy": "Deployer", "end": "Cleanup"},
    )

    workflow.add_edge("Deployer", "Cleanup")
    workflow.add_edge("Cleanup", END)

    return workflow.compile(checkpointer=checkpointer, interrupt_after=["Review"])
