"""
models.py — Data models for the SentinelAI vulnerability detection engine.

All structured types used across the parser, flow tracker, rule engine,
and analyzer are defined here to keep the system consistent and typed.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


# ─── Confidence Levels ──────────────────────────────────────────────────────

class Confidence(Enum):
    """How confident the engine is in a finding."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# ─── AST-Extracted Nodes ────────────────────────────────────────────────────

@dataclass
class FunctionNode:
    """A parsed function definition."""
    name: str
    args: List[str]
    line: int
    end_line: Optional[int] = None


@dataclass
class AssignmentNode:
    """A parsed variable assignment (e.g. `query = "SELECT ..." + user_id`)."""
    target: str
    value_repr: str          # string representation of the RHS
    value_names: List[str]   # names referenced in the RHS  (e.g. ["user_id"])
    line: int
    is_fstring: bool = False


@dataclass
class CallNode:
    """A parsed function/method call."""
    func_name: str           # "execute", "os.system", "cursor.execute", etc.
    args_repr: List[str]     # string representation of each positional arg
    args_names: List[str]    # variable names used in args
    line: int
    is_method: bool = False  # True when the call is obj.method(...)


@dataclass
class InputNode:
    """A detected user-controlled input source."""
    variable: str
    source: str              # "input()", "request.GET", "sys.argv", "parameter"
    line: int


@dataclass
class ReturnNode:
    """A return statement."""
    value_repr: str
    line: int


@dataclass
class StringNode:
    """A raw string constant — used for secret detection."""
    value: str
    line: int


# ─── Aggregated AST Data ────────────────────────────────────────────────────

@dataclass
class ASTData:
    """Everything the AST parser extracts from a source file."""
    functions: List[FunctionNode] = field(default_factory=list)
    assignments: List[AssignmentNode] = field(default_factory=list)
    calls: List[CallNode] = field(default_factory=list)
    inputs: List[InputNode] = field(default_factory=list)
    returns: List[ReturnNode] = field(default_factory=list)
    strings: List[StringNode] = field(default_factory=list)


# ─── Flow Tracking ──────────────────────────────────────────────────────────

@dataclass
class FlowChain:
    """Represents a data-flow path from an input source to a dangerous sink."""
    source_var: str          # original tainted variable
    source_kind: str         # "input()", "request.GET", etc.
    source_line: int
    sink_func: str           # dangerous function that consumes the tainted data
    sink_line: int
    path: List[str]          # chain of variables: ["user_id", "query"]


# ─── Final Finding ──────────────────────────────────────────────────────────

@dataclass
class Finding:
    """A single vulnerability finding produced by the rule engine."""
    vuln_type: str           # "SQL Injection", "Command Injection", etc.
    confidence: Confidence
    cwe: str                 # "CWE-89", "CWE-78", etc.
    source: str              # tainted variable name
    sink: str                # dangerous call repr
    line: int                # line of the sink
    source_line: int         # line of the source
    explanation: str
    flow_path: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.vuln_type,
            "confidence": self.confidence.value,
            "cwe": self.cwe,
            "source": self.source,
            "sink": self.sink,
            "line": self.line,
            "source_line": self.source_line,
            "explanation": self.explanation,
            "flow_path": self.flow_path,
        }
