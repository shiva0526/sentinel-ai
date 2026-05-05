"""
main.py — FastAPI entrypoint for the SentinelAI Orchestrator.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .graph.builder import build_pipeline
from .core.config import settings
from .services.email_service import (
    notify_scan_started,
    notify_detection_complete,
    notify_fix_in_progress,
    notify_patch_complete,
    notify_pipeline_failed,
)


# Build the LangGraph pipeline
pipeline = build_pipeline()

# Create FastAPI app
app = FastAPI(
    title="SentinelAI Orchestrator",
    description="Autonomous Purple Team Security Pipeline",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HuntRequest(BaseModel):
    repo_url: str
    email: Optional[str] = None
    scan_mode: str = "auto"


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "orchestrator", "version": "2.0.0"}


@app.post("/hunt")
def trigger_pipeline(request: HuntRequest):
    print(f"\n{'='*60}")
    print(f"  SentinelAI Pipeline Initiated")
    print(f"  Target: {request.repo_url}")
    if request.email:
        print(f"  Notify: {request.email}")
    print(f"{'='*60}\n")

    # Send "scan started" email
    if request.email:
        notify_scan_started(request.email, request.repo_url)

    initial_state = {
        "repo_url": request.repo_url,
        "email": request.email or "",
        "scan_mode": request.scan_mode,
        "iterations": 0,
    }

    try:
        final_state = pipeline.invoke(initial_state)

        resolved_mode = final_state.get("adaptive_mode", request.scan_mode)
        email = request.email

        # Detect-only response (explicit or auto-selected)
        if resolved_mode == "detect_only":
            if final_state.get("test_status") == "FAIL":
                if email:
                    notify_pipeline_failed(email, request.repo_url, final_state.get("test_logs", "Scan failed."))
                return {
                    "status": "failed",
                    "mode": "detect_only",
                    "error": final_state.get("test_logs", "Scan failed.")
                }

            vuln_count = final_state.get("total_vulnerabilities", 0)
            if email:
                notify_detection_complete(email, request.repo_url, vuln_count)

            return {
                "status": "scan_complete",
                "mode": "detect_only",
                "repo_stats": final_state.get("repo_stats"),
                "total_vulnerabilities": vuln_count,
                "vulnerabilities": final_state.get("vulnerabilities", []),
            }

        # Full pipeline response
        if final_state.get("test_status") == "FAIL" and not final_state.get("cve_id"):
            if email:
                notify_pipeline_failed(email, request.repo_url, final_state.get("test_logs", "Pipeline failed."))
            return {
                "status": "failed",
                "mode": "full",
                "error": final_state.get("test_logs", "Pipeline failed.")
            }

        # Send completion email
        cve_id = final_state.get("cve_id", "Security Vulnerability")
        pr_url = final_state.get("pr_url")
        if email:
            notify_patch_complete(email, request.repo_url, cve_id, pr_url)

        return {
            "status": "success",
            "mode": "full",
            "repo_stats": final_state.get("repo_stats"),
            "vulnerability_found": cve_id,
            "secure_patch": final_state.get("proposed_patch"),
            "test_status": final_state.get("test_status"),
            "patched_files": final_state.get("patched_files", 0),
            "pr_url": pr_url,
        }
    except Exception as e:
        if request.email:
            notify_pipeline_failed(request.email, request.repo_url, str(e))
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


if __name__ == "__main__":
    print("Starting SentinelAI Orchestrator on port 8000...")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
