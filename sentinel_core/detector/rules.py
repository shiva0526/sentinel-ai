"""
rules.py — Deterministic rule engine for the SentinelAI detection engine.

Each rule inspects the ASTData and FlowChains to produce structured
Finding objects.  Rules are independent and composable — add a new one
by writing a function and appending it to RULE_REGISTRY.
"""

import re
from typing import List

from .models import ASTData, FlowChain, Finding, Confidence
from ..utils.patterns import (
    DANGEROUS_FUNCS,
    SQL_PATTERN,
    SECRET_PATTERNS,
    SECRET_VARIABLE_NAMES,
    HTML_SINKS,
    SANITIZERS,
)


# ══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL RULES
# ══════════════════════════════════════════════════════════════════════════════

def rule_sql_injection(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    CWE-89 — SQL Injection.
    Triggered when user input flows into an SQL execution sink AND
    the intermediate assignment contains SQL keywords (SELECT, INSERT, etc.).
    """
    findings: List[Finding] = []

    sql_sinks = {"execute", "executemany", "executescript", "raw"}

    for chain in flows:
        sink_method = chain.sink_func.split(".")[-1]
        if sink_method not in sql_sinks:
            continue

        # Verify that the flow path passes through a string containing SQL keywords
        has_sql_context = False
        for assign in ast_data.assignments:
            if assign.target in chain.path:
                if SQL_PATTERN.search(assign.value_repr):
                    has_sql_context = True
                    break
                # Also flag f-strings that concat user input into queries
                if assign.is_fstring and any(n in assign.value_names for n in chain.path):
                    has_sql_context = True
                    break

        if not has_sql_context:
            # Even without SQL keywords, direct input → execute is suspicious
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.HIGH

        # Check for sanitisation
        if _has_sanitizer(ast_data, chain):
            confidence = Confidence.LOW

        findings.append(Finding(
            vuln_type="SQL Injection",
            confidence=confidence,
            cwe="CWE-89",
            source=chain.source_var,
            sink=f"{chain.sink_func}({', '.join(chain.path[-1:])})",
            line=chain.sink_line,
            source_line=chain.source_line,
            explanation=(
                f"User input '{chain.source_var}' (from {chain.source_kind}) "
                f"flows into SQL execution sink '{chain.sink_func}()' "
                f"without parameterised query. Path: {' → '.join(chain.path)}"
            ),
            flow_path=chain.path,
        ))

    return findings


def rule_command_injection(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    CWE-78 — OS Command Injection.
    Triggered when user input flows into os.system, subprocess.*, os.popen, etc.
    """
    findings: List[Finding] = []

    cmd_sinks = {
        "os.system", "system", "os.popen", "popen",
        "subprocess.run", "subprocess.call", "subprocess.Popen",
        "subprocess.check_output", "subprocess.check_call",
    }

    for chain in flows:
        if chain.sink_func not in cmd_sinks and chain.sink_func.split(".")[-1] not in cmd_sinks:
            continue

        confidence = Confidence.HIGH
        if _has_sanitizer(ast_data, chain):
            confidence = Confidence.LOW

        findings.append(Finding(
            vuln_type="Command Injection",
            confidence=confidence,
            cwe="CWE-78",
            source=chain.source_var,
            sink=f"{chain.sink_func}({', '.join(chain.path[-1:])})",
            line=chain.sink_line,
            source_line=chain.source_line,
            explanation=(
                f"User input '{chain.source_var}' (from {chain.source_kind}) "
                f"flows into command execution sink '{chain.sink_func}()'. "
                f"Path: {' → '.join(chain.path)}"
            ),
            flow_path=chain.path,
        ))

    return findings


def rule_code_injection(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    CWE-94 — Code Injection (eval / exec).
    Triggered when user input flows into eval() or exec().
    """
    findings: List[Finding] = []

    code_sinks = {"eval", "exec", "compile"}

    for chain in flows:
        if chain.sink_func not in code_sinks:
            continue

        findings.append(Finding(
            vuln_type="Code Injection",
            confidence=Confidence.CRITICAL,
            cwe="CWE-94",
            source=chain.source_var,
            sink=f"{chain.sink_func}({', '.join(chain.path[-1:])})",
            line=chain.sink_line,
            source_line=chain.source_line,
            explanation=(
                f"User input '{chain.source_var}' (from {chain.source_kind}) "
                f"flows into dynamic code execution '{chain.sink_func}()'. "
                f"This is almost always exploitable. Path: {' → '.join(chain.path)}"
            ),
            flow_path=chain.path,
        ))

    return findings


def rule_xss(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    CWE-79 — Cross-Site Scripting (XSS).
    Triggered when user input flows into an HTML rendering sink
    without escaping.
    """
    findings: List[Finding] = []

    for chain in flows:
        sink_name = chain.sink_func.split(".")[-1]
        if sink_name not in HTML_SINKS:
            continue

        confidence = Confidence.HIGH
        if _has_sanitizer(ast_data, chain):
            confidence = Confidence.LOW

        findings.append(Finding(
            vuln_type="Cross-Site Scripting (XSS)",
            confidence=confidence,
            cwe="CWE-79",
            source=chain.source_var,
            sink=f"{chain.sink_func}()",
            line=chain.sink_line,
            source_line=chain.source_line,
            explanation=(
                f"User input '{chain.source_var}' (from {chain.source_kind}) "
                f"flows into HTML rendering sink '{chain.sink_func}()' "
                f"without escaping. Path: {' → '.join(chain.path)}"
            ),
            flow_path=chain.path,
        ))

    return findings


def rule_hardcoded_secrets(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    CWE-798 — Hardcoded Credentials / Secrets.
    Triggered when a string constant looks like an API key, password,
    or token based on variable names and value patterns.
    """
    findings: List[Finding] = []
    seen_lines: set = set()

    # Check assignments where the variable name is suspicious
    for assign in ast_data.assignments:
        if SECRET_VARIABLE_NAMES.search(assign.target):
            # The value should be a literal string (not a function call, etc.)
            value = assign.value_repr.strip("'\"")
            if len(value) >= 8 and not value.startswith("{") and not value.startswith("os."):
                if assign.line not in seen_lines:
                    seen_lines.add(assign.line)
                    findings.append(Finding(
                        vuln_type="Hardcoded Secret",
                        confidence=Confidence.HIGH,
                        cwe="CWE-798",
                        source=assign.target,
                        sink=f"{assign.target} = {_truncate(assign.value_repr, 40)}",
                        line=assign.line,
                        source_line=assign.line,
                        explanation=(
                            f"Variable '{assign.target}' appears to contain a "
                            f"hardcoded credential or secret (line {assign.line})."
                        ),
                        flow_path=[assign.target],
                    ))

    # Check raw strings against regex patterns
    for string_node in ast_data.strings:
        for pattern in SECRET_PATTERNS:
            if pattern.search(string_node.value):
                if string_node.line not in seen_lines:
                    seen_lines.add(string_node.line)
                    findings.append(Finding(
                        vuln_type="Hardcoded Secret",
                        confidence=Confidence.MEDIUM,
                        cwe="CWE-798",
                        source="<string literal>",
                        sink=_truncate(string_node.value, 50),
                        line=string_node.line,
                        source_line=string_node.line,
                        explanation=(
                            f"String at line {string_node.line} matches a known "
                            f"secret pattern (API key, token, or credential)."
                        ),
                        flow_path=[],
                    ))
                break  # one match per string is enough

    return findings


def rule_insecure_deserialization(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    CWE-502 — Insecure Deserialization.
    Triggered when user input flows into pickle.loads, yaml.load, etc.
    """
    findings: List[Finding] = []

    deser_sinks = {"pickle.loads", "loads", "yaml.load", "load", "marshal.loads"}

    for chain in flows:
        if chain.sink_func not in deser_sinks:
            continue

        # "loads" and "load" are too generic — only flag if it's clearly pickle/yaml
        if chain.sink_func in ("loads", "load"):
            # Check if there's an import of pickle or yaml in calls
            has_deser_context = any(
                "pickle" in c.func_name or "yaml" in c.func_name or "marshal" in c.func_name
                for c in ast_data.calls
            )
            if not has_deser_context:
                continue

        findings.append(Finding(
            vuln_type="Insecure Deserialization",
            confidence=Confidence.HIGH,
            cwe="CWE-502",
            source=chain.source_var,
            sink=f"{chain.sink_func}()",
            line=chain.sink_line,
            source_line=chain.source_line,
            explanation=(
                f"User input '{chain.source_var}' (from {chain.source_kind}) "
                f"flows into deserialization sink '{chain.sink_func}()'. "
                f"Arbitrary code execution is possible. Path: {' → '.join(chain.path)}"
            ),
            flow_path=chain.path,
        ))

    return findings


# ══════════════════════════════════════════════════════════════════════════════
# RULE REGISTRY — add new rules here
# ══════════════════════════════════════════════════════════════════════════════

RULE_REGISTRY = [
    rule_sql_injection,
    rule_command_injection,
    rule_code_injection,
    rule_xss,
    rule_hardcoded_secrets,
    rule_insecure_deserialization,
]


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def apply_rules(ast_data: ASTData, flows: List[FlowChain]) -> List[Finding]:
    """
    Run all registered rules against the parsed data and flow chains.

    Args:
        ast_data: Parsed ASTData from ast_parser.parse_code().
        flows:    Flow chains from flow_tracker.track_flows().

    Returns:
        List of Finding objects — one per detected vulnerability.
    """
    all_findings: List[Finding] = []

    for rule_fn in RULE_REGISTRY:
        findings = rule_fn(ast_data, flows)
        all_findings.extend(findings)

    return all_findings


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _has_sanitizer(ast_data: ASTData, chain: FlowChain) -> bool:
    """
    Check if any known sanitiser function appears in calls that operate
    on variables in the flow chain.  If so, the finding confidence should
    be reduced.
    """
    chain_vars = set(chain.path)
    for call in ast_data.calls:
        # Does this call reference a variable in our taint chain?
        if not chain_vars.intersection(call.args_names):
            continue
        # Is it a sanitiser?
        for san in SANITIZERS:
            if san in call.func_name:
                return True
    return False


def _truncate(s: str, length: int) -> str:
    """Truncate a string for display, appending '…' if shortened."""
    return s if len(s) <= length else s[:length] + "…"
