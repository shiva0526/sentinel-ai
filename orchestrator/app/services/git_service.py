"""
git_service.py — Git operations for branch creation, committing patches,
                  and opening Pull Requests via the GitHub API.

Safety rules:
    - NEVER push directly to main.
    - ALWAYS create a new branch.
"""

import os
import re
import subprocess
import json
from urllib import request as urllib_request
from urllib.error import HTTPError


# ---------------------------------------------------------------------------
# Local file patching (kept for backward compatibility with deployer)
# ---------------------------------------------------------------------------

def apply_patch_to_file(repo_path: str, rel_file_path: str, original_code: str, patched_code: str) -> bool:
    """Apply the patch by replacing original_code with patched_code in the file."""
    full_path = os.path.join(repo_path, rel_file_path)
    if not os.path.exists(full_path):
        print(f"Error: File {full_path} not found.")
        return False

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if original_code not in content:
        print(f"Warning: Could not find exact original code snippet in {rel_file_path}. Patching might be partial.")
        return False

    new_content = content.replace(original_code, patched_code)

    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


# ---------------------------------------------------------------------------
# Branch + Commit + Push
# ---------------------------------------------------------------------------

BRANCH_NAME = "sentinel-fix"


def create_branch_and_push(repo_path: str, repo_url: str, commit_message: str) -> bool:
    """Create a new branch, commit staged changes, and push the branch.

    Returns True on success, False on failure.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN not set in environment.")
        return False

    try:
        # Configure git user
        subprocess.run(["git", "config", "user.name", "SentinelAI"], cwd=repo_path, check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "config", "user.email", "sentinel-ai@autonomous.security"], cwd=repo_path, check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Unshallow the clone so we can push branches
        subprocess.run(["git", "fetch", "--unshallow"], cwd=repo_path,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Create and checkout new branch
        subprocess.run(["git", "checkout", "-b", BRANCH_NAME], cwd=repo_path, check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Stage all changes
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Commit
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Prepare authenticated URL
        auth_url = repo_url.replace("https://github.com/", f"https://{github_token}@github.com/")
        if not auth_url.endswith(".git"):
            auth_url += ".git"

        # Push branch (never main!)
        result = subprocess.run(
            ["git", "push", auth_url, f"HEAD:{BRANCH_NAME}"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"Git push failed: {result.stderr}")
            return False

        return True
    except Exception as e:
        print(f"Branch/push failed: {e}")
        return False


# ---------------------------------------------------------------------------
# GitHub Pull Request creation via REST API
# ---------------------------------------------------------------------------

def _extract_owner_repo(repo_url: str):
    """Extract owner and repo name from a GitHub URL."""
    # Handles https://github.com/owner/repo or https://github.com/owner/repo.git
    match = re.search(r"github\.com/([^/]+)/([^/.]+)", repo_url)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def create_pull_request(repo_url: str, title: str, body: str) -> str | None:
    """Open a Pull Request from sentinel-fix → main using the GitHub API.

    Returns the PR URL on success, or None on failure.
    """
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN not set.")
        return None

    owner, repo = _extract_owner_repo(repo_url)
    if not owner or not repo:
        print(f"Error: Could not parse owner/repo from URL: {repo_url}")
        return None

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    payload = json.dumps({
        "title": title,
        "body": body,
        "head": BRANCH_NAME,
        "base": "main",
    }).encode("utf-8")

    req = urllib_request.Request(
        api_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urllib_request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pr_url = data.get("html_url")
            print(f"    [+] PR created: {pr_url}")
            return pr_url
    except HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else "No body"
        print(f"    [!] GitHub API error ({e.code}): {error_body}")
        return None
    except Exception as e:
        print(f"    [!] PR creation failed: {e}")
        return None
