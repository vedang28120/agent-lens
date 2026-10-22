import os
from typing import Dict, List, Optional, Any, Set
from .cartography import CodebaseCartographer
from .parser import CodeParser, FileParseResult, Symbol


class GhostPatchSandbox:
    """Simulates code modifications in an in-memory shadow AST to detect regressions before touching disk."""

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def dry_run_patch(self, file_path: str, proposed_content: str) -> Dict[str, Any]:
        """Performs a virtual dry-run of a proposed file replacement."""
        norm_file = file_path.replace("\\", "/")
        full_path = os.path.join(self.cart.root_path, norm_file)

        # 1. Parse current original version
        original_result = self.cart.file_results.get(norm_file)
        if not original_result and os.path.exists(full_path):
            original_result = CodeParser.parse_file(full_path)

        # 2. Parse shadow proposed content
        shadow_result = CodeParser.parse_file(norm_file, content=proposed_content)

        # If shadow content has syntax error, reject immediately
        if shadow_result.parse_error:
            return {
                "verdict": "REJECTED",
                "safety_score": 0,
                "file": norm_file,
                "error": shadow_result.parse_error,
                "breakages": [f"Syntax error in patch: {shadow_result.parse_error}"],
                "added_symbols": [],
                "removed_symbols": [],
                "modified_symbols": [],
            }

        # 3. Diff symbols
        orig_symbols = {s.name: s for s in (original_result.symbols if original_result else [])}
        shadow_symbols = {s.name: s for s in shadow_result.symbols}

        added = [name for name in shadow_symbols if name not in orig_symbols]
        removed = [name for name in orig_symbols if name not in shadow_symbols]

        modified = []
        for name in orig_symbols:
            if name in shadow_symbols:
                orig_s = orig_symbols[name]
                shad_s = shadow_symbols[name]
                if orig_s.signature != shad_s.signature:
                    modified.append({
                        "name": name,
                        "old_signature": orig_s.signature,
                        "new_signature": shad_s.signature,
                        "param_change": orig_s.parameters != shad_s.parameters,
                    })

        # 4. Check for broken callers across the codebase
        breakages = []
        warnings = []

        # Check removed symbols
        for rem_name in removed:
            sym_key = f"{norm_file}::{rem_name}"
            callers = self.cart.reverse_call_graph.get(sym_key, set())
            if callers:
                breakages.append(
                    f"CRITICAL: Symbol `{rem_name}` was deleted, but is called by {len(callers)} location(s): {', '.join(list(callers)[:4])}"
                )

        # Check modified parameters
        for mod in modified:
            if mod["param_change"]:
                sym_key = f"{norm_file}::{mod['name']}"
                callers = self.cart.reverse_call_graph.get(sym_key, set())
                if callers:
                    warnings.append(
                        f"Signature changed for `{mod['name']}`: callers may need parameter updates: {', '.join(list(callers)[:3])}"
                    )

        # 5. Determine Verdict
        if breakages:
            verdict = "DANGEROUS"
            score = 30
        elif warnings:
            verdict = "WARNING"
            score = 70
        else:
            verdict = "SAFE"
            score = 100

        return {
            "verdict": verdict,
            "safety_score": score,
            "file": norm_file,
            "error": None,
            "added_symbols": added,
            "removed_symbols": removed,
            "modified_symbols": modified,
            "breakages": breakages,
            "warnings": warnings,
            "net_lines": shadow_result.line_count - (original_result.line_count if original_result else 0),
        }
