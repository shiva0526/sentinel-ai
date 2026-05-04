"""
mechanic.py — Blue Team Patch Generator Agent.
"""

import re
from ..graph.state import WarRoomState
from ..services.llm_service import generate_with_fallback, get_blue_client


def mechanic_agent(state: WarRoomState):
    print("\n[2] Mechanic (Blue Team): Writing secure patch...")

    # Check if retrying after sandbox failure
    feedback = ""
    if state.get("test_status") == "FAIL":
        feedback = f"\nWARNING: Your previous patch FAILED. Crash logs:\n{state['test_logs']}\nFix the error!"

    prompt = f"""
    You are an expert DevSecOps Engineer. Patch the vulnerable Python code.
    Use the AST blueprint to understand the structure.
    
    Vulnerable Code:
    ```python
    {state['original_code']}
    ```
    
    AST Blueprint:
    {state.get('ast_graph', 'N/A')}
    {feedback}
    
    Rewrite the code to be secure (e.g., prevent SQL injection, sanitize inputs).
    Your patch must:
    - Be a complete, self-contained function definition.
    - Not depend on undefined variables. If it requires external dependencies like a database connection (`db`), mock or define them minimally within the snippet so it can be executed standalone.
    - Be compatible with being imported and called directly.
    
    ONLY output raw Python code. No markdown formatting. No explanations.
    """

    patched_code = generate_with_fallback(get_blue_client(), prompt)
    patched_code = re.sub(r"^```python\n|```$", "", patched_code, flags=re.MULTILINE).strip()

    print("--- PATCH GENERATED ---")
    print(patched_code)
    print("-----------------------\n")

    return {"proposed_patch": patched_code}
