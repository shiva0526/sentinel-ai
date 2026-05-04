"""
flow_tracker.py — Taint-style data flow tracker for the SentinelAI detection engine.

Tracks how user-controlled input variables propagate through assignments
and eventually reach dangerous sink functions.  Returns a list of FlowChain
objects, each representing a concrete source → … → sink path.
"""

from typing import Dict, List, Set

from .models import ASTData, FlowChain, InputNode, AssignmentNode, CallNode
from ..utils.patterns import DANGEROUS_FUNCS, HTML_SINKS


class DataFlowTracker:
    """
    Builds a taint propagation map from ASTData and resolves which
    dangerous sinks are reachable from which input sources.
    """

    def __init__(self, ast_data: ASTData):
        self.ast_data = ast_data

        # taint_map:  variable_name → set of original input variable names
        self.taint_map: Dict[str, Set[str]] = {}

        # propagation_graph:  variable → list of variables it flows into
        self.propagation_graph: Dict[str, List[str]] = {}

        # Reverse lookup: input variable → InputNode (for source metadata)
        self._input_lookup: Dict[str, InputNode] = {}

    # ── Public API ──────────────────────────────────────────────────────

    def track(self) -> List[FlowChain]:
        """Run the full flow analysis and return all source→sink chains."""
        self._seed_inputs()
        self._propagate_assignments()
        return self._resolve_sinks()

    # ── Step 1: Seed the taint map with input sources ───────────────────

    def _seed_inputs(self):
        for inp in self.ast_data.inputs:
            self.taint_map[inp.variable] = {inp.variable}
            self._input_lookup[inp.variable] = inp

    # ── Step 2: Propagate taint through assignments ─────────────────────

    def _propagate_assignments(self):
        """
        Iterate over assignments and propagate taint.
        We do multiple passes to handle transitive flows:
            user_id → query → final_query
        """
        # Sort assignments by line number for natural order
        assignments = sorted(self.ast_data.assignments, key=lambda a: a.line)

        changed = True
        max_passes = 10  # prevent infinite loops
        passes = 0

        while changed and passes < max_passes:
            changed = False
            passes += 1

            for assign in assignments:
                tainted_sources: Set[str] = set()

                # Check each variable name referenced in the RHS
                for name in assign.value_names:
                    if name in self.taint_map:
                        tainted_sources.update(self.taint_map[name])
                        # Track the propagation edge
                        self.propagation_graph.setdefault(name, []).append(assign.target)

                if tainted_sources:
                    existing = self.taint_map.get(assign.target, set())
                    merged = existing | tainted_sources
                    if merged != existing:
                        self.taint_map[assign.target] = merged
                        changed = True

    # ── Step 3: Check which sinks consume tainted variables ─────────────

    def _resolve_sinks(self) -> List[FlowChain]:
        chains: List[FlowChain] = []

        for call in self.ast_data.calls:
            # Is this call a dangerous sink?
            if not self._is_dangerous_sink(call):
                continue

            # Check if any of the call's arguments are tainted
            for arg_name in call.args_names:
                if arg_name not in self.taint_map:
                    continue

                # For each original input source that reaches this sink
                for source_var in self.taint_map[arg_name]:
                    inp = self._input_lookup.get(source_var)
                    if not inp:
                        continue

                    path = self._build_path(source_var, arg_name)

                    chains.append(FlowChain(
                        source_var=source_var,
                        source_kind=inp.source,
                        source_line=inp.line,
                        sink_func=call.func_name,
                        sink_line=call.line,
                        path=path,
                    ))

        return chains

    # ── Helpers ─────────────────────────────────────────────────────────

    def _is_dangerous_sink(self, call: CallNode) -> bool:
        """Check if a call matches any known dangerous function or HTML sink."""
        # Direct match: "execute", "os.system", etc.
        if call.func_name in DANGEROUS_FUNCS:
            return True
        # Method match: "cursor.execute" → check "execute"
        if "." in call.func_name:
            method = call.func_name.split(".")[-1]
            if method in DANGEROUS_FUNCS:
                return True
        # HTML sinks for XSS detection
        func_base = call.func_name.split(".")[-1]
        if func_base in HTML_SINKS or call.func_name in HTML_SINKS:
            return True
        return False

    def _build_path(self, source: str, sink_arg: str) -> List[str]:
        """
        Reconstruct the shortest taint path from source to sink_arg
        using BFS on the propagation graph.
        """
        if source == sink_arg:
            return [source]

        visited: Set[str] = set()
        queue: List[List[str]] = [[source]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            if current == sink_arg:
                return path

            if current in visited:
                continue
            visited.add(current)

            for neighbour in self.propagation_graph.get(current, []):
                if neighbour not in visited:
                    queue.append(path + [neighbour])

        # Fallback: couldn't trace exact path, return endpoints
        return [source, sink_arg]


# ─── Public API ──────────────────────────────────────────────────────────────

def track_flows(ast_data: ASTData) -> List[FlowChain]:
    """
    Analyse data flows in parsed AST data and return all
    input-source → dangerous-sink chains.

    Args:
        ast_data: Parsed ASTData from ast_parser.parse_code().

    Returns:
        List of FlowChain objects describing tainted data paths.
    """
    tracker = DataFlowTracker(ast_data)
    return tracker.track()
