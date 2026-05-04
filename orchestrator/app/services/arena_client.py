"""
arena_client.py — HTTP client for the Go Arena sandbox.

All Arena communication goes through this service.
"""

import requests
from ..core.config import settings


def execute_in_sandbox(combined_code: str) -> dict:
    """Send combined code to the Arena sandbox for execution.

    Returns:
        dict with keys: success (bool), output (str), error (str)
    """
    response = requests.post(
        f"{settings.ARENA_URL}/execute",
        json={
            "language": "python",
            "combined_code": combined_code,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def search_web(query: str) -> str:
    """Search the web via the Arena's DuckDuckGo OSINT endpoint.

    Returns:
        Raw JSON response text from the search.
    """
    response = requests.post(
        f"{settings.ARENA_URL}/search",
        json={"query": query},
        timeout=15,
    )
    return response.text
