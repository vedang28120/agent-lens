import os
import re
from typing import Dict, List, Optional, Set, Any, Tuple
from .parser import CodeParser, FileParseResult, Symbol

# Directories and files to ignore during indexation
IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".next",
    ".nuxt",
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll",
    ".so", ".dylib", ".pyc", ".woff", ".woff2", ".ttf"
}


class CodebaseCartographer:
    """Builds an in-memory semantic map and dependency graph of a codebase."""

    def __init__(self, root_path: str = "."):
        self.root_path = os.path.abspath(root_path)
        self.file_results: Dict[str, FileParseResult] = {}
        # symbol_name -> list of (file_rel_path, Symbol)
        self.symbol_index: Dict[str, List[Tuple[str, Symbol]]] = {}
        # file_rel_path -> set of imported module strings
        self.file_imports: Dict[str, Set[str]] = {}
        # file_rel_path -> set of files that import this file
        self.file_dependents: Dict[str, Set[str]] = {}
        # caller_symbol_key -> set of called_symbol_keys
        self.call_graph: Dict[str, Set[str]] = {}
        # symbol_key -> set of caller_symbol_keys (reverse graph)
        self.reverse_call_graph: Dict[str, Set[str]] = {}

    def scan(self) -> Dict[str, Any]:
        """Scans the root path and builds index and dependency graph."""
        self.file_results.clear()
        self.symbol_index.clear()
        self.file_imports.clear()
        self.file_dependents.clear()
        self.call_graph.clear()
        self.reverse_call_graph.clear()

        scanned_count = 0
        total_lines = 0

        for root, dirs, files in os.walk(self.root_path):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTENSIONS:
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.root_path).replace("\\", "/")

                parse_res = CodeParser.parse_file(full_path)
                self.file_results[rel_path] = parse_res
                scanned_count += 1
                total_lines += parse_res.line_count

                # Index imports
                mod_set = set()
                for imp in parse_res.imports:
                    mod_set.add(imp.module)
                self.file_imports[rel_path] = mod_set

                # Index symbols
                for sym in parse_res.symbols:
                    if sym.name not in self.symbol_index:
                        self.symbol_index[sym.name] = []
                    self.symbol_index[sym.name].append((rel_path, sym))

        # Build reverse dependencies & call linkages
        self._build_dependency_links()

        return {
            "root_path": self.root_path,
            "files_scanned": scanned_count,
            "total_lines": total_lines,
            "symbols_indexed": sum(len(v) for v in self.symbol_index.values()),
            "unique_symbol_names": len(self.symbol_index),
        }

    def _build_dependency_links(self):
        """Cross-references imports and function calls across all indexed files."""
        # 1. File dependency linkages
        for file_path, imported_mods in self.file_imports.items():
            for mod in imported_mods:
                # Find matching indexed files
                target_file = self._resolve_module_to_file(mod)
                if target_file and target_file != file_path:
                    if target_file not in self.file_dependents:
                        self.file_dependents[target_file] = set()
                    self.file_dependents[target_file].add(file_path)

        # 2. Symbol-level call graph
        for file_path, result in self.file_results.items():
            for sym in result.symbols:
                caller_key = f"{file_path}::{sym.name}"
                if caller_key not in self.call_graph:
                    self.call_graph[caller_key] = set()

                for called_name in sym.calls:
                    # Strip method prefixes e.g. self.bar -> bar
                    clean_called = called_name.split(".")[-1]
                    if clean_called in self.symbol_index:
                        for target_file, target_sym in self.symbol_index[clean_called]:
                            callee_key = f"{target_file}::{target_sym.name}"
                            self.call_graph[caller_key].add(callee_key)
                            if callee_key not in self.reverse_call_graph:
                                self.reverse_call_graph[callee_key] = set()
                            self.reverse_call_graph[callee_key].add(caller_key)

    def _resolve_module_to_file(self, module_str: str) -> Optional[str]:
        """Converts import path e.g. 'core.parser' or './parser' to indexed rel_path."""
        mod_clean = module_str.replace(".", "/").lstrip("./")
        for ext in [".py", ".ts", ".js", ".tsx", ".jsx"]:
            candidate = f"{mod_clean}{ext}"
            if candidate in self.file_results:
                return candidate
            candidate_init = f"{mod_clean}/__init__.py"
            if candidate_init in self.file_results:
                return candidate_init
            candidate_index = f"{mod_clean}/index{ext}"
            if candidate_index in self.file_results:
                return candidate_index

        # Suffix matching
        for file_path in self.file_results:
            if file_path.endswith(f"/{mod_clean}.py") or file_path == f"{mod_clean}.py":
                return file_path
        return None

    def get_symbol_card(self, symbol_name: str, file_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Generates a high-density, token-optimized symbol card."""
        matches = self.symbol_index.get(symbol_name, [])
        if not matches:
            return None

        # Filter by file_hint if provided
        selected = None
        if file_hint:
            norm_hint = file_hint.replace("\\", "/")
            for f_path, sym in matches:
                if norm_hint in f_path:
                    selected = (f_path, sym)
                    break
        if not selected:
            selected = matches[0]

        file_path, sym = selected
        sym_key = f"{file_path}::{sym.name}"
        callers = sorted(list(self.reverse_call_graph.get(sym_key, [])))

        # Find tests that call or reference this symbol
        tests = [c for c in callers if "test" in c.lower()]

        # Compute blast radius
        blast_info = self.calculate_blast_radius(file_path, sym.name)

        return {
            "symbol": sym.name,
            "kind": sym.kind,
            "file": file_path,
            "lines": f"{sym.line_start}-{sym.line_end} ({sym.line_end - sym.line_start + 1} lines)",
            "signature": sym.signature,
            "docstring": sym.docstring,
            "parent": sym.parent,
            "decorators": sym.decorators,
            "parameters": sym.parameters,
            "return_type": sym.return_type,
            "calls": sym.calls[:10],
            "callers_count": len(callers),
            "direct_callers": callers[:10],
            "related_tests": tests,
            "risk_level": blast_info["risk_level"],
            "impacted_files_count": len(blast_info["impacted_files"]),
        }

    def format_card_markdown(self, card: Dict[str, Any]) -> str:
        """Formats the symbol card into ultra-compact, high-density markdown."""
        lines = [
            f"### [SYMBOL CARD] `{card['symbol']}` ({card['kind']})",
            f"- **Location**: `{card['file']}` (L{card['lines']})",
            f"- **Signature**: `{card['signature']}`",
        ]
        if card.get("docstring"):
            lines.append(f"- **Doc**: \"{card['docstring']}\"")
        if card.get("decorators"):
            lines.append(f"- **Decorators**: `{'`, `'.join(card['decorators'])}`")
        if card.get("calls"):
            lines.append(f"- **Calls**: {', '.join(card['calls'])}")

        callers_str = f"{card['callers_count']} caller(s)"
        if card["direct_callers"]:
            callers_sample = ", ".join([f"`{c}`" for c in card["direct_callers"][:5]])
            callers_str += f": {callers_sample}"
        lines.append(f"- **Callers**: {callers_str}")

        if card.get("related_tests"):
            lines.append(f"- **Covering Tests**: {', '.join(card['related_tests'])}")

        risk_label = f"[{card['risk_level']}]"
        lines.append(f"- **Blast Radius**: **{card['risk_level']}** {risk_label} ({card['impacted_files_count']} dependent file(s))")

        return "\n".join(lines)

    def calculate_blast_radius(self, file_path: str, symbol_name: Optional[str] = None) -> Dict[str, Any]:
        """Calculates transitive blast radius if file or symbol is modified."""
        norm_file = file_path.replace("\\", "/")
        impacted_files: Set[str] = set()
        impacted_symbols: Set[str] = set()

        if symbol_name:
            # Symbol-level blast radius
            target_key = f"{norm_file}::{symbol_name}"
            visited = set()
            queue = [target_key]

            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                visited.add(curr)

                callers = self.reverse_call_graph.get(curr, set())
                for caller in callers:
                    impacted_symbols.add(caller)
                    caller_file = caller.split("::")[0]
                    if caller_file != norm_file:
                        impacted_files.add(caller_file)
                    if caller not in visited:
                        queue.append(caller)
        else:
            # File-level blast radius
            visited = set()
            queue = [norm_file]

            while queue:
                curr = queue.pop(0)
                if curr in visited:
                    continue
                visited.add(curr)

                dependents = self.file_dependents.get(curr, set())
                for dep in dependents:
                    impacted_files.add(dep)
                    if dep not in visited:
                        queue.append(dep)

        # Classify risk
        file_count = len(impacted_files)
        if file_count == 0:
            risk = "LOW"
        elif file_count <= 2:
            risk = "MEDIUM"
        elif file_count <= 6:
            risk = "HIGH"
        else:
            risk = "CRITICAL"

        tests = [f for f in impacted_files if "test" in f.lower()]

        return {
            "target_file": norm_file,
            "target_symbol": symbol_name,
            "risk_level": risk,
            "impacted_files": sorted(list(impacted_files)),
            "impacted_symbols": sorted(list(impacted_symbols))[:25],
            "related_tests": sorted(tests),
        }

    def get_file_outline(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Returns structured outline of a single file without its body content."""
        norm_file = file_path.replace("\\", "/")
        result = self.file_results.get(norm_file)
        if not result:
            # Try finding by endswith
            for f_key, res in self.file_results.items():
                if f_key.endswith(norm_file):
                    result = res
                    norm_file = f_key
                    break

        if not result:
            return None

        symbols_summary = []
        for s in result.symbols:
            symbols_summary.append({
                "name": s.name,
                "kind": s.kind,
                "lines": f"{s.line_start}-{s.line_end}",
                "signature": s.signature,
                "parent": s.parent,
                "doc": s.docstring[:80] + "..." if s.docstring and len(s.docstring) > 80 else s.docstring,
            })

        return {
            "file": norm_file,
            "language": result.language,
            "line_count": result.line_count,
            "imports_count": len(result.imports),
            "symbols_count": len(result.symbols),
            "symbols": symbols_summary,
        }

    def format_outline_markdown(self, outline: Dict[str, Any]) -> str:
        """Formats the outline into compact markdown."""
        lines = [
            f"### Outline: `{outline['file']}` ({outline['line_count']} lines, {outline['language']})",
            f"Total Symbols: {outline['symbols_count']} | Imports: {outline['imports_count']}",
            "",
        ]
        for s in outline["symbols"]:
            indent = "  " if s["parent"] else ""
            doc_str = f" - *{s['doc']}*" if s.get("doc") else ""
            lines.append(f"{indent}- `{s['signature']}` [L{s['lines']}]{doc_str}")

        return "\n".join(lines)

    def get_graph_export(self) -> Dict[str, Any]:
        """Exports graph in node-link JSON format for web visualization."""
        nodes = []
        links = []
        file_node_map = {}

        # File nodes
        for idx, (f_path, res) in enumerate(self.file_results.items()):
            dep_count = len(self.file_dependents.get(f_path, set()))
            nodes.append({
                "id": f_path,
                "name": os.path.basename(f_path),
                "type": "file",
                "language": res.language,
                "lines": res.line_count,
                "symbols_count": len(res.symbols),
                "dependents_count": dep_count,
            })
            file_node_map[f_path] = idx

        # File dependency links
        for src_file, imported_mods in self.file_imports.items():
            for mod in imported_mods:
                target_file = self._resolve_module_to_file(mod)
                if target_file and target_file in file_node_map and target_file != src_file:
                    links.append({
                        "source": src_file,
                        "target": target_file,
                        "type": "imports",
                    })

        return {
            "nodes": nodes,
            "links": links,
        }
