"""
shared/schemas/api_models.py — API-level request/response models.

Used by the frontend and orchestrator to define the REST API contracts.
"""

from pydantic import BaseModel
from typing import Optional, List


class HuntRequest(BaseModel):
    """POST /hunt request body."""
    repo_url: str


class HuntResponse(BaseModel):
    """POST /hunt response body."""
    status: str
    vulnerability_found: Optional[str] = None
    secure_patch: Optional[str] = None
    test_status: Optional[str] = None
    findings_count: int = 0


class HealthResponse(BaseModel):
    """GET /health response body."""
    status: str
    services: dict
