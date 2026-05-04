import ast
import textwrap

def build_combined_app(app_code: str, exploit_code: str) -> str:
    """Wrap the generated snippet into a runnable generic environment."""
    function_name = None
    try:
        tree = ast.parse(app_code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_name = node.name
                break
    except SyntaxError:
        pass

    if not function_name:
        function_name = "target_function" # Fallback

    # Create generic wrapper
    wrapped_code = f"""
import sys
import os
import asyncio
import json

# --- Patched logic ---
{app_code}

# --- Standard entrypoint ---
def run_app(*args, **kwargs):
    try:
        import inspect
        if inspect.iscoroutinefunction({function_name}):
            result = asyncio.run({function_name}(*args, **kwargs))
        else:
            result = {function_name}(*args, **kwargs)
        print("APP_OK")
        return result
    except Exception as e:
        import sys
        print(f"APP_ERROR: {{str(e)}}", file=sys.stderr)
        raise e

# --- Exploit logic ---
{exploit_code}
"""
    return wrapped_code.strip() + "\n"
