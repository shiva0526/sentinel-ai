import ast

class ASTBlueprintGenerator(ast.NodeVisitor):
    def __init__(self):
        self.blueprint = []
        self.indent_level = 0

    def add_line(self, text):
        self.blueprint.append("  " * self.indent_level + text)

    def visit_FunctionDef(self, node):
        self.add_line(f"🔧 Function: {node.name}() (Line {node.lineno})")
        self.indent_level += 1
        self.generic_visit(node)
        self.indent_level -= 1

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.add_line(f"📞 Calls: {node.func.id}()")
        elif isinstance(node.func, ast.Attribute):
            self.add_line(f"📞 Calls Method: {node.func.attr}()")
        self.generic_visit(node)

    def visit_Return(self, node):
        self.add_line(f"⬅️ Returns a value (Line {node.lineno})")
        self.generic_visit(node)

def generate_ast_blueprint(code_string: str) -> str:
    try:
        # Parse the raw code into an Abstract Syntax Tree
        tree = ast.parse(code_string)
        
        # Walk through the tree and map it out
        generator = ASTBlueprintGenerator()
        generator.visit(tree)
        
        return "\n".join(generator.blueprint)
    except Exception as e:
        return f"Failed to parse AST: {str(e)}"

# Quick test to see how it works!
if __name__ == "__main__":
    vulnerable_code = """
def process_payment(user_id, amount):
    db_query = f"SELECT * FROM users WHERE id = {user_id}"
    execute(db_query)
    return "Success"
"""
    print("Raw Code:")
    print(vulnerable_code)
    print("-" * 20)
    print("AST Blueprint mapping:")
    print(generate_ast_blueprint(vulnerable_code))