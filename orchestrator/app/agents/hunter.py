"""
hunter.py — Vulnerability Hunter Agent.

Uses the rule-based detection engine first, falls back to LLM scanning.
"""

import re
import os
from google.genai import types

from ..graph.state import WarRoomState
from ..services.detector_client import format_findings_for_llm, get_primary_cwe
from ..services.arena_client import search_web
from ..services.llm_service import get_blue_client
from ..services.repo_service import fetch_repo, cleanup_repo
from ..services.file_scanner import get_code_files
from ..services.vuln_selector import find_vulnerable_file

def _search_web_for_cve(query: str) -> str:
    """Tool for Gemini automatic function calling — searches for CVE intel."""
    try:
        return search_web(query)
    except Exception as e:
        return f"Search failed: {e}"

def hunter_agent(state: WarRoomState):
    repo_url = state.get("repo_url")
    print(f"\n[0] Hunter Agent: Scanning target: {repo_url}")

    repo_path = None
    try:
        # 1. Fetch the repository
        repo_path = fetch_repo(repo_url)
        print("    [+] Repo fetched.")
        
        # 2. Scan for code files
        files = get_code_files(repo_path)
        print(f"    [*] Found {len(files)} relevant code files.")
        
        if not files:
            return {"test_status": "FAIL", "test_logs": "No Python code files found in the repository."}
            
        # 3. Find the most vulnerable file
        print("    [*] Running rule-based detection engine across all files...")
        result = find_vulnerable_file(files)
        
        ai_client = get_blue_client()
        
        if result:
            vuln_file_path = result["file_path"]
            # Convert absolute path to relative path for better display
            rel_file_path = os.path.relpath(vuln_file_path, repo_path)
            
            print(f"    [+] Engine detected vulnerability in {rel_file_path} (Score: {result['score']})")
            
            cve_id = get_primary_cwe(result["findings"])
            structured_prompt = format_findings_for_llm(result["findings"])
            
            validation_prompt = f"""
            You are an expert Application Security Researcher validating findings from an automated scanner.
            
            Target Code (File: {rel_file_path}):
            ```python
            {result['code']}
            ```
            
            Automated Scanner Results:
            {structured_prompt}
            
            For each finding, confirm if TRUE POSITIVE or FALSE POSITIVE.
            
            Return in this format:
            CVE_ID: {cve_id}
            VULNERABLE_SNIPPET: 
            [Only the exact vulnerable lines]
            """
            
            print("    [*] Sending structured findings to AI for validation...")
            chat = ai_client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(temperature=0.2, tools=[_search_web_for_cve])
            )
            response = chat.send_message(validation_prompt)
            llm_result = response.text
            
            # Parse AI findings
            cve_match = re.search(r"CVE_ID:\s*(.*)", llm_result)
            snippet_match = re.search(r"VULNERABLE_SNIPPET:\s*(.*)", llm_result, re.DOTALL)
            
            final_cve_id = cve_match.group(1).strip() if cve_match else "UNKNOWN-VULN"
            vulnerable_code = snippet_match.group(1).strip() if snippet_match else result["code"]
            
            print(f"    [!] BUG FOUND: {final_cve_id}")
            
            return {
                "cve_id": final_cve_id,
                "original_code": vulnerable_code,
                "vulnerable_file": rel_file_path,
                "repo_path": repo_path,
            }
            
        else:
            print("    [*] No rule-based findings found across any file. Falling back to AI scan...")
            
            # Concatenate up to 100KB of files for the LLM fallback
            combined_code = ""
            for f_path in files:
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    rel_path = os.path.relpath(f_path, repo_path)
                    file_chunk = f"--- File: {rel_path} ---\n{content}\n\n"
                    if len(combined_code) + len(file_chunk) > 100 * 1024:
                        print("    [!] Token limit approached, truncating files for LLM fallback.")
                        break
                    combined_code += file_chunk
                    
            hunter_prompt = f"""
            You are an elite Application Security Researcher.
            Perform static analysis on the following code files and identify the most critical vulnerability.
            
            Target Files:
            {combined_code}
            
            Return in this format:
            CVE_ID: [CWE-ID]
            VULNERABLE_SNIPPET: 
            [Only the vulnerable lines]
            """
            
            chat = ai_client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(temperature=0.2, tools=[_search_web_for_cve])
            )
            print("    [*] Analyzing concatenated code with AI...")
            response = chat.send_message(hunter_prompt)
            llm_result = response.text
            
            cve_match = re.search(r"CVE_ID:\s*(.*)", llm_result)
            snippet_match = re.search(r"VULNERABLE_SNIPPET:\s*(.*)", llm_result, re.DOTALL)
            
            final_cve_id = cve_match.group(1).strip() if cve_match else "UNKNOWN-VULN"
            vulnerable_code = snippet_match.group(1).strip() if snippet_match else combined_code
            
            print(f"    [!] BUG FOUND (AI Fallback): {final_cve_id}")
            
            return {
                "cve_id": final_cve_id,
                "original_code": vulnerable_code,
                "vulnerable_file": "Multiple Files (Fallback)",
                "repo_path": repo_path,
            }
            
    except Exception as e:
        return {"test_status": "FAIL", "test_logs": f"Hunter Agent failed: {str(e)}"}
