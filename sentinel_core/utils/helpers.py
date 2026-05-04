"""
helpers.py — Shared utility helpers for sentinel_core.
"""


def truncate(s: str, max_length: int = 80) -> str:
    """Truncate a string for display, adding ellipsis if shortened."""
    return s if len(s) <= max_length else s[:max_length] + "..."


def format_flow_path(path: list) -> str:
    """Format a flow path list into a readable arrow chain."""
    return " -> ".join(path) if path else "<direct>"


def safe_line_preview(code: str, line: int, context: int = 0) -> str:
    """Extract a line (and optional context) from source code."""
    lines = code.split("\n")
    if line < 1 or line > len(lines):
        return ""
    start = max(0, line - 1 - context)
    end = min(len(lines), line + context)
    return "\n".join(lines[start:end])
