import os
import ast
import rapidfuzz.process
import rapidfuzz.fuzz
from typing import Dict, List, Optional, Any, Set
from .cartography import CodebaseCartographer
from .parser import CodeParser, Symbol


class ContextPacker:
    """Intelligently slices and prunes codebase ASTs into token-budgeted prompt contexts."""

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def pack(self, query: str, token_budget: int = 1200) -> Dict[str, Any]:
        """Slices relevant files, preserving target implementations while pruning sibling bodies."""
        if not self.cart.file_results:
            self.cart.scan()

        # 1. Match query against indexed symbols
        matched_symbols = self._find_relevant_symbols(query)
        if not matched_symbols:
            return {
                "query": query,
                "token_budget": token_budget,
                "estimated_tokens": 0,
                "slice_content": f"# No matching symbols found for query: '{query}'",
                "symbols_included": [],
                "files_included": [],
            }

        target_file, primary_sym = matched_symbols[0]
        full_path = os.path.join(self.cart.root_path, target_file)

        # 2. Read full content
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                raw_code = f.read()
        except Exception as e:
            return {
                "query": query,
                "error": f"Failed to read {target_file}: {str(e)}",
            }

        # 3. Generate AST-pruned slice
        pruned_code = self._prune_file(target_file, raw_code, primary_sym.name)

        # 4. Include callers context
        callers = self.cart.reverse_call_graph.get(f"{target_file}::{primary_sym.name}", set())
        callers_note = f"\n# Inbound Callers ({len(callers)}): " + (", ".join(list(callers)[:5]) if callers else "None")

        # 5. Format output
        header = f"# === AGENTLENS CONTEXT SLICE ===\n# Target: {primary_sym.name} in {target_file} (L{primary_sym.line_start}-{primary_sym.line_end}){callers_note}\n\n"
        final_slice = header + pruned_code

        # Token approximation (~3.8 chars per token for code)
        est_tokens = int(len(final_slice) / 3.8)

        # Truncate gracefully on line boundaries if exceeding budget
        if est_tokens > token_budget:
            max_chars = int(token_budget * 3.8)
            slice_lines = final_slice.splitlines()
            curr_chars = 0
            truncated_lines = []
            for line in slice_lines:
                if curr_chars + len(line) + 1 > max_chars:
                    break
                truncated_lines.append(line)
                curr_chars += len(line) + 1
            final_slice = "\n".join(truncated_lines) + "\n\n# ... [TRUNCATED ON LINE BOUNDARY TO FIT TOKEN BUDGET]"
            est_tokens = int(len(final_slice) / 3.8)

        return {
            "query": query,
            "target_symbol": primary_sym.name,
            "target_file": target_file,
            "token_budget": token_budget,
            "estimated_tokens": est_tokens,
            "slice_content": final_slice,
            "symbols_included": [primary_sym.name],
            "files_included": [target_file],
        }

    def _find_relevant_symbols(self, query: str) -> List[tuple]:
        """Finds closest matching symbols using exact then fuzzy matching."""
        # Exact match
        if query in self.cart.symbol_index:
            return self.cart.symbol_index[query]

        # Case-insensitive match
        for s_name, locs in self.cart.symbol_index.items():
            if s_name.lower() == query.lower():
                return locs

        # Fuzzy match using RapidFuzz
        choices = list(self.cart.symbol_index.keys())
        if not choices:
            return []

        best_matches = rapidfuzz.process.extract(query, choices, scorer=rapidfuzz.fuzz.token_sort_ratio, limit=3)
        results = []
        for match_name, score, _ in best_matches:
            if score >= 60:
                results.extend(self.cart.symbol_index[match_name])

        return results

    def _prune_file(self, file_path: str, raw_code: str, target_symbol_name: str) -> str:
        """Prunes sibling function/method bodies, preserving imports, classes, and target function."""
        lines = raw_code.splitlines()
        lang = CodeParser.detect_language(file_path)

        if lang != "python":
            # For non-python files, return targeted line window
            parse_res = self.cart.file_results.get(file_path)
            if parse_res:
                target_sym = next((s for s in parse_res.symbols if s.name == target_symbol_name), None)
                if target_sym:
                    start = max(0, target_sym.line_start - 10)
                    end = min(len(lines), target_sym.line_end + 10)
                    window = lines[start:end]
                    return f"// ... [lines 1-{start} omitted]\n" + "\n".join(window) + f"\n// ... [lines {end}-{len(lines)} omitted]"
            return raw_code

        # Python AST-guided pruning
        try:
            tree = ast.parse(raw_code, filename=file_path)
        except Exception:
            return raw_code

        # Collect target node line range so we never prune closures/helpers inside the target!
        target_range = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == target_symbol_name:
                    target_range = (node.lineno, node.end_lineno or node.lineno)
                    break

        pruned_lines = []
        skip_until_line = -1

        # Collect symbols to prune (all functions/methods outside target)
        prune_ranges = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name != target_symbol_name:
                    node_start = node.lineno
                    node_end = node.end_lineno or node.lineno

                    # If this function is nested INSIDE target function/class, preserve it intact!
                    if target_range and target_range[0] <= node_start <= target_range[1]:
                        continue

                    # Keep signature and docstring, prune body
                    body_start = node.lineno
                    if node.body:
                        # If first item is docstring, start pruning after docstring
                        if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                            body_start = node.body[0].end_lineno or node.body[0].lineno
                        else:
                            body_start = node.lineno
                    prune_ranges.append((body_start, node.end_lineno or node.lineno, node.name))

        prune_map = {r[0]: (r[1], r[2]) for r in prune_ranges}

        idx = 0
        while idx < len(lines):
            line_no = idx + 1

            if line_no in prune_map:
                end_l, name = prune_map[line_no]
                # Add the first line (signature or doc)
                pruned_lines.append(lines[idx])
                # Determine indentation
                indent = " " * (len(lines[idx]) - len(lines[idx].lstrip()))
                pruned_lines.append(f"{indent}    ...  # [pruned {end_l - line_no} lines of {name}]")
                idx = end_l  # Skip to end of function
            else:
                pruned_lines.append(lines[idx])
                idx += 1

        return "\n".join(pruned_lines)
