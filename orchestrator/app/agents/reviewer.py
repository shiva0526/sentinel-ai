"""
reviewer.py — Handles human review and approval for deployment.
"""

from ..graph.state import WarRoomState

def reviewer_agent(state: WarRoomState):
    print("\n[!] REVIEW REQUIRED: A secure patch has been generated and validated.")
    print(f"    Vulnerability: {state.get('cve_id')}")
    print(f"    File: {state.get('vulnerable_file')}")
    print("\n--- Proposed Patch ---")
    print(state.get('proposed_patch'))
    print("----------------------")
    
    # In a real LangGraph HIL system, we would interrupt here.
    # For now, we will provide the state and expect deployment_approved to be set.
    return {"deployment_approved": None} # None indicates "pending"
