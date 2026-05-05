"""
deployer.py — Pushes validated patches to GitHub via branch + Pull Request.

Safety: NEVER pushes directly to main. Always creates a sentinel-fix branch.
"""

from ..graph.state import WarRoomState
from ..services.git_service import apply_patch_to_file, create_branch_and_push, create_pull_request

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
    cve_id = state.get("cve_id", "Security Vulnerability")

    if not all([repo_path, rel_file_path, original_code, proposed_patch]):
        print("    [!] Missing data for deployment. Push aborted.")
        return {"test_status": "FAIL_PUSH", "test_logs": "Missing deployment data"}

    # 1. Apply patch to local file
    print(f"    [*] Applying patch to {rel_file_path}...")
    if not apply_patch_to_file(repo_path, rel_file_path, original_code, proposed_patch):
        print("    [!] FAILED: Could not apply patch to local file.")
        return {"test_status": "FAIL_PUSH", "test_logs": "Failed to apply patch to file."}

    print("    [+] Patch applied locally.")

    # 2. Create branch, commit, and push
    commit_msg = f"fix: SentinelAI autonomous patch for {cve_id}"
    print(f"    [*] Creating branch 'sentinel-fix' and pushing...")
    if not create_branch_and_push(repo_path, repo_url, commit_msg):
        print("    [!] FAILED: Git branch/push failed.")
        return {"test_status": "FAIL_PUSH", "test_logs": "Git branch/push operation failed."}

    print("    [+] Branch pushed successfully.")

    # 3. Create Pull Request
    pr_title = f"[SentinelAI] Autonomous Security Patch: {cve_id}"
    pr_body = (
        f"## SentinelAI Autonomous Security Patch\n\n"
        f"**Vulnerability:** {cve_id}\n"
        f"**File:** `{rel_file_path}`\n\n"
        f"This patch was automatically generated, tested, and validated by SentinelAI's Purple Team pipeline.\n\n"
        f"### What changed\n"
        f"The vulnerable code was replaced with a secure implementation that mitigates the identified vulnerability.\n\n"
        f"### Validation\n"
        f"- Exploit payload was generated and tested against the patch in a sandboxed environment.\n"
        f"- Result: **PASS** — the exploit was successfully blocked.\n"
    )

    print("    [*] Creating Pull Request...")
    pr_url = create_pull_request(repo_url, pr_title, pr_body)

    if pr_url:
        print(f"    [+] SUCCESS: PR created at {pr_url}")
        return {
            "test_status": "SUCCESS_PUSH",
            "patched_files": 1,
            "pr_url": pr_url,
        }
    else:
        print("    [!] Branch pushed but PR creation failed.")
        return {
            "test_status": "SUCCESS_PUSH",
            "patched_files": 1,
            "pr_url": None,
            "test_logs": "Branch pushed successfully but PR creation failed. Create PR manually.",
        }
