import os
import re
import ast
from typing import Dict, List, Optional, Any, Set
from .cartography import CodebaseCartographer


class DynamicRiskDetector:
    """
    Detects dynamic dispatch, reflection (getattr, hasattr, globals), duck typing,
    and string-based symbol lookups that defeat static AST analysis in Python.
    """

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def audit_symbol_dynamic_risk(self, target_symbol: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Audits the repository for dynamic occurrences of `target_symbol` that static AST
        call graphs would otherwise miss.
        """
        findings = []
        target_re = re.compile(rf"\b{re.escape(target_symbol)}\b")
        string_re = re.compile(rf"['\"][^'\"]*{re.escape(target_symbol)}[^'\"]*['\"]")
        getattr_re = re.compile(rf"(?:getattr|hasattr|setattr|delattr)\s*\([^,]+,\s*['\"]{re.escape(target_symbol)}['\"]")

        for file_path, parse_res in self.cart.file_results.items():
            if target_file and file_path == target_file:
                continue

            full_path = os.path.join(self.cart.root_path, file_path)
            if not os.path.exists(full_path):
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            # Quick filter: if symbol name does not appear at all, skip
            if target_symbol not in content:
                continue

            lines = content.splitlines()

            # 1. Direct Reflection Check: getattr(obj, 'symbol')
            for match in getattr_re.finditer(content):
                line_no = content[:match.start()].count("\n") + 1
                snippet = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                findings.append({
                    "file": file_path,
                    "line": line_no,
                    "type": "DYNAMIC_REFLECTION",
                    "detail": f"Direct reflection via `{match.group(0)}`",
                    "snippet": snippet,
                    "severity": "HIGH",
                })

            # 2. String literal references: e.g. "symbol" in dict or callback registration
            for match in string_re.finditer(content):
                if getattr_re.search(match.group(0)):
                    continue
                line_no = content[:match.start()].count("\n") + 1
                snippet = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                if not snippet.startswith("#") and not snippet.startswith("//"):
                    findings.append({
                        "file": file_path,
                        "line": line_no,
                        "type": "STRING_LITERAL_REFERENCE",
                        "detail": f"Symbol name referenced as string: {match.group(0)}",
                        "snippet": snippet,
                        "severity": "MEDIUM",
                    })

            # 3. Python AST Loose Attribute Access (Duck Typing)
            if parse_res.language == "python":
                try:
                    tree = ast.parse(content, filename=file_path)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Attribute) and node.attr == target_symbol:
                            # If caller file does NOT statically import target file, this is duck typing
                            is_statically_linked = False
                            for imp in parse_res.imports:
                                if target_symbol in imp.names:
                                    is_statically_linked = True
                                    break

                            if not is_statically_linked:
                                line_no = node.lineno
                                snippet = lines[line_no - 1].strip() if line_no <= len(lines) else ""
                                # Avoid duplicate entries for same line
                                if not any(f["file"] == file_path and f["line"] == line_no for f in findings):
                                    findings.append({
                                        "file": file_path,
                                        "line": line_no,
                                        "type": "DUCK_TYPED_ATTRIBUTE_ACCESS",
                                        "detail": f"Attribute `.{target_symbol}` accessed without explicit module import",
                                        "snippet": snippet,
                                        "severity": "HIGH",
                                    })
                except Exception:
                    pass

        # Deduplicate and sort findings
        high_count = sum(1 for f in findings if f["severity"] == "HIGH")
        med_count = sum(1 for f in findings if f["severity"] == "MEDIUM")

        if high_count > 0:
            risk_level = "HIGH"
        elif med_count > 0:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        return {
            "target_symbol": target_symbol,
            "target_file": target_file,
            "dynamic_risk_level": risk_level,
            "total_unverified_references": len(findings),
            "findings": findings[:15],
            "caveats": [
                "Static AST call graphs cannot guarantee detection of runtime reflection or duck typing.",
                "Review any HIGH severity findings above before assuming zero downstream impact."
            ]
        }
