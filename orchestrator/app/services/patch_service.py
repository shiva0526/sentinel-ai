"""
patch_service.py — Applies validated patches to source files.
"""

import os


def apply_patch(file_path: str, original_function: str, patched_function: str) -> bool:
    """
    Replace the original vulnerable snippet with the patched version in the given file.

    Args:
        file_path: Absolute path to the file to patch.
        original_function: The exact original code to replace.
        patched_function: The replacement code.

    Returns:
        True if patch was applied, False otherwise.
    """
    if not os.path.exists(file_path):
        print(f"    [!] Patch target not found: {file_path}")
        return False

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"    [!] Failed to read file: {e}")
        return False

    if original_function not in content:
        print(f"    [!] Original snippet not found in {file_path}. Patch skipped.")
        return False

    updated_content = content.replace(original_function, patched_function, 1)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
    except Exception as e:
        print(f"    [!] Failed to write patched file: {e}")
        return False

    return True
