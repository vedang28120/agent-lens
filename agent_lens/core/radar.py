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

        # Filter to production graph (ignore test files when determining architectural coupling)
        prod_nodes = [n for n in G.nodes if "test" not in n.lower()]
        prod_G = G.subgraph(prod_nodes)

        try:
            pagerank = nx.pagerank(prod_G, alpha=0.85)
        except Exception:
            pagerank = {n: 0.0 for n in prod_nodes}

        god_candidates = []
        for node in prod_nodes:
            in_deg = prod_G.in_degree(node)
            out_deg = prod_G.out_degree(node)
            pr = pagerank.get(node, 0.0)

            res = self.cart.file_results.get(node)
            sym_count = len(res.symbols) if res else 0
            line_count = res.line_count if res else 0

            # A God Node has high coupling in both directions or monolithic size (>450 lines) with high dependents
            is_god = (in_deg >= 4 and out_deg >= 3) or (line_count > 450 and in_deg >= 5)
            if is_god or in_deg >= 5:
                risk = "HIGH" if (in_deg >= 6 or (in_deg >= 4 and out_deg >= 4)) else "MEDIUM"
                god_candidates.append({
                    "file": node,
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "pagerank": round(pr, 4),
                    "symbols_count": sym_count,
                    "lines": line_count,
                    "risk": risk,
                })

        god_candidates.sort(key=lambda x: (x["in_degree"], x["pagerank"]), reverse=True)
        return god_candidates[:8]

    def _find_orphan_symbols(self) -> List[Dict[str, Any]]:
        """Identifies functions or classes that are defined but never called or imported."""
        orphans = []
        ignored_names = {
            "main", "cli", "__init__", "setUp", "tearDown",
            "run", "handler", "execute", "test_", "do_GET", "do_POST", "do_OPTIONS",
            "start", "stop", "to_dict", "asdict"
        }

        # Collect all imported symbol names across all files
        imported_symbols: Set[str] = set()
        for f_path, res in self.cart.file_results.items():
            for imp in res.imports:
                imported_symbols.update(imp.names)

        for sym_name, locations in self.cart.symbol_index.items():
            # Skip dunders, private helpers, common lifecycle names, dynamic visitor methods, and constants
            if (sym_name.startswith("_") or
                sym_name.isupper() or
                sym_name.startswith("visit_") or
                sym_name.startswith("do_") or
                sym_name.startswith("on_") or
                any(ign in sym_name for ign in ignored_names)):
                continue

            # If imported by any file, it's not an orphan
            if sym_name in imported_symbols:
                continue

            for file_path, sym in locations:
                if "test" in file_path.lower() or "web/" in file_path.lower():
                    continue
                if sym.kind in ["constant", "variable"]:
                    continue

                sym_key = f"{file_path}::{sym.name}"
                callers = self.cart.reverse_call_graph.get(sym_key, set())

                if len(callers) == 0:
                    orphans.append({
                        "symbol": sym.name,
                        "kind": sym.kind,
                        "file": file_path,
                        "line": sym.line_start,
                        "signature": sym.signature,
                    })

        return orphans[:25]

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
