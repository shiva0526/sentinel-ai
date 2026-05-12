"""
SentinelAI -- Hybrid Repo Fix Pipeline API
============================================
Wires the Semantic Scanner, AST Manager, and GitOps Engine into a single
FastAPI orchestration endpoint that can scan a repo, isolate a vulnerable
function, apply a patch, and commit the fix on a new branch.
"""

import os
import sys
import shutil
import stat

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import git  # GitPython

# ── Internal SentinelAI modules ──────────────────────────────────────────
from sentinel_core.scanner import SentinelScanner
from sentinel_core.ast_manager import extract_function, inject_patch
from sentinel_core.git_manager import SentinelGitManager
from sentinel_core.notifier import send_email

# ── LangGraph Adversarial Pipeline ───────────────────────────────────────
# Add the orchestrator directory to sys.path so graph.py's local imports
# (ast_tool, recon_agents, hunter_agent) resolve correctly.
_orchestrator_dir = os.path.join(os.path.dirname(__file__), "..", "orchestrator")
if _orchestrator_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_orchestrator_dir))

from graph import app as sentinel_graph  # compiled LangGraph state machine



# ====================================================================== #
#  Pydantic Request Model                                                  #
# ====================================================================== #
class RepoScanRequest(BaseModel):
    repo_path: str


# ====================================================================== #
#  FastAPI Application                                                     #
# ====================================================================== #
app = FastAPI(
    title="SentinelAI Hybrid Repo Fix Pipeline",
    version="0.1.0",
    description="Scan -> Isolate -> Patch -> Commit in a single request.",
)

# ── CORS: Allow all origins to connect ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler — ensures CORS headers on ALL errors ─────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch any unhandled exception and return a proper JSON 500 response
    so the CORS middleware can still attach its headers."""
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.post("/scan_and_fix_repo")
def scan_and_fix_repo(request: RepoScanRequest):
    """
    End-to-end autonomous orchestration endpoint.

    Pipeline stages:
        1. Scan & Triage  (SentinelScanner — multi-vector sweep)
        2. Isolate         (ast_manager.extract_function)
        3. Adversarial Sandbox (LangGraph Blue/Red team + Go Arena)
        4. Surgical Injection  (ast_manager.inject_patch)
        5. GitOps Delivery     (SentinelGitManager)
    """

    # ── 0. Setup GitManager & Prepare Local Repo ─────────────────────
    
    # Notify pipeline started
    send_email(
        subject=f"SentinelAI Pipeline Initiated: {request.repo_path}",
        html_body=f"<h2>SentinelAI Pipeline Started</h2><p>The Purple Team orchestration engine has started processing the repository: <b>{request.repo_path}</b>.</p><p>You will be notified once the remediation is complete.</p>"
    )
    
    gm = SentinelGitManager()

    if request.repo_path.startswith("http"):
        print(f"[Pipeline] URL detected. Cloning '{request.repo_path}'...")
        repo = gm.clone_repo(request.repo_path)
        repo_path = repo.working_dir
    else:
        repo_path = os.path.abspath(request.repo_path)
        repo = git.Repo(repo_path)

    # ── 1. Scan & Triage (autonomous multi-vector sweep) ─────────────
    print("\n[Pipeline] Stage 1 -- Scan & Triage (autonomous)")

    # 1. Clean the URL/path to get just the repo name (e.g., "test")
    repo_name = request.repo_path.split("/")[-1].replace(".git", "")

    # 2. Create a safe Windows folder path for the ChromaDB
    safe_db_path = os.path.abspath(f"./sentinel_db_{repo_name}")

    # 3. Initialize the scanner with the safe path
    if os.path.exists(safe_db_path):
        def _force_remove(func, path, _exc_info):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        try:
            shutil.rmtree(safe_db_path, onerror=_force_remove)
        except PermissionError:
            # ChromaDB may still hold file handles; use a fresh unique path
            import uuid
            safe_db_path = os.path.abspath(f"./sentinel_db_{repo_name}_{uuid.uuid4().hex[:8]}")
            print(f"[Pipeline]   Previous DB locked, using: {safe_db_path}")

    scanner = SentinelScanner(db_path=safe_db_path)
    scanner.ingest_repo(repo_path)

    # Core threat vectors to sweep
    THREAT_VECTORS = [
        "SQL injection",
        "Server-Side Request Forgery SSRF",
        "OS Command Injection RCE",
        "Hardcoded Secrets",
    ]

    best_threat = None
    detected_threat = None

    for vector in THREAT_VECTORS:
        hits = scanner.find_threats(vector)
        if hits:
            top_hit = hits[0]  # highest confidence for this vector
            print(f"[Pipeline]   {vector}: top score {top_hit['confidence_score']:.2%}")
            if best_threat is None or top_hit["confidence_score"] > best_threat["confidence_score"]:
                best_threat = top_hit
                detected_threat = vector

    if best_threat is None:
        raise HTTPException(status_code=404, detail="No threats detected across all vectors.")

    top_threat = best_threat
    file_path = top_threat["file"]
    function_name = top_threat["function_name"]

    print(f"[Pipeline]   Winner: '{detected_threat}' -> {function_name}() in {file_path}")
    print(f"[Pipeline]   Confidence: {top_threat['confidence_score']:.2%}")

    # ── 2. Isolate ───────────────────────────────────────────────────
    print("\n[Pipeline] Stage 2 -- Isolate vulnerable function")

    vulnerable_code = extract_function(file_path, function_name)
    print(f"[Pipeline]   Extracted {len(vulnerable_code)} bytes of vulnerable code")

    # ── 3. Adversarial Sandbox (Real LangGraph) ──────────────────────
    print("\n[Pipeline] Stage 3 -- Adversarial Sandbox (LangGraph)")

    final_state = sentinel_graph.invoke({
        "original_code": vulnerable_code,
        "iterations": 0,
    })

    secure_patch = final_state.get("proposed_patch", "")
    test_status = final_state.get("test_status", "FAIL")

    print(f"[Pipeline]   Arena verdict: {test_status}")

    if test_status != "PASS":
        raise HTTPException(
            status_code=500,
            detail="Arena Validation Failed: The generated patch was successfully exploited.",
        )

    # ── 4. Surgical Injection ────────────────────────────────────────
    print("\n[Pipeline] Stage 4 -- Surgical Injection")

    inject_patch(file_path, function_name, secure_patch)

    # ── 5. GitOps Delivery ───────────────────────────────────────────
    print("\n[Pipeline] Stage 5 -- GitOps Delivery")

    # repo and gm are already initialized at the start of the function

    branch_name = f"sentinel-fix-{function_name}"
    commit_msg = f"SentinelAI Auto-Fix: Secured {function_name}"

    # Compute the relative path of the fixed file for staging
    rel_path = os.path.relpath(file_path, repo_path)

    gm.create_fix_branch(repo, branch_name)
    gm.commit_changes(repo, rel_path, commit_msg)

    # Extract "username/repo" from the URL (e.g., "shiva0526/test")
    repo_full_name = request.repo_path.split("github.com/")[-1].replace(".git", "")

    # Push to GitHub and create the Pull Request
    print("[Pipeline]   Pushing branch to cloud and opening PR...")
    pr_url = gm.push_and_create_pr(
        repo=repo,
        repo_full_name=repo_full_name,
        branch_name=branch_name,
        pr_title=f"SentinelAI Auto-Fix: Secured {function_name}",
        pr_body="### SentinelAI Automated Remediation\nThis PR was generated autonomously after neutralizing a critical vulnerability.",
    )
    print(f"[Pipeline]   PR Created: {pr_url}")

    # ── 6. Response ──────────────────────────────────────────────────
    print("\n[Pipeline] Done -- returning results.\n")

    # Notify pipeline completed
    send_email(
        subject=f"SentinelAI Remediation Complete: {function_name}",
        html_body=f"<h2>Threat Neutralized</h2><p>SentinelAI successfully isolated and patched the vulnerable function <b>{function_name}</b>.</p><p>Detected Threat: {detected_threat}</p><p>GitOps PR: <a href='{pr_url}'>{pr_url}</a></p>"
    )

    return {
        "status": "FIXED",
        "detected_threat": detected_threat,
        "file_fixed": rel_path,
        "vulnerable_code": vulnerable_code,
        "secure_patch": secure_patch,
        "git_branch": branch_name,
        "pr_url": pr_url,
    }


# ====================================================================== #
#  Execution Block                                                         #
# ====================================================================== #
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
