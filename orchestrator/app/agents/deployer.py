"""
deployer.py — Pushes validated patches to GitHub.
"""

from ..graph.state import WarRoomState
from ..services.git_service import apply_patch_to_file, push_changes_to_github

def deployer_agent(state: WarRoomState):
    print("\n[5] Deployer Agent: Preparing to push code...")

    if not state.get("deployment_approved"):
        print("    [!] Deployment NOT approved by user. Skipping push.")
        return {"test_status": "SKIPPED_PUSH"}

    repo_path = state.get("repo_path")
    rel_file_path = state.get("vulnerable_file")
    original_code = state.get("original_code")
    proposed_patch = state.get("proposed_patch")
    repo_url = state.get("repo_url")

    if not all([repo_path, rel_file_path, original_code, proposed_patch]):
        print("    [!] Missing data for deployment. Push aborted.")
        return {"test_status": "FAIL_PUSH", "test_logs": "Missing deployment data"}

    print(f"    [*] Applying patch to {rel_file_path}...")
    if apply_patch_to_file(repo_path, rel_file_path, original_code, proposed_patch):
        print("    [+] Patch applied locally.")
        
        print("    [*] Pushing changes to GitHub...")
        commit_msg = f"🛡️ SentinelAI: Autonomous Patch for {state.get('cve_id', 'Security Vulnerability')}"
        if push_changes_to_github(repo_path, repo_url, commit_msg):
            print("    [✅] SUCCESS: Patched code pushed to GitHub!")
            return {"test_status": "SUCCESS_PUSH"}
        else:
            print("    [❌] FAILED: Git push failed.")
            return {"test_status": "FAIL_PUSH", "test_logs": "Git push operation failed."}
    else:
        print("    [❌] FAILED: Could not apply patch to local file.")
        return {"test_status": "FAIL_PUSH", "test_logs": "Failed to apply patch to file."}
