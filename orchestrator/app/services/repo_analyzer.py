"""
repo_analyzer.py — Analyzes repository size to determine the optimal scan mode.
"""

import os
from typing import Dict, Any

# Thresholds for adaptive mode selection
MAX_FILES_FOR_FULL = 20
MAX_LINES_FOR_FULL = 5000

EXCLUDED_DIRS = {".git", "node_modules", "venv", "__pycache__", ".idea", ".vscode"}


def analyze_repo(repo_path: str) -> Dict[str, Any]:
    """
    Walk the repository and count Python files + total lines of code.

    Returns:
        dict with keys: file_count, total_lines, recommended_mode
    """
    file_count = 0
    total_lines = 0

    for root, dirs, files in os.walk(repo_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]

        for file in files:
            if file.endswith(".py") and not file.startswith('.'):
                file_count += 1
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8", errors="ignore") as f:
                        total_lines += sum(1 for _ in f)
                except:
                    continue

    if file_count <= MAX_FILES_FOR_FULL and total_lines <= MAX_LINES_FOR_FULL:
        recommended_mode = "full"
    else:
        recommended_mode = "detect_only"

    return {
        "file_count": file_count,
        "total_lines": total_lines,
        "recommended_mode": recommended_mode,
    }
