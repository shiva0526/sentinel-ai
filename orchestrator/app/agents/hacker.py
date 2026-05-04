"""
hacker.py — Red Team Exploit Generator Agent.
"""

import re
from ..graph.state import WarRoomState
from ..services.llm_service import generate_with_fallback, get_red_client


def hacker_agent(state: WarRoomState):
    print("\n[3] Hacker (Red Team): Writing exploit payload...")

    prompt = f"""
    You are an expert Red Team Security Researcher.
    Write a Python exploit payload to test if a security patch is effective.
    
    Original Vulnerable Code:
    ```python
    {state['original_code']}
    ```
    
    Patched Code (Blue Team):
    ```python
    {state['proposed_patch']}
    ```
    
    Write a script that attempts to attack the patched code.
    1. You MUST call `run_app(input_value)` (which wraps the patched code) with your malicious payload.
    2. Use classic attack payloads (SQL injection, command injection, etc.).
    3. You MUST print EXACTLY:
       "EXPLOIT_SUCCESS" if the attack works (i.e. the patch failed).
       "EXPLOIT_FAILED" if the attack is blocked (i.e. the patch works).
    
    ONLY output raw Python code. No markdown. No explanations.
    """

    exploit = generate_with_fallback(get_red_client(), prompt)
    exploit = re.sub(r"^```python\n|```$", "", exploit, flags=re.MULTILINE).strip()

    print("--- EXPLOIT GENERATED ---")
    print(exploit)
    print("-------------------------\n")

    return {"exploit_payload": exploit}
