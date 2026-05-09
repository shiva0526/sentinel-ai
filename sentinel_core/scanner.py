"""
SentinelAI — Semantic Scanner Module
=====================================
Ingests a Python repository, parses it into individual functions using
Tree-Sitter, and stores them in a ChromaDB vector database for
semantic security analysis.
"""

import os
import shutil
from typing import List, Dict, Any

import chromadb
from tree_sitter import Language, Parser
import tree_sitter_python


class SentinelScanner:
    """
    Core scanner that combines AST-level code parsing with vector-based
    semantic search to surface security-relevant functions from a codebase.
    """

    def __init__(self, db_path: str = "./sentinel_db"):
        # ── ChromaDB Setup ──────────────────────────────────────────
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="codebase")

        # ── Tree-Sitter Setup ──────────────────────────────────────
        self.language = Language(tree_sitter_python.language())
        self.parser = Parser(self.language)

    # ------------------------------------------------------------------ #
    #  Ingestion Logic                                                     #
    # ------------------------------------------------------------------ #
    def ingest_repo(self, repo_path: str) -> int:
        """
        Recursively walk *repo_path*, parse every `.py` file, extract
        each function definition, and upsert it into ChromaDB.

        Returns the total number of functions ingested.
        """
        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for root, _dirs, files in os.walk(repo_path):
            for filename in files:
                if not filename.endswith(".py"):
                    continue

                filepath = os.path.join(root, filename)

                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    source_code = f.read()

                tree = self.parser.parse(bytes(source_code, "utf-8"))
                functions = self._extract_functions(tree.root_node, source_code)

                for func in functions:
                    doc_id = f"{filepath}::{func['name']}"
                    ids.append(doc_id)
                    documents.append(func["code"])
                    metadatas.append(
                        {
                            "file": filepath,
                            "function_name": func["name"],
                            "line_number": func["line_number"],
                        }
                    )

        if ids:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)

        print(f"[SentinelScanner] Ingested {len(ids)} functions from '{repo_path}'")
        return len(ids)

    # ------------------------------------------------------------------ #
    #  Detection Logic                                                     #
    # ------------------------------------------------------------------ #
    def find_threats(
        self, threat_query: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query ChromaDB for the *top_k* functions whose source code is
        most semantically similar to *threat_query*.

        Returns a list of dicts with keys:
            file, function_name, code, confidence_score
        """
        results = self.collection.query(
            query_texts=[threat_query],
            n_results=top_k,
        )

        threats: List[Dict[str, Any]] = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            # ChromaDB returns L2 distance by default; convert to a
            # 0-1 confidence score (lower distance → higher confidence).
            confidence = round(1 / (1 + distance), 4)

            threats.append(
                {
                    "file": results["metadatas"][0][i]["file"],
                    "function_name": results["metadatas"][0][i]["function_name"],
                    "code": results["documents"][0][i],
                    "confidence_score": confidence,
                }
            )

        return threats

    # ------------------------------------------------------------------ #
    #  Private Helpers                                                     #
    # ------------------------------------------------------------------ #
    def _extract_functions(self, node, source_code: str) -> List[Dict[str, Any]]:
        """
        Walk the Tree-Sitter AST and collect every `function_definition`
        node's name, full source text, and starting line number.
        """
        functions: List[Dict[str, Any]] = []

        if node.type == "function_definition":
            # The first child of type `identifier` is the function name.
            name_node = node.child_by_field_name("name")
            func_name = name_node.text.decode("utf-8") if name_node else "<anonymous>"

            func_code = source_code[node.start_byte : node.end_byte]
            line_number = node.start_point[0] + 1  # 1-indexed

            functions.append(
                {
                    "name": func_name,
                    "code": func_code,
                    "line_number": line_number,
                }
            )

        # Recurse into children to catch nested / class-level methods too.
        for child in node.children:
            functions.extend(self._extract_functions(child, source_code))

        return functions


# ====================================================================== #
#  Phase 3 — Evaluation Test                                              #
# ====================================================================== #
if __name__ == "__main__":
    import textwrap

    TEST_DIR = "test_repo"

    # ── 1. Create test repo ─────────────────────────────────────────
    os.makedirs(TEST_DIR, exist_ok=True)

    # Safe utility function
    with open(os.path.join(TEST_DIR, "math_utils.py"), "w") as f:
        f.write(
            textwrap.dedent(
                """\
                def add(a, b):
                    \"\"\"Return the sum of two numbers.\"\"\"
                    return a + b
                """
            )
        )

    # Vulnerable database utility
    with open(os.path.join(TEST_DIR, "db_utils.py"), "w") as f:
        f.write(
            textwrap.dedent(
                """\
                import sqlite3

                def get_user(uid):
                    conn = sqlite3.connect("app.db")
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM users WHERE id={uid}")
                    return cursor.fetchone()
                """
            )
        )

    # ── 2. Clean previous DB so the demo is reproducible ────────────
    db_path = "./sentinel_db"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    # ── 3. Ingest & Scan ────────────────────────────────────────────
    scanner = SentinelScanner(db_path=db_path)
    scanner.ingest_repo(TEST_DIR)

    print("\n" + "=" * 60)
    print("  THREAT SCAN RESULTS")
    print("=" * 60)

    threats = scanner.find_threats("SQL injection using f-strings")

    for idx, threat in enumerate(threats, start=1):
        print(f"\n-- Match #{idx} ({'%.2f' % (threat['confidence_score'] * 100)}% confidence) --")
        print(f"  File     : {threat['file']}")
        print(f"  Function : {threat['function_name']}")
        print(f"  Code     :\n{textwrap.indent(threat['code'], '    ')}")

    print("\n" + "=" * 60)
