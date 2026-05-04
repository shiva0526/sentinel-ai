"""
main.py — FastAPI entrypoint for the SentinelAI Orchestrator.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .graph.builder import build_pipeline
from .core.config import settings


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


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "orchestrator", "version": "2.0.0"}


@app.post("/hunt")
def trigger_pipeline(request: HuntRequest):
    print(f"\n{'='*60}")
    print(f"  SentinelAI Pipeline Initiated")
    print(f"  Target: {request.repo_url}")
    print(f"{'='*60}\n")

    initial_state = {
        "repo_url": request.repo_url,
        "iterations": 0,
    }

    try:
        final_state = pipeline.invoke(initial_state)
        return {
            "status": "success",
            "vulnerability_found": final_state.get("cve_id"),
            "secure_patch": final_state.get("proposed_patch"),
            "test_status": final_state.get("test_status"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")


if __name__ == "__main__":
    print("Starting SentinelAI Orchestrator on port 8000...")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
