"""
cleanup.py — Final cleanup agent.
"""

from ..graph.state import WarRoomState
from ..services.repo_service import cleanup_repo

def cleanup_agent(state: WarRoomState):
    repo_path = state.get("repo_path")
    if repo_path:
        print(f"\n[6] Cleanup Agent: Removing temporary repository at {repo_path}")
        cleanup_repo(repo_path)
    return {"repo_path": None}
