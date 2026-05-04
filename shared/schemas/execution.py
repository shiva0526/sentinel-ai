"""
shared/schemas/execution.py — Cross-service execution data contracts.

Used by orchestrator (sender) and arena (receiver) to define the
sandbox execution request/response format.
"""

from dataclasses import dataclass


@dataclass
class ExecutionRequest:
    """Request sent to the Arena sandbox."""
    language: str
    app_code: str
    exploit_payload: str


@dataclass
class ExecutionResponse:
    """Response returned from the Arena sandbox."""
    success: bool
    output: str
    error: str
