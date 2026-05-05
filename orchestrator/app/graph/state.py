"""
state.py — WarRoomState definition for the LangGraph pipeline.
"""

from typing import TypedDict, Optional, List, Dict, Any


class WarRoomState(TypedDict):
    repo_url: str
    scan_mode: Optional[str]
    adaptive_mode: Optional[str]
    repo_stats: Optional[Dict[str, Any]]
    vulnerabilities: Optional[List[Dict[str, Any]]]
    total_vulnerabilities: Optional[int]
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
    patched_files: Optional[int]
    pr_url: Optional[str]
    iterations: int
