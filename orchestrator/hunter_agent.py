import re
import os
import sys
import requests
from typing import Dict, Any
from google.genai import types

# Add the project root to path so we can import sentinel_ai
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sentinel_ai.detector.analyzer import VulnerabilityAnalyzer


def search_web_for_cve(query: str) -> str:
    """Searches the web for vulnerability intelligence, CVE details, and exploit methods.
    Use this tool when you need to confirm the severity, find the exact CVE ID, or research how a vulnerability is typically exploited.
    """
    try:
        res = requests.post("http://localhost:8081/search", json={"query": query}, timeout=15)
        return res.text
    except Exception as e:
        return f"Search failed: {e}"


# Initialize the rule-based detection engine
_analyzer = VulnerabilityAnalyzer(verbose=False)


# We will pass the Gemini client from graph.py into this agent
def run_pentagi_hunter(state: Dict[str, Any], ai_client) -> Dict[str, Any]:
    repo_url = state.get("repo_url")
    print(f"\n[TARGET] [0] PentAGI Hunter: Scanning target repository: {repo_url}")
    
    # 1. Fetch the code (For simplicity, assuming a raw github file link is passed)
    # If it's a full repo, the AI would normally use a GitHub API tool here.
    try:
        if "raw.githubusercontent.com" in repo_url:
            code_content = requests.get(repo_url).text
        else:
            # Fallback for testing if a raw URL isn't provided
            code_content = """
import sqlite3
def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Vulnerable SQL Query
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
    return cursor.fetchall()
            """
            print("   [WARN] Not a raw file URL. Using simulated vulnerable code for testing.")
    except Exception as e:
        return {"test_status": "FAIL", "test_logs": f"Failed to fetch repo: {str(e)}"}

    print("   [OK] Code fetched.")

    # ══════════════════════════════════════════════════════════════════
    # 2. NEW: Run the rule-based detection engine FIRST (deterministic)
    # ══════════════════════════════════════════════════════════════════
    print("   [SCAN] Running rule-based vulnerability detection engine...")
    rule_findings = _analyzer.run(code_content)

    if rule_findings:
        # ── Rule engine found vulnerabilities — use structured data ──
        print(f"   [HIT] Rule engine detected {len(rule_findings)} vulnerability(ies)!")
        for i, f in enumerate(rule_findings, 1):
            print(f"      [{i}] {f.vuln_type} ({f.confidence.value}) — {f.cwe} @ line {f.line}")

        # Use the highest-confidence finding as the primary CVE
        primary = rule_findings[0]
        cve_id = primary.cwe

        # Build a structured prompt for the LLM to VALIDATE (not guess)
        structured_prompt = _analyzer.format_for_llm(rule_findings)

        validation_prompt = f"""
        You are an expert Application Security Researcher validating findings from an automated scanner.
        
        Target Code:
        ```python
        {code_content}
        ```
        
        Automated Scanner Results:
        {structured_prompt}
        
        For each finding:
        1. Confirm if it is a TRUE POSITIVE or FALSE POSITIVE
        2. If true positive, identify the exact vulnerable lines
        
        Return your validation in this format:
        CVE_ID: {cve_id}
        VULNERABLE_SNIPPET: 
        [Only the exact lines of vulnerable code from the most critical finding]
        """

        # 3. Send to LLM for validation (not blind guessing)
        print("   [AI] Sending structured findings to AI for validation...")
        chat = ai_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                temperature=0.2,
                tools=[search_web_for_cve]
            )
        )
        response = chat.send_message(validation_prompt)
        result = response.text

    else:
        # ── No rule-based findings — fall back to pure LLM scan ─────
        print("   [INFO] No rule-based findings. Falling back to AI-powered scan...")

        hunter_prompt = f"""
        You are an elite, highly aggressive Application Security Researcher (Pentester).
        Your goal is to perform static analysis on the following source code and identify the most critical vulnerability.
        
        Target Code:
        ```python
        {code_content}
        ```
        
        Identify the vulnerability. 
        Return your findings in this exact format:
        CVE_ID: [Guess a CVE or use CWE-ID, e.g., CWE-89]
        VULNERABLE_SNIPPET: 
        [Only the exact lines of vulnerable code]
        """

        chat = ai_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                temperature=0.2,
                tools=[search_web_for_cve]
            )
        )
        
        print("   [AI] Analyzing code and checking web databases...")
        response = chat.send_message(hunter_prompt)
        result = response.text

    # 4. Parse the AI's findings
    cve_match = re.search(r"CVE_ID:\s*(.*)", result)
    snippet_match = re.search(r"VULNERABLE_SNIPPET:\s*(.*)", result, re.DOTALL)

    cve_id = cve_match.group(1).strip() if cve_match else "UNKNOWN-VULN"
    vulnerable_code = snippet_match.group(1).strip() if snippet_match else code_content

    print(f"   [ALERT] BUG FOUND! Type: {cve_id}")
    
    # Pass the findings directly to SentinelAI's War Room!
    return {
        "cve_id": cve_id,
        "original_code": vulnerable_code,
        "vulnerable_file": repo_url
    }

