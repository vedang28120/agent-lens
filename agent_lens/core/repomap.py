import os
import networkx as nx
from typing import Dict, List, Optional, Any
from .cartography import CodebaseCartographer


class RepoMapGenerator:
    """
    Generates an Aider-style, PageRank-weighted, token-budgeted global repository map.
    Gives AI agents an instant structural overview of the entire codebase in <1000 tokens.
    """

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def generate_repo_map(self, token_budget: int = 1024) -> Dict[str, Any]:
        """
        Ranks files by PageRank architectural importance and formats an ultra-dense
        indented signature tree within the specified token budget.
        """
        if not self.cart.file_results:
            self.cart.scan()

        # Build file graph and compute PageRank
        G = nx.DiGraph()
        for f in self.cart.file_results:
            G.add_node(f)

        for src_file, imported_mods in self.cart.file_imports.items():
            for mod in imported_mods:
                target = self.cart._resolve_module_to_file(mod)
                if target and target != src_file and target in self.cart.file_results:
                    G.add_edge(src_file, target)

        try:
            pagerank = nx.pagerank(G, alpha=0.85)
        except Exception:
            pagerank = {f: 1.0 for f in self.cart.file_results}

        # Sort files by PageRank descending, then line count
        ranked_files = sorted(
            self.cart.file_results.keys(),
            key=lambda f: (pagerank.get(f, 0.0), self.cart.file_results[f].line_count),
            reverse=True
        )

        max_chars = int(token_budget * 3.8)
        output_lines = [
            "# === REPOSITORY STRUCTURE MAP (PageRank Weighted) ===",
            "# Compact symbol tree of key modules and exported interfaces",
            ""
        ]

        current_chars = sum(len(l) + 1 for l in output_lines)
        files_included = 0
        symbols_included = 0

        for f_path in ranked_files:
            res = self.cart.file_results[f_path]
            # Skip test files from top-level architecture overview if space is tight
            if "test" in f_path.lower() and len(ranked_files) > 15:
                continue

            file_header = f"{f_path}:"
            if current_chars + len(file_header) + 2 > max_chars:
                break

            file_lines = [file_header]

            # Group symbols by parent class
            classes: Dict[str, List[Any]] = {}
            top_level_fns: List[Any] = []

            for sym in res.symbols:
                if sym.kind == "class":
                    if sym.name not in classes:
                        classes[sym.name] = []
                elif sym.parent:
                    if sym.parent not in classes:
                        classes[sym.parent] = []
                    classes[sym.parent].append(sym)
                elif sym.kind in ["function", "async_function"]:
                    top_level_fns.append(sym)

            # Add classes and methods
            for cls_name, methods in classes.items():
                cls_line = f"  class {cls_name}:"
                file_lines.append(cls_line)
                symbols_included += 1
                for m in methods[:6]:  # Limit to top 6 methods per class
                    file_lines.append(f"    def {m.name}{self._clean_signature(m.signature)}")
                    symbols_included += 1

            # Add top-level functions
            for fn in top_level_fns[:8]:  # Limit to top 8 functions per file
                file_lines.append(f"  def {fn.name}{self._clean_signature(fn.signature)}")
                symbols_included += 1

            candidate_block = "\n".join(file_lines) + "\n"
            if current_chars + len(candidate_block) > max_chars:
                break

            output_lines.extend(file_lines)
            output_lines.append("")
            current_chars += len(candidate_block)
            files_included += 1

        map_content = "\n".join(output_lines)
        est_tokens = max(1, int(len(map_content) / 3.8))

        return {
            "token_budget": token_budget,
            "estimated_tokens": est_tokens,
            "files_included": files_included,
            "total_files": len(self.cart.file_results),
            "symbols_included": symbols_included,
            "map_content": map_content,
        }

    def _clean_signature(self, sig: str) -> str:
        """Extracts clean parenthesized arguments e.g. '(self, query: str)' from full signature."""
        if "(" in sig and ")" in sig:
            start = sig.find("(")
            end = sig.rfind(")")
            return sig[start:end+1]
        return "()"
