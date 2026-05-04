"""
analyzer.py — Top-level vulnerability analyzer for SentinelAI.

Orchestrates the full detection pipeline:
    1. AST parsing
    2. Input extraction
    3. Data flow tracking
    4. Rule-based vulnerability detection
    5. Structured report generation

Usage:
    from sentinel_ai.detector import VulnerabilityAnalyzer

    analyzer = VulnerabilityAnalyzer()
    report = analyzer.run(source_code)
"""

import json
import logging
from typing import List, Dict, Any, Optional

from .ast_parser import parse_code
from .flow_tracker import track_flows
from .rules import apply_rules
from .models import ASTData, FlowChain, Finding

logger = logging.getLogger("sentinel_ai.analyzer")


class VulnerabilityAnalyzer:
    """
    Main entry point for the SentinelAI rule-based detection engine.
    
    Combines AST parsing → flow tracking → rule evaluation into a
    single `.run()` call that returns structured findings.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if verbose:
            logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        else:
            logging.basicConfig(level=logging.INFO, format="%(message)s")

    def run(self, source_code: str) -> List[Finding]:
        """
        Run the full vulnerability detection pipeline on source code.

        Args:
            source_code: Raw Python source code string.

        Returns:
            List of Finding objects with all detected vulnerabilities.
        """
        # ── Step 1: Parse the AST ───────────────────────────────────────
        logger.info("🔬 [1/4] Parsing AST...")
        try:
            ast_data = parse_code(source_code)
        except SyntaxError as e:
            logger.error(f"   ❌ Syntax error in source code: {e}")
            return []

        if self.verbose:
            self._log_ast_data(ast_data)

        # ── Step 2: Track data flows ────────────────────────────────────
        logger.info("🔄 [2/4] Tracking data flows...")
        flows = track_flows(ast_data)

        if self.verbose:
            self._log_flows(flows)

        # ── Step 3: Apply rules ─────────────────────────────────────────
        logger.info("☠️  [3/4] Applying vulnerability rules...")
        findings = apply_rules(ast_data, flows)

        # ── Step 4: Deduplicate and sort ────────────────────────────────
        logger.info("📊 [4/4] Generating report...")
        findings = self._deduplicate(findings)
        findings.sort(key=lambda f: (
            self._confidence_rank(f.confidence), f.line
        ))

        logger.info(f"   ✅ Analysis complete: {len(findings)} vulnerability(ies) found.\n")
        return findings

    # ── Report Formats ──────────────────────────────────────────────────

    def run_json(self, source_code: str) -> str:
        """Run analysis and return findings as a JSON string."""
        findings = self.run(source_code)
        return json.dumps(
            [f.to_dict() for f in findings],
            indent=2,
        )

    def run_report(self, source_code: str) -> str:
        """Run analysis and return a human-readable text report."""
        findings = self.run(source_code)
        if not findings:
            return "✅ No vulnerabilities detected."

        lines = [
            f"{'='*60}",
            f"  SentinelAI Vulnerability Report — {len(findings)} finding(s)",
            f"{'='*60}",
            "",
        ]

        for i, f in enumerate(findings, 1):
            lines.append(f"  [{i}] {f.vuln_type} ({f.confidence.value} Confidence)")
            lines.append(f"      CWE:     {f.cwe}")
            lines.append(f"      Source:   {f.source} (line {f.source_line})")
            lines.append(f"      Sink:    {f.sink} (line {f.line})")
            if f.flow_path:
                lines.append(f"      Flow:    {' → '.join(f.flow_path)}")
            lines.append(f"      Detail:  {f.explanation}")
            lines.append("")

        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def format_for_llm(self, findings: List[Finding]) -> str:
        """
        Format findings into a structured prompt suitable for sending
        to an LLM for validation and patch generation.

        This replaces the naive "just ask the AI to find bugs" approach
        with deterministic findings that the AI confirms and patches.
        """
        if not findings:
            return "No rule-based vulnerabilities detected. Perform a general security review."

        sections = [
            "The following vulnerabilities were detected by SentinelAI's rule-based engine.",
            "For each finding, confirm whether it is a true positive and suggest a secure patch.",
            "",
            "---",
        ]

        for i, f in enumerate(findings, 1):
            sections.append(f"Finding #{i}:")
            sections.append(f"  - Type: {f.vuln_type}")
            sections.append(f"  - CWE: {f.cwe}")
            sections.append(f"  - Confidence: {f.confidence.value}")
            sections.append(f"  - Input Source: {f.source} (line {f.source_line})")
            sections.append(f"  - Dangerous Sink: {f.sink} (line {f.line})")
            if f.flow_path:
                sections.append(f"  - Data Flow: {' → '.join(f.flow_path)}")
            sections.append(f"  - Explanation: {f.explanation}")
            sections.append("")
            sections.append("Task:")
            sections.append("  Confirm this vulnerability and suggest a secure fix.")
            sections.append("---")

        return "\n".join(sections)

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _deduplicate(findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on (type, source, sink, line)."""
        seen = set()
        unique = []
        for f in findings:
            key = (f.vuln_type, f.source, f.sink, f.line)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    @staticmethod
    def _confidence_rank(confidence) -> int:
        """Rank for sorting (Critical first)."""
        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        return order.get(confidence.value, 99)

    def _log_ast_data(self, data: ASTData):
        logger.debug(f"   Functions:   {len(data.functions)}")
        for fn in data.functions:
            logger.debug(f"     🔧 {fn.name}({', '.join(fn.args)}) @ line {fn.line}")
        logger.debug(f"   Assignments: {len(data.assignments)}")
        for a in data.assignments:
            logger.debug(f"     📝 {a.target} = {a.value_repr[:60]} @ line {a.line}")
        logger.debug(f"   Calls:       {len(data.calls)}")
        for c in data.calls:
            logger.debug(f"     📞 {c.func_name}({', '.join(c.args_repr[:3])}) @ line {c.line}")
        logger.debug(f"   Inputs:      {len(data.inputs)}")
        for inp in data.inputs:
            logger.debug(f"     🎯 {inp.variable} ← {inp.source} @ line {inp.line}")
        logger.debug("")

    def _log_flows(self, flows: List[FlowChain]):
        if not flows:
            logger.debug("   No tainted data flows detected.")
            return
        for chain in flows:
            logger.debug(
                f"   ⛓️  {chain.source_var} ({chain.source_kind}) "
                f"→ {chain.sink_func}() @ line {chain.sink_line}  "
                f"[{' → '.join(chain.path)}]"
            )
        logger.debug("")
