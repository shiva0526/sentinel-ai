"""
patterns.py — Reusable pattern constants for vulnerability detection.

Centralises all keyword lists, dangerous function names, input sources,
and regex patterns so that rules.py and the rest of the engine can
reference them without duplication.
"""

import re

# ─── SQL Patterns ────────────────────────────────────────────────────────────

SQL_KEYWORDS = [
    "SELECT", "INSERT", "UPDATE", "DELETE",
    "DROP", "ALTER", "CREATE", "UNION",
    "WHERE", "FROM", "INTO", "VALUES",
]

SQL_PATTERN = re.compile(
    r"\b(?:" + "|".join(SQL_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# ─── Dangerous Sink Functions ────────────────────────────────────────────────

DANGEROUS_FUNCS = {
    # SQL execution
    "execute":       "SQL Execution",
    "executemany":   "SQL Execution",
    "raw":           "SQL Execution (Django ORM raw)",
    "executescript":  "SQL Execution",

    # OS / command injection
    "os.system":     "OS Command Execution",
    "os.popen":      "OS Command Execution",
    "system":        "OS Command Execution",
    "popen":         "OS Command Execution",

    # subprocess
    "subprocess.run":            "Subprocess Execution",
    "subprocess.call":           "Subprocess Execution",
    "subprocess.Popen":          "Subprocess Execution",
    "subprocess.check_output":   "Subprocess Execution",
    "subprocess.check_call":     "Subprocess Execution",

    # Dynamic code execution
    "eval":          "Dynamic Code Evaluation",
    "exec":          "Dynamic Code Execution",
    "compile":       "Dynamic Code Compilation",

    # Deserialization
    "pickle.loads":  "Insecure Deserialization",
    "yaml.load":     "Insecure YAML Deserialization",
    "marshal.loads": "Insecure Deserialization",
}

# ─── Input Sources ───────────────────────────────────────────────────────────

INPUT_FUNCTIONS = [
    "input",
]

INPUT_METHODS = [
    "request.GET",
    "request.POST",
    "request.args",
    "request.form",
    "request.json",
    "request.data",
    "request.values",
    "request.cookies",
    "request.headers",
]

INPUT_MODULES = [
    "sys.argv",
    "os.environ",
]

# ─── Secret / Hardcoded Credential Patterns ──────────────────────────────────

SECRET_PATTERNS = [
    # Generic API keys (long alphanumeric strings)
    re.compile(r"(?i)(api[_-]?key|apikey)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
    re.compile(r"(?i)(secret|token|password|passwd|pwd)\s*=\s*['\"][^'\"]{8,}['\"]"),
    # AWS-style keys
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # Generic long hex/base64 strings assigned to suspicious names
    re.compile(r"(?i)(key|secret|token)\s*=\s*['\"][A-Fa-f0-9]{32,}['\"]"),
]

# Quick name-based check for assignments
SECRET_VARIABLE_NAMES = re.compile(
    r"(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth|credential|private_key)",
)

# ─── HTML / XSS Sinks ───────────────────────────────────────────────────────

HTML_SINKS = [
    "render_template_string",   # Jinja2 — renders raw string as template
    "Markup",                   # Flask  — marks string as safe HTML
    "format_html",              # Django — but only if misused
    "HttpResponse",             # Django — raw response body
    "make_response",            # Flask  — raw response body
]

# ─── Sanitisation Indicators ─────────────────────────────────────────────────
# If any of these appear between source and sink, we lower confidence.

SANITIZERS = [
    "escape",
    "quote",
    "sanitize",
    "clean",
    "strip_tags",
    "bleach",
    "parameterize",
    "placeholder",
    "html.escape",
    "markupsafe.escape",
    "shlex.quote",
    "re.escape",
]
