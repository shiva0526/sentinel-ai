"""
ast_parser.py — Deep AST parser for the SentinelAI detection engine.

Walks a Python AST and extracts every security-relevant node into the
structured ASTData model: functions, assignments, calls, inputs, returns,
and raw strings.
"""

import ast
from typing import List

from .models import (
    ASTData,
    FunctionNode,
    AssignmentNode,
    CallNode,
    InputNode,
    ReturnNode,
    StringNode,
)
from ..utils.patterns import INPUT_FUNCTIONS, INPUT_METHODS, INPUT_MODULES


class SecurityASTVisitor(ast.NodeVisitor):
    """Walks an AST tree and collects security-relevant nodes."""

    def __init__(self):
        self.data = ASTData()
        self._current_function_args: List[str] = []

    # ── Function Definitions ────────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef):
        args = [a.arg for a in node.args.args]
        self.data.functions.append(FunctionNode(
            name=node.name,
            args=args,
            line=node.lineno,
            end_line=getattr(node, "end_lineno", None),
        ))

        # Mark every function parameter as an input source
        for arg_name in args:
            if arg_name == "self":
                continue
            self.data.inputs.append(InputNode(
                variable=arg_name,
                source=f"parameter({node.name})",
                line=node.lineno,
            ))

        # Track args so we can tag them inside the body
        prev_args = self._current_function_args
        self._current_function_args = args
        self.generic_visit(node)
        self._current_function_args = prev_args

    # Also handle async functions
    visit_AsyncFunctionDef = visit_FunctionDef

    # ── Assignments ─────────────────────────────────────────────────────

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            target_name = self._node_to_name(target)
            if target_name is None:
                continue

            value_repr = self._node_to_repr(node.value)
            value_names = self._extract_names(node.value)
            is_fstring = isinstance(node.value, ast.JoinedStr)

            self.data.assignments.append(AssignmentNode(
                target=target_name,
                value_repr=value_repr,
                value_names=value_names,
                line=node.lineno,
                is_fstring=is_fstring,
            ))

            # Check if the RHS is a call to an input function
            self._check_input_assignment(target_name, node.value, node.lineno)

        self.generic_visit(node)

    # ── Calls ───────────────────────────────────────────────────────────

    def visit_Call(self, node: ast.Call):
        func_name = self._call_to_name(node)
        if func_name:
            args_repr = [self._node_to_repr(a) for a in node.args]
            args_names = []
            for a in node.args:
                args_names.extend(self._extract_names(a))

            self.data.calls.append(CallNode(
                func_name=func_name,
                args_repr=args_repr,
                args_names=args_names,
                line=node.lineno,
                is_method="." in func_name,
            ))

        self.generic_visit(node)

    # ── Return Statements ───────────────────────────────────────────────

    def visit_Return(self, node: ast.Return):
        value_repr = self._node_to_repr(node.value) if node.value else ""
        self.data.returns.append(ReturnNode(
            value_repr=value_repr,
            line=node.lineno,
        ))
        self.generic_visit(node)

    # ── String Constants (for secret detection) ─────────────────────────

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str) and len(node.value) >= 8:
            self.data.strings.append(StringNode(
                value=node.value,
                line=node.lineno,
            ))
        self.generic_visit(node)

    # ── Subscript access (request.GET["key"]) ───────────────────────────

    def visit_Subscript(self, node: ast.Subscript):
        # Detect request.GET["foo"], request.POST["bar"], etc.
        name = self._node_to_repr(node.value)
        for pattern in INPUT_METHODS:
            if name == pattern:
                # Try to figure out the variable it's assigned to
                # (handled by visit_Assign via _check_input_assignment)
                pass
        self.generic_visit(node)

    # ══════════════════════════════════════════════════════════════════════
    # HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _check_input_assignment(self, target: str, value_node: ast.AST, line: int):
        """Check if an assignment RHS is a known input source."""
        # Case 1: x = input(...)
        if isinstance(value_node, ast.Call):
            call_name = self._call_to_name(value_node)
            if call_name in INPUT_FUNCTIONS:
                self.data.inputs.append(InputNode(
                    variable=target, source=f"{call_name}()", line=line,
                ))
                return

        # Case 2: x = request.GET["key"]  or  request.form.get("key")
        repr_str = self._node_to_repr(value_node)
        for pattern in INPUT_METHODS:
            if pattern in repr_str:
                self.data.inputs.append(InputNode(
                    variable=target, source=pattern, line=line,
                ))
                return

        # Case 3: x = sys.argv[1]
        for mod_pattern in INPUT_MODULES:
            if mod_pattern in repr_str:
                self.data.inputs.append(InputNode(
                    variable=target, source=mod_pattern, line=line,
                ))
                return

    def _node_to_name(self, node: ast.AST) -> str | None:
        """Try to extract a simple string name from an AST target node."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = self._node_to_name(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return None

    def _node_to_repr(self, node: ast.AST) -> str:
        """Best-effort string representation of an AST expression."""
        if node is None:
            return ""
        try:
            return ast.unparse(node)
        except Exception:
            return "<unknown>"

    def _call_to_name(self, node: ast.Call) -> str | None:
        """Get the full dotted name of a function call."""
        return self._node_to_name(node.func)

    def _extract_names(self, node: ast.AST) -> List[str]:
        """Recursively collect all Name references inside an expression."""
        names: List[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.append(child.id)
        return names


# ─── Public API ──────────────────────────────────────────────────────────────

def parse_code(source_code: str) -> ASTData:
    """
    Parse Python source code and return structured ASTData.
    
    Args:
        source_code: Raw Python source code string.
    
    Returns:
        ASTData containing all extracted security-relevant nodes.
    
    Raises:
        SyntaxError: If the source code cannot be parsed.
    """
    tree = ast.parse(source_code)
    visitor = SecurityASTVisitor()
    visitor.visit(tree)
    return visitor.data
