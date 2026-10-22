import os
import re
from typing import Dict, List, Optional, Any, Set
from .cartography import CodebaseCartographer
from .parser import CodeParser, FileParseResult, Symbol
from .security import resolve_safe_path


class GhostPatchSandbox:
    """Simulates code modifications in an in-memory shadow AST to detect regressions before touching disk."""

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def dry_run_patch(self, file_path: str, proposed_content: str) -> Dict[str, Any]:
        """Performs a virtual dry-run of a proposed file replacement."""
        # 0. Enforce path security jail
        try:
            full_path = resolve_safe_path(self.cart.root_path, file_path)
            base_real = os.path.realpath(os.path.abspath(self.cart.root_path))
            norm_file = os.path.relpath(full_path, base_real).replace("\\", "/")
        except (ValueError, PermissionError) as e:
            return {
                "verdict": "REJECTED",
                "safety_score": 0,
                "file": file_path,
                "error": f"Security boundary violation: {str(e)}",
                "breakages": [str(e)],
                "added_symbols": [],
                "removed_symbols": [],
                "modified_symbols": [],
            }

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

        # 5. Determine Verdict & Confidence
        caveats = [
            "Static analysis cannot guarantee safety against dynamic dispatch, getattr, **kwargs, or duck typing.",
            "Run unit tests via shadow-worktree for definitive runtime verification."
        ]

        if breakages:
            verdict = "DANGEROUS"
            score = 30
            confidence = "HIGH_CONFIDENCE_FAILURE"
        elif warnings:
            verdict = "WARNING"
            score = 70
            confidence = "STATIC_SIGNATURE_DRIFT"
        else:
            verdict = "SAFE"
            score = 90  # Never claim 100% in a dynamic language without test execution
            confidence = "NO_STATIC_BREAKAGES"

        return {
            "verdict": verdict,
            "safety_score": score,
            "confidence_assessment": confidence,
            "file": norm_file,
            "error": None,
            "added_symbols": added,
            "removed_symbols": removed,
            "modified_symbols": modified,
            "breakages": breakages,
            "warnings": warnings,
            "caveats": caveats,
            "net_lines": shadow_result.line_count - (original_result.line_count if original_result else 0),
        }

    def dry_run_patch_diff(
        self,
        file_path: str,
        search_block: Optional[str] = None,
        replace_block: Optional[str] = None,
        diff_patch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Performs a token-efficient dry-run by applying a localized search-and-replace block
        or unified diff patch in-memory, without requiring the full file text.
        """
        try:
            full_path = resolve_safe_path(self.cart.root_path, file_path)
            base_real = os.path.realpath(os.path.abspath(self.cart.root_path))
            norm_file = os.path.relpath(full_path, base_real).replace("\\", "/")
        except (ValueError, PermissionError) as e:
            return {
                "verdict": "REJECTED",
                "safety_score": 0,
                "file": file_path,
                "error": str(e),
                "breakages": [str(e)],
                "added_symbols": [],
                "removed_symbols": [],
                "modified_symbols": [],
            }

        if not os.path.exists(full_path):
            return {
                "verdict": "REJECTED",
                "safety_score": 0,
                "file": norm_file,
                "error": f"Target file does not exist: {file_path}",
                "breakages": [f"File {file_path} not found"],
                "added_symbols": [],
                "removed_symbols": [],
                "modified_symbols": [],
            }

        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            original_content = f.read()

        if search_block is not None and replace_block is not None:
            if search_block not in original_content:
                return {
                    "verdict": "REJECTED",
                    "safety_score": 0,
                    "file": norm_file,
                    "error": "Target search_block was not found in original file content.",
                    "breakages": ["Search block mismatch"],
                    "added_symbols": [],
                    "removed_symbols": [],
                    "modified_symbols": [],
                }
            # Replace exactly once or target occurrence
            proposed_content = original_content.replace(search_block, replace_block, 1)
            return self.dry_run_patch(norm_file, proposed_content)

        elif diff_patch is not None:
            # Simple unified patch simulator
            lines = original_content.splitlines(keepends=True)
            patch_lines = diff_patch.splitlines(keepends=True)
            # Apply basic +/- hunks
            new_lines = []
            skip_count = 0
            for pline in patch_lines:
                if pline.startswith("---") or pline.startswith("+++") or pline.startswith("@@"):
                    continue
                elif pline.startswith("-"):
                    continue
                elif pline.startswith("+"):
                    new_lines.append(pline[1:])
                elif pline.startswith(" "):
                    new_lines.append(pline[1:])
            
            proposed = "".join(new_lines) if new_lines else original_content
            return self.dry_run_patch(norm_file, proposed)

        return {
            "verdict": "REJECTED",
            "safety_score": 0,
            "file": norm_file,
            "error": "Must provide either (search_block and replace_block) or diff_patch.",
            "breakages": ["Missing patch parameters"],
            "added_symbols": [],
            "removed_symbols": [],
            "modified_symbols": [],
        }
