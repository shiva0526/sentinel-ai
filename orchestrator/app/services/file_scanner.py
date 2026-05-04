"""
file_scanner.py — Recursively scans a repository for relevant source files.
"""

import os
from typing import List

MAX_FILES = 50
MAX_FILE_SIZE_BYTES = 200 * 1024  # 200KB

EXCLUDED_DIRS = {".git", "node_modules", "venv", "__pycache__", ".idea", ".vscode"}

def get_code_files(repo_path: str) -> List[str]:
    """
    Recursively scan the repository directory and extract up to MAX_FILES relevant source files.
    """
    code_files = []
    
    for root, dirs, files in os.walk(repo_path):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]
        
        for file in files:
            if file.endswith(".py") and not file.startswith('.'):
                file_path = os.path.join(root, file)
                
                # Check file size
                if os.path.getsize(file_path) > MAX_FILE_SIZE_BYTES:
                    print(f"    [!] Skipping large file: {file_path}")
                    continue
                
                code_files.append(file_path)
                
                if len(code_files) >= MAX_FILES:
                    print(f"    [!] File limit reached ({MAX_FILES}). Stopping scan.")
                    return code_files
                    
    return code_files
