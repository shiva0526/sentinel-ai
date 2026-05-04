"""
state.py — WarRoomState definition for the LangGraph pipeline.
"""

from typing import TypedDict, Optional


class WarRoomState(TypedDict):
    repo_url: str
    cve_id: Optional[str]
    vulnerable_file: Optional[str]
    original_code: Optional[str]
    ast_graph: Optional[str]
    repo_path: Optional[str]
    proposed_patch: Optional[str]
    exploit_payload: Optional[str]
    test_logs: Optional[str]
    test_status: Optional[str]
    deployment_approved: Optional[bool]
    iterations: int
