"""
detector_client.py — Client for the sentinel_core detection engine.

Wraps sentinel_core.DetectorService so agents don't import it directly.
"""

import sys
import os

# Add project root so sentinel_core is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from sentinel_core import DetectorService


# Singleton instance
_service = DetectorService(verbose=False)


def detect_vulnerabilities(source_code: str):
    """Run the rule-based detection engine and return findings."""
    return _service.detect(source_code)


def format_findings_for_llm(findings) -> str:
    """Format findings into a structured LLM validation prompt."""
    return _service.format_for_llm(findings)


def get_primary_cwe(findings) -> str:
    """Return the CWE of the highest-confidence finding."""
    return _service.get_primary_cwe(findings) or "UNKNOWN"
