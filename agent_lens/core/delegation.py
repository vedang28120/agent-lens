import os
from typing import Dict, List, Optional, Any, Set
from .cartography import CodebaseCartographer


class DelegationContractGenerator:
    """
    Generates ultra-compact, token-budgeted (<600 tokens) subagent delegation briefings
    specifying exact symbol contracts, scoped file boundaries, and verification criteria.
    """

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def generate_briefing(
        self,
        objective: str,
        target_files: List[str],
        target_symbols: Optional[List[str]] = None,
        test_command: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesizes an unambiguous, bounded delegation contract for a subagent.
        """
        if not self.cart.file_results:
            self.cart.scan()

        norm_files = [f.replace("\\", "/") for f in target_files]
        all_symbols = []
        tests: Set[str] = set()
        downstream_callers: Set[str] = set()

        # Collect symbols and blast radius
        for f in norm_files:
            res = self.cart.file_results.get(f)
            if res:
                for sym in res.symbols:
                    if target_symbols is None or sym.name in target_symbols:
                        all_symbols.append({
                            "name": sym.name,
                            "kind": sym.kind,
                            "file": f,
                            "lines": f"L{sym.line_start}-{sym.line_end}",
                            "signature": sym.signature,
                            "doc": sym.docstring.split("\n")[0] if sym.docstring else "",
                        })

            blast = self.cart.calculate_blast_radius(f)
            tests.update(blast.get("related_tests", []))
            for caller in blast.get("impacted_symbols", []):
                if not any(caller.startswith(nf) for nf in norm_files):
                    downstream_callers.add(caller)

        auto_test_cmd = test_command or ("pytest " + " ".join(sorted(list(tests))) if tests else "pytest")

        briefing_data = {
            "objective": objective,
            "scoped_files": norm_files,
            "forbidden_files": sorted(list(set(self.cart.file_results.keys()) - set(norm_files)))[:10],
            "symbol_contracts": all_symbols[:8],
            "downstream_callers_count": len(downstream_callers),
            "key_downstream_callers": sorted(list(downstream_callers))[:5],
            "covering_tests": sorted(list(tests)),
            "verification_command": auto_test_cmd,
        }

        markdown_brief = self.format_briefing_markdown(briefing_data)
        briefing_data["markdown"] = markdown_brief
        briefing_data["estimated_tokens"] = int(len(markdown_brief) / 3.8)

        return briefing_data

    def format_briefing_markdown(self, briefing: Dict[str, Any]) -> str:
        lines = [
            f"# [SUBAGENT DELEGATION CONTRACT] {briefing['objective']}",
            "",
            "## 1. SCOPE & BOUNDARIES",
            f"- **Allowed Files to Modify**: `{'`, `'.join(briefing['scoped_files'])}`",
            "- **STRICT CONSTRAINT**: Do NOT modify any other files in the repository.",
            "",
            "## 2. SYMBOL INTERFACE CONTRACTS",
        ]

        for s in briefing["symbol_contracts"]:
            doc_suffix = f" -- *{s['doc']}*" if s.get("doc") else ""
            lines.append(f"- `{s['file']}` [{s['lines']}]: `{s['signature']}`{doc_suffix}")

        if briefing.get("key_downstream_callers"):
            lines.append("")
            lines.append("## 3. DOWNSTREAM CONTRACT PROTECTION")
            lines.append(f"Callers that rely on these interfaces ({briefing['downstream_callers_count']} total):")
            for c in briefing["key_downstream_callers"]:
                lines.append(f"  - `{c}`")
            lines.append("⚠️ Changes must maintain signature backward-compatibility.")

        lines.append("")
        lines.append("## 4. DEFINITION OF DONE & VERIFICATION")
        lines.append(f"- Execute verification command: `{briefing['verification_command']}`")
        lines.append("- All unit tests must pass with 0 failures before marking task complete.")

        return "\n".join(lines)
