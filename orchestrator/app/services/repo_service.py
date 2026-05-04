"""
repo_service.py — Clones GitHub repositories for analysis.
"""

import subprocess
import tempfile
import os
import shutil

# Maximum time allowed for git clone (in seconds)
CLONE_TIMEOUT = 15

def fetch_repo(repo_url: str) -> str:
    """
    Clone GitHub repository into a temporary directory.
    Return the local path.
    Raise exception if failed.
    """
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Only github.com repositories are supported.")

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp(prefix="sentinel_repo_")
    
    print(f"    [*] Cloning repository {repo_url} into {temp_dir}...")
    
    try:
        # Run git clone with depth=1 for speed
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=CLONE_TIMEOUT
        )
        
        if result.returncode != 0:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Git clone failed: {result.stderr}")
            
        return temp_dir
        
    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise TimeoutError(f"Cloning repository timed out after {CLONE_TIMEOUT} seconds.")
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to fetch repository: {str(e)}")

def cleanup_repo(repo_path: str):
    """Clean up the temporary repository directory."""
    if repo_path and os.path.exists(repo_path):
        shutil.rmtree(repo_path, ignore_errors=True)
