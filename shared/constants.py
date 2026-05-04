"""
shared/constants.py — Cross-service constants.
"""

# Service URLs
ARENA_URL = "http://localhost:8080"
ORCHESTRATOR_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"

# Arena endpoints
ARENA_EXECUTE_ENDPOINT = f"{ARENA_URL}/execute"
ARENA_SEARCH_ENDPOINT = f"{ARENA_URL}/search"

# Orchestrator endpoints
ORCHESTRATOR_HUNT_ENDPOINT = f"{ORCHESTRATOR_URL}/hunt"

# Sandbox constraints
SANDBOX_TIMEOUT_SECONDS = 10
SANDBOX_IMAGE = "python:3.10-slim"
