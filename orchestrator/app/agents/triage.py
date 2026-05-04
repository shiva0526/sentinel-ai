"""
triage.py — Triage Agent (preprocessing step).
"""

import ast
from ..graph.state import WarRoomState


class ASTBlueprintGenerator(ast.NodeVisitor):
    """Generates a human-readable AST blueprint for the Mechanic agent."""

    def __init__(self):
        self.blueprint = []
        self.indent_level = 0

    def add_line(self, text):
        self.blueprint.append("  " * self.indent_level + text)

    def visit_FunctionDef(self, node):
        self.add_line(f"Function: {node.name}() (Line {node.lineno})")
        self.indent_level += 1
        self.generic_visit(node)
        self.indent_level -= 1

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.add_line(f"Calls: {node.func.id}()")
        elif isinstance(node.func, ast.Attribute):
            self.add_line(f"Calls Method: {node.func.attr}()")
        self.generic_visit(node)

    def visit_Return(self, node):
        self.add_line(f"Returns a value (Line {node.lineno})")
        self.generic_visit(node)


def _generate_ast_blueprint(code_string: str) -> str:
    try:
        tree = ast.parse(code_string)
        gen = ASTBlueprintGenerator()
        gen.visit(tree)
        return "\n".join(gen.blueprint)
    except Exception as e:
        return f"Failed to parse AST: {e}"


def triage_agent(state: WarRoomState):
    print("\n[1] Triage Agent: Mapping code structure...")
    blueprint = _generate_ast_blueprint(state.get("original_code", ""))
    return {"ast_graph": blueprint}
