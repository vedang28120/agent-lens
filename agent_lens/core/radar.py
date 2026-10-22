import os
import networkx as nx
from typing import Dict, List, Any, Set, Tuple
from .cartography import CodebaseCartographer


class ArchitectureRadar:
    """Analyzes architectural health, circular dependencies, God Nodes, and orphan symbols."""

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def analyze(self) -> Dict[str, Any]:
        """Runs complete architectural scan and returns metrics, antipatterns, and health score."""
        # Ensure fresh cartography data
        if not self.cart.file_results:
            self.cart.scan()

        file_graph = self._build_file_dependency_graph()
        cycles = self._find_circular_dependencies(file_graph)
        god_nodes = self._find_god_nodes(file_graph)
        dead_symbols = self._find_orphan_symbols()

        health_score = self._calculate_health_score(cycles, god_nodes, dead_symbols)

        return {
            "health_score": health_score,
            "status": "HEALTHY" if health_score >= 80 else ("WARNING" if health_score >= 60 else "CRITICAL"),
            "circular_dependencies": cycles,
            "circular_count": len(cycles),
            "god_nodes": god_nodes,
            "orphan_symbols": dead_symbols,
            "orphan_count": len(dead_symbols),
            "total_files": len(self.cart.file_results),
            "total_symbols": sum(len(v) for v in self.cart.symbol_index.values()),
        }

    def _build_file_dependency_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for f_path in self.cart.file_results:
            G.add_node(f_path)

        for src_file, imported_mods in self.cart.file_imports.items():
            for mod in imported_mods:
                target = self.cart._resolve_module_to_file(mod)
                if target and target != src_file and target in self.cart.file_results:
                    G.add_edge(src_file, target)
        return G

    def _find_circular_dependencies(self, G: nx.DiGraph) -> List[List[str]]:
        try:
            raw_cycles = list(nx.simple_cycles(G))
            # Format nicely
            clean_cycles = []
            for cycle in raw_cycles:
                if len(cycle) > 1:
                    clean_cycles.append(cycle + [cycle[0]])
            return clean_cycles[:10]  # Cap at top 10
        except Exception:
            return []

    def _find_god_nodes(self, G: nx.DiGraph) -> List[Dict[str, Any]]:
        if len(G.nodes) == 0:
            return []

        try:
            pagerank = nx.pagerank(G, alpha=0.85)
        except Exception:
            pagerank = {n: 0.0 for n in G.nodes}

        god_candidates = []
        for node in G.nodes:
            in_deg = G.in_degree(node)
            out_deg = G.out_degree(node)
            pr = pagerank.get(node, 0.0)

            # A God Node has high incoming dependencies or extreme centralization
            if in_deg >= 2 or pr > (2.0 / max(1, len(G.nodes))):
                res = self.cart.file_results.get(node)
                sym_count = len(res.symbols) if res else 0
                line_count = res.line_count if res else 0

                god_candidates.append({
                    "file": node,
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "pagerank": round(pr, 4),
                    "symbols_count": sym_count,
                    "lines": line_count,
                    "risk": "HIGH" if in_deg >= 4 else "MEDIUM",
                })

        # Sort by in_degree and pagerank descending
        god_candidates.sort(key=lambda x: (x["in_degree"], x["pagerank"]), reverse=True)
        return god_candidates[:8]

    def _find_orphan_symbols(self) -> List[Dict[str, Any]]:
        """Identifies functions or classes that are defined but never called or imported."""
        orphans = []
        ignored_names = {
            "main", "cli", "__init__", "setUp", "tearDown",
            "run", "handler", "execute", "test_", "do_GET", "do_POST", "do_OPTIONS"
        }

        for sym_name, locations in self.cart.symbol_index.items():
            # Skip common names, dunder methods, and tests
            if sym_name.startswith("__") or any(ign in sym_name for ign in ignored_names):
                continue

            for file_path, sym in locations:
                if "test" in file_path.lower():
                    continue

                sym_key = f"{file_path}::{sym.name}"
                callers = self.cart.reverse_call_graph.get(sym_key, set())

                # Check if called anywhere
                if len(callers) == 0:
                    orphans.append({
                        "symbol": sym.name,
                        "kind": sym.kind,
                        "file": file_path,
                        "line": sym.line_start,
                        "signature": sym.signature,
                    })

        return orphans[:25]  # Cap at top 25

    def _calculate_health_score(self, cycles: list, god_nodes: list, dead_symbols: list) -> int:
        score = 100
        # Penalize circular dependencies heavily (-15 per cycle loop)
        score -= len(cycles) * 15

        # Penalize extreme God-node concentration
        high_risk_gods = [g for g in god_nodes if g.get("risk") == "HIGH"]
        score -= len(high_risk_gods) * 8

        # Penalize orphan code clutter
        score -= min(20, len(dead_symbols) // 2)

        return max(15, min(100, score))
