"""
SentinelAI — GitOps Engine
==========================
Automates cloning, branching, committing, and opening GitHub Pull Requests
as part of the SentinelAI autonomous security remediation pipeline.
"""

import os
import stat
import shutil
import urllib.parse

import git  # GitPython
from github import Github  # PyGithub
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


def _remove_readonly(func, path, _exc_info):
    """Error handler for shutil.rmtree on Windows (read-only .git objects)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class SentinelGitManager:
    """Manages Git operations for the SentinelAI remediation workflow."""

    # ------------------------------------------------------------------ #
    #  1. Clone a repository (fresh clone every time)
    # ------------------------------------------------------------------ #
    def clone_repo(self, repo_url: str) -> git.Repo:
        """
        Clone *repo_url* into a dedicated workspace folder.

        - Workspace: ``./sentinel_workspaces/<repo_name>``
        - If the target folder already exists it is deleted first so that
          every invocation starts from a clean state.
        - The ``GITHUB_TOKEN`` environment variable is injected into the
          URL for authenticated HTTPS cloning.
        """
        # Create the workspace root if it doesn't exist
        workspace_root = os.path.join(".", "sentinel_workspaces")
        os.makedirs(workspace_root, exist_ok=True)

        # Extract the repo name from the URL (strip trailing .git if present)
        repo_name = repo_url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        local_dir = os.path.join(workspace_root, repo_name)

        # Always start fresh — remove existing folder
        if os.path.isdir(local_dir):
            print(f"[GitManager] Removing existing folder '{local_dir}' for fresh clone ...")
            shutil.rmtree(local_dir, onerror=_remove_readonly)

        # Inject the GITHUB_TOKEN into the clone URL
        token = os.getenv("GITHUB_TOKEN")
        parsed = urllib.parse.urlparse(repo_url)
        auth_url = parsed._replace(netloc=f"{token}@{parsed.hostname}").geturl()

        print(f"[GitManager] Cloning '{repo_url}' -> '{local_dir}' ...")
        repo = git.Repo.clone_from(auth_url, local_dir)
        print(f"[GitManager] Clone complete.")
        return repo

    # ------------------------------------------------------------------ #
    #  2. Create a fix branch and check it out
    # ------------------------------------------------------------------ #
    def create_fix_branch(self, repo: git.Repo, branch_name: str):
        """
        Create a new branch from the current active branch and check it out.
        If the branch already exists, just check it out.
        """
        if branch_name in [b.name for b in repo.branches]:
            print(f"[GitManager] Branch '{branch_name}' already exists -- checking out.")
            repo.git.checkout(branch_name)
        else:
            print(f"[GitManager] Creating branch '{branch_name}' from '{repo.active_branch.name}' ...")
            repo.git.checkout("-b", branch_name)
        print(f"[GitManager] Active branch: {repo.active_branch.name}")

    # ------------------------------------------------------------------ #
    #  3. Stage a file and commit
    # ------------------------------------------------------------------ #
    def commit_changes(self, repo: git.Repo, file_path: str, commit_message: str):
        """
        Stage the given *file_path* and commit with *commit_message*.
        *file_path* should be relative to the repository root.
        """
        repo.index.add([file_path])
        repo.index.commit(commit_message)
        print(f"[GitManager] Committed: '{commit_message}'")

    # ------------------------------------------------------------------ #
    #  4. Push branch & open a GitHub Pull Request
    # ------------------------------------------------------------------ #
    def push_and_create_pr(
        self,
        repo: git.Repo,
        repo_full_name: str,
        branch_name: str,
        pr_title: str,
        pr_body: str,
    ):
        """
        Push the active branch to the remote and create a Pull Request
        on GitHub via the PyGithub API.

        Parameters
        ----------
        repo : git.Repo
            The local GitPython Repo object (must have an ``origin`` remote).
        repo_full_name : str
            Repository in ``owner/repo`` format (e.g. ``shiva0526/test``).
        branch_name : str
            The feature/fix branch to push and merge.
        pr_title : str
            Title for the Pull Request.
        pr_body : str
            Markdown body for the Pull Request description.
        """
        # --- Push via GitPython ---
        print(f"[GitManager] Pushing branch '{branch_name}' to origin ...")
        repo.remotes.origin.push(branch_name)
        print(f"[GitManager] Push complete.")

        # --- Create PR via PyGithub ---
        gh = Github(os.getenv("GITHUB_TOKEN"))
        gh_repo = gh.get_repo(repo_full_name)

        # Determine the default branch to merge into
        base_branch = gh_repo.default_branch

        pr = gh_repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=base_branch,
        )
        print(f"[GitManager] Pull Request created: {pr.html_url}")
        return pr.html_url


# ====================================================================== #
#  Quick validation — confirm environment is configured
# ====================================================================== #
if __name__ == "__main__":
    print("=" * 60)
    print("  SentinelAI GitOps Engine — Environment Check")
    print("=" * 60)

    token = os.getenv("GITHUB_TOKEN")
    if token:
        print("\n[OK] .env loaded successfully.")
        print(f"[OK] GITHUB_TOKEN found ({len(token)} characters).")
    else:
        print("\n[FAIL] GITHUB_TOKEN not found in environment.")
        print("       Make sure your .env file contains GITHUB_TOKEN=<your_token>")

    print("\n" + "=" * 60)
