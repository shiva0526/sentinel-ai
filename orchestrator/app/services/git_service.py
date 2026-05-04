import os
import subprocess

def apply_patch_to_file(repo_path: str, rel_file_path: str, original_code: str, patched_code: str) -> bool:
    """Apply the patch by replacing original_code with patched_code in the file."""
    full_path = os.path.join(repo_path, rel_file_path)
    if not os.path.exists(full_path):
        print(f"Error: File {full_path} not found.")
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if original_code not in content:
        # If exact match fails, try a more flexible replacement or log error
        print(f"Warning: Could not find exact original code snippet in {rel_file_path}. Patching might be partial.")
        # Fallback: if the file is small and seems to be the one, we might replace it entirely
        # but for now, let's just do exact replacement for safety.
        return False

    new_content = content.replace(original_code, patched_code)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def push_changes_to_github(repo_path: str, repo_url: str, commit_message: str) -> bool:
    """Commit and push changes back to the repository."""
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN not set in environment.")
        return False

    try:
        # Configure git user for the commit
        subprocess.run(["git", "config", "user.name", "SentinelAI"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "sentinel-ai@autonomous.security"], cwd=repo_path, check=True)

        # Stage changes
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        
        # Commit
        subprocess.run(["git", "commit", "-m", commit_message], cwd=repo_path, check=True)

        # Prepare authenticated URL
        # Format: https://<token>@github.com/user/repo.git
        auth_url = repo_url.replace("https://github.com/", f"https://{github_token}@github.com/")
        
        # Push
        result = subprocess.run(
            ["git", "push", auth_url, "HEAD:main"], 
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
        print(f"Push failed: {e}")
        return False
