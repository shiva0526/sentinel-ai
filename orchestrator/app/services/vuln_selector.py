"""
vuln_selector.py — Analyzes files and selects the most vulnerable one.
"""

from typing import List, Optional

from .detector_client import detect_vulnerabilities

# Priority scoring logic
VULN_SCORES = {
    "SQL Injection": 10,
    "Command Injection": 9,
    "Code Injection": 8,
    "Hardcoded Secret": 7,
    "Hardcoded Secrets": 7,
    "XSS": 6,
    "Insecure Deserialization": 6
}

def _get_finding_score(vuln_type: str) -> int:
    """Return the score for a specific vulnerability type."""
    # Handle slight variations in naming
    for key, score in VULN_SCORES.items():
        if key.lower() in vuln_type.lower():
            return score
    return 5  # Default score for unknown vulnerabilities

def find_vulnerable_file(files: List[str]) -> Optional[dict]:
    """
    Run rule-based detector on each file, identify vulnerabilities,
    and return the file with the highest score.
    """
    best_candidate = None
    highest_score = -1

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
            
            # Skip empty files
            if not code.strip():
                continue
                
            findings = detect_vulnerabilities(code)
            
            if findings:
                # Calculate max score from findings in this file
                max_file_score = max(_get_finding_score(f.vuln_type) for f in findings)
                
                if max_file_score > highest_score:
                    highest_score = max_file_score
                    best_candidate = {
                        "file_path": file_path,
                        "code": code,
                        "findings": findings,
                        "score": max_file_score
                    }
                    
        except Exception as e:
            print(f"    [!] Error scanning file {file_path}: {e}")
            
    return best_candidate
