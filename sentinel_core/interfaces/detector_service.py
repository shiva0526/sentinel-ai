"""
detector_service.py — Clean public API for the detection engine.

This is the ONLY interface the orchestrator should use to interact
with sentinel_core.  It wraps VulnerabilityAnalyzer and provides
simple, typed methods.
"""

import json
from typing import List, Optional

from ..detector.analyzer import VulnerabilityAnalyzer
from ..detector.models import Finding


class DetectorService:
    """
    Clean integration point for the SentinelAI detection engine.

    Usage:
        from sentinel_core import DetectorService

        svc = DetectorService()
        findings = svc.detect(source_code)
        llm_prompt = svc.format_for_llm(findings)
    """

    def __init__(self, verbose: bool = False):
        self._analyzer = VulnerabilityAnalyzer(verbose=verbose)

    def detect(self, source_code: str) -> List[Finding]:
        """Run the full detection pipeline and return findings."""
        return self._analyzer.run(source_code)

    def detect_json(self, source_code: str) -> str:
        """Run detection and return JSON string."""
        return self._analyzer.run_json(source_code)

    def detect_report(self, source_code: str) -> str:
        """Run detection and return human-readable report."""
        return self._analyzer.run_report(source_code)

    def format_for_llm(self, findings: List[Finding]) -> str:
        """Format findings into a structured LLM validation prompt."""
        return self._analyzer.format_for_llm(findings)

    def has_findings(self, source_code: str) -> bool:
        """Quick check: does this code have any vulnerabilities?"""
        return len(self.detect(source_code)) > 0

    def get_primary_cwe(self, findings: List[Finding]) -> Optional[str]:
        """Return the CWE of the highest-confidence finding, or None."""
        if not findings:
            return None
        return findings[0].cwe
