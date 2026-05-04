"""
main_detector.py — CLI entry point and test harness for SentinelAI's
rule-based vulnerability detection engine.

Run:
    python main_detector.py          # all test cases
    python main_detector.py --json   # JSON output
    python main_detector.py --verbose  # show AST + flow debug info
"""

import sys
import argparse

# Allow running from project root
sys.path.insert(0, ".")

from sentinel_ai.detector.analyzer import VulnerabilityAnalyzer


# ══════════════════════════════════════════════════════════════════════════════
# TEST CASES — real-world-style vulnerable Python snippets
# ══════════════════════════════════════════════════════════════════════════════

TEST_CASES = {

    # ── 1. Classic SQL Injection ─────────────────────────────────────────
    "SQL Injection (string concat)": '''\
user_id = input()
query = "SELECT * FROM users WHERE id = " + user_id
execute(query)
''',

    # ── 2. SQL Injection via f-string ────────────────────────────────────
    "SQL Injection (f-string)": '''\
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()
''',

    # ── 3. Command Injection ─────────────────────────────────────────────
    "Command Injection (os.system)": '''\
import os
filename = input("Enter filename: ")
os.system("cat " + filename)
''',

    # ── 4. Command Injection (subprocess) ────────────────────────────────
    "Command Injection (subprocess)": '''\
import subprocess
user_cmd = input("Enter command: ")
cmd = "ls " + user_cmd
subprocess.run(cmd, shell=True)
''',

    # ── 5. Code Injection (eval) ─────────────────────────────────────────
    "Code Injection (eval)": '''\
expression = input("Enter math expression: ")
result = eval(expression)
print(result)
''',

    # ── 6. Hardcoded Secrets ─────────────────────────────────────────────
    "Hardcoded Secrets": '''\
api_key = "AIzaSyBzRg7rlHVi43nsSOo2maVOpvM2N1g_9Ps"
password = "SuperSecret123!@#"
db_url = "postgres://admin:password@localhost/db"
''',

    # ── 7. XSS via render_template_string ────────────────────────────────
    "XSS (Flask template)": '''\
from flask import request, render_template_string
def page():
    name = request.args.get("name")
    html = "<h1>Hello " + name + "</h1>"
    return render_template_string(html)
''',

    # ── 8. Multi-vulnerability file ──────────────────────────────────────
    "Multi-vulnerability combo": '''\
import os
import sqlite3

api_token = "sk-abc123def456ghi789jklmnopqrstuvwxyz0123"

def process(user_input):
    query = "SELECT * FROM data WHERE val = '" + user_input + "'"
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(query)
    
    cmd = "echo " + user_input
    os.system(cmd)
    
    result = eval(user_input)
    return result
''',

    # ── 9. Safe code (should produce no findings) ────────────────────────
    "Safe code (no vulnerabilities)": '''\
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
''',
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="SentinelAI Vulnerability Detector")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show AST/flow debug info")
    parser.add_argument("--file", "-f", type=str, help="Scan a specific Python file instead of test cases")
    parser.add_argument("--llm", action="store_true", help="Show LLM-formatted prompt output")
    args = parser.parse_args()

    analyzer = VulnerabilityAnalyzer(verbose=args.verbose)

    # ── Scan a specific file ────────────────────────────────────────────
    if args.file:
        print(f"\n🎯 Scanning file: {args.file}\n")
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()

        if args.json:
            print(analyzer.run_json(source))
        elif args.llm:
            findings = analyzer.run(source)
            print(analyzer.format_for_llm(findings))
        else:
            print(analyzer.run_report(source))
        return

    # ── Run all test cases ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  🛡️  SentinelAI Rule-Based Vulnerability Detection Engine")
    print("  Running all test cases...")
    print("=" * 70)

    total_findings = 0

    for name, code in TEST_CASES.items():
        print(f"\n{'─'*70}")
        print(f"  📋 Test Case: {name}")
        print(f"{'─'*70}")
        print(f"  Code:")
        for i, line in enumerate(code.strip().split("\n"), 1):
            print(f"    {i:3d} │ {line}")
        print()

        if args.json:
            output = analyzer.run_json(code)
            print(output)
        elif args.llm:
            findings = analyzer.run(code)
            print(analyzer.format_for_llm(findings))
        else:
            report = analyzer.run_report(code)
            print(report)

        findings = analyzer.run(code)
        total_findings += len(findings)

    print(f"\n{'='*70}")
    print(f"  🏁 TOTAL: {total_findings} vulnerabilities across {len(TEST_CASES)} test cases")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
