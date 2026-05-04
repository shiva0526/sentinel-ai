"""
seed_examples.py — Seed the system with example vulnerable code snippets.
"""

EXAMPLES = {
    "sql_injection": {
        "name": "SQL Injection via f-string",
        "url": "https://raw.githubusercontent.com/example/vuln/main/sqli.py",
        "code": '''
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")
    return cursor.fetchall()
''',
    },
    "command_injection": {
        "name": "Command Injection via os.system",
        "url": "https://raw.githubusercontent.com/example/vuln/main/cmdi.py",
        "code": '''
import os

def run_command(user_input):
    os.system("ls " + user_input)
''',
    },
    "xss": {
        "name": "XSS via render_template_string",
        "url": "https://raw.githubusercontent.com/example/vuln/main/xss.py",
        "code": '''
from flask import request, render_template_string

def page():
    name = request.args.get("name")
    return render_template_string("<h1>Hello " + name + "</h1>")
''',
    },
}


if __name__ == "__main__":
    print("Available test examples:")
    for key, ex in EXAMPLES.items():
        print(f"  [{key}] {ex['name']}")
    print(f"\nTotal: {len(EXAMPLES)} examples loaded.")
