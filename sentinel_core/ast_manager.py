"""
SentinelAI -- Surgical AST Tool
================================
Precisely extracts and replaces individual functions in a Python source
file using Tree-Sitter byte ranges.  Because every splice operates on
raw bytes with exact AST boundaries, surrounding code is *never* corrupted.
"""

from typing import Optional, Tuple

from tree_sitter import Language, Parser
import tree_sitter_python

# ── Tree-Sitter Setup (module-level, reused across calls) ─────────────
PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)


# ---------------------------------------------------------------------- #
#  Private helper                                                         #
# ---------------------------------------------------------------------- #
def _find_function_node(root_node, function_name: str):
    """
    Depth-first search of the AST for a `function_definition` node
    whose `name` field matches *function_name*.

    Returns the matching node, or None.
    """
    if root_node.type == "function_definition":
        name_node = root_node.child_by_field_name("name")
        if name_node and name_node.text.decode("utf-8") == function_name:
            return root_node

    for child in root_node.children:
        result = _find_function_node(child, function_name)
        if result is not None:
            return result

    return None


def _locate_function_bytes(
    file_path: str, function_name: str
) -> Tuple[bytes, int, int]:
    """
    Read *file_path* in binary mode, parse its AST, and return
    ``(raw_bytes, start_byte, end_byte)`` for the target function.

    Raises ``ValueError`` if the function is not found.
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    tree = parser.parse(raw)
    node = _find_function_node(tree.root_node, function_name)

    if node is None:
        raise ValueError(
            f"Function '{function_name}' not found in '{file_path}'"
        )

    return raw, node.start_byte, node.end_byte


# ---------------------------------------------------------------------- #
#  Phase 2 -- Extraction                                                   #
# ---------------------------------------------------------------------- #
def extract_function(file_path: str, function_name: str) -> str:
    """
    Return the exact source text of *function_name* inside *file_path*
    by slicing on Tree-Sitter byte boundaries.
    """
    raw, start, end = _locate_function_bytes(file_path, function_name)
    return raw[start:end].decode("utf-8")


# ---------------------------------------------------------------------- #
#  Phase 3 -- Injection                                                    #
# ---------------------------------------------------------------------- #
def inject_patch(
    file_path: str, function_name: str, patched_code: str
) -> None:
    """
    Replace *function_name* in *file_path* with *patched_code*.

    The file is reconstructed as::

        before_bytes + patched_code (utf-8) + after_bytes

    so nothing outside the function's AST span is touched.
    """
    raw, start, end = _locate_function_bytes(file_path, function_name)

    before = raw[:start]
    after = raw[end:]
    new_content = before + patched_code.encode("utf-8") + after

    with open(file_path, "wb") as f:
        f.write(new_content)

    print(f"[AST Manager] Patched '{function_name}' in '{file_path}'")


# ====================================================================== #
#  Phase 4 -- Evaluation Test                                              #
# ====================================================================== #
if __name__ == "__main__":
    TARGET_FILE = "test_repo/db_utils.py"
    TARGET_FUNC = "get_user"

    # ── Step 1: Extract the original vulnerable function ────────────
    original = extract_function(TARGET_FILE, TARGET_FUNC)
    print("EXTRACTED:")
    print(original)

    # ── Step 2: Define the Blue Team patch ──────────────────────────
    patched_code = (
        "def get_user(uid):\n"
        "    # SENTINEL-AI PATCHED\n"
        "    cursor.execute('SELECT * FROM users WHERE id=?', (uid,))\n"
        "    return cursor.fetchone()"
    )

    # ── Step 3: Inject the patch ────────────────────────────────────
    inject_patch(TARGET_FILE, TARGET_FUNC, patched_code)

    # ── Step 4: Verify the full file is intact ──────────────────────
    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        new_contents = f.read()

    print("\nNEW FILE CONTENTS:")
    print(new_contents)
