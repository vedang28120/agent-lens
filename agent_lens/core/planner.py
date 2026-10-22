import os
import networkx as nx
from typing import Dict, List, Optional, Any, Set
from .cartography import CodebaseCartographer


class RefactorPlanner:
    """Generates topologically sorted, blast-ordered refactor execution plans for AI agents."""

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def plan_refactor(self, target_file: str, target_symbol: Optional[str] = None, objective: str = "Refactor") -> Dict[str, Any]:
        """Creates a step-by-step ordered refactor DAG from target up to callers and tests."""
        if not self.cart.file_results:
            self.cart.scan()

        norm_file = target_file.replace("\\", "/")
        blast = self.cart.calculate_blast_radius(norm_file, symbol_name=target_symbol)

        affected_files = set([norm_file] + blast["impacted_files"] + blast["related_tests"])

        # Build sub-DAG of affected files
        G = nx.DiGraph()
        for f in affected_files:
            G.add_node(f)

        for f in affected_files:
            dependents = self.cart.file_dependents.get(f, set())
            for dep in dependents:
                if dep in affected_files and dep != f:
                    # Edge: f must be modified BEFORE dep (dependency order)
                    G.add_edge(f, dep)

        # Topological sort (or fallback to degree-based if cycles exist)
        try:
            sorted_files = list(nx.topological_sort(G))
        except nx.NetworkXUnfeasible:
            # Handle circular cycle gracefully by in-degree
            sorted_files = sorted(G.nodes, key=lambda n: G.in_degree(n))

        # Categorize steps
        steps = []
        for idx, file_path in enumerate(sorted_files, 1):
            is_target = (file_path == norm_file)
            is_test = "test" in file_path.lower()

            if is_target:
                action = "CORE_MUTATION"
                desc = f"Modify target implementation: `{target_symbol or 'file'}` in `{file_path}`"
                risk = blast["risk_level"]
            elif is_test:
                action = "UPDATE_TESTS"
                desc = f"Update test assertions and mock data in `{file_path}`"
                risk = "LOW"
            else:
                action = "UPDATE_CALLERS"
                desc = f"Adapt downstream callers and imported references in `{file_path}`"
                risk = "MEDIUM"

            # Inbound requirements
            predecessors = list(G.predecessors(file_path))

            steps.append({
                "step_number": idx,
                "file": file_path,
                "action": action,
                "description": desc,
                "risk": risk,
                "prerequisites": predecessors,
                "preflight_cmd": f"python run.py preflight {file_path}",
            })

        # Final verification step
        steps.append({
            "step_number": len(steps) + 1,
            "file": "ALL",
            "action": "FINAL_VERIFICATION",
            "description": "Run test suite and ghost-patch safety audit",
            "risk": "LOW",
            "prerequisites": [s["file"] for s in steps[:-1]],
            "preflight_cmd": "python -m pytest tests -v",
        })

        return {
            "objective": objective,
            "target_file": norm_file,
            "target_symbol": target_symbol,
            "total_steps": len(steps),
            "risk_level": blast["risk_level"],
            "impacted_files_count": len(blast["impacted_files"]),
            "affected_tests_count": len(blast["related_tests"]),
            "execution_steps": steps,
        }

    def format_plan_markdown(self, plan: Dict[str, Any]) -> str:
        """Formats the refactor plan into markdown instructions."""
        lines = [
            f"## [REFACTOR PLAN] Objective: {plan['objective']}",
            f"Target: `{plan['target_file']}`" + (f" -> `{plan['target_symbol']}`" if plan['target_symbol'] else ""),
            f"Overall Risk: **{plan['risk_level']}** | Total Steps: {plan['total_steps']}",
            "",
            "### Execution Sequence (Topologically Ordered):",
        ]

        for s in plan["execution_steps"]:
            badge = f"[{s['action']}]"
            lines.append(f"**Step {s['step_number']}**: {badge} `{s['file']}` (Risk: {s['risk']})")
            lines.append(f"  - {s['description']}")
            if s["prerequisites"]:
                lines.append(f"  - *Prerequisites*: {', '.join(s['prerequisites'])}")
            lines.append(f"  - *Verification*: `{s['preflight_cmd']}`")
            lines.append("")

        return "\n".join(lines)
