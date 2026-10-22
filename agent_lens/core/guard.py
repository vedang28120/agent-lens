import os
import ast
import builtins
import rapidfuzz.process
import rapidfuzz.fuzz
from typing import Dict, List, Optional, Any, Set, Tuple
from .cartography import CodebaseCartographer
from .parser import CodeParser
from .security import resolve_safe_path


class HallucinationGuard:
    """Detects hallucinated method calls, non-existent imports, and symbol misspellings."""

    # Common Python built-in functions and modules to ignore
    BUILTIN_NAMES = set(dir(builtins)) | {
        "len", "str", "int", "float", "list", "dict", "set", "tuple", "bool",
        "print", "range", "enumerate", "zip", "map", "filter", "any", "all",
        "min", "max", "sum", "sorted", "reversed", "isinstance", "issubclass",
        "hasattr", "getattr", "setattr", "delattr", "open", "super", "type"
    }

    COMMON_STDLIB = {
        "os", "sys", "re", "json", "math", "time", "datetime", "uuid", "random",
        "pathlib", "subprocess", "typing", "collections", "itertools", "functools",
        "copy", "tempfile", "shutil", "logging", "threading", "multiprocessing",
        "asyncio", "socket", "http", "urllib", "sqlite3", "hashlib", "io"
    }

    BUILTIN_METHODS = {
        "keys", "values", "items", "get", "append", "extend", "pop", "insert",
        "remove", "clear", "add", "update", "discard", "copy", "count", "index",
        "strip", "lstrip", "rstrip", "split", "splitlines", "replace", "startswith",
        "endswith", "join", "lower", "upper", "capitalize", "title", "format",
        "find", "rfind", "encode", "decode", "close", "read", "write", "flush",
        "seek", "connect", "cursor", "execute", "fetchall", "fetchone", "commit",
        "rollback", "start", "stop", "join", "is_alive", "acquire", "release",
        "add_argument", "add_parser", "add_subparsers", "parse_args", "print_help",
        "to_dict", "asdict", "parse", "visit", "generic_visit"
    }

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer

    def verify_file(self, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Inspects file AST for calls and imports that do not exist in the codebase."""
        if not self.cart.file_results:
            self.cart.scan()

        try:
            full_path = resolve_safe_path(self.cart.root_path, file_path)
            base_real = os.path.realpath(os.path.abspath(self.cart.root_path))
            norm_file = os.path.relpath(full_path, base_real).replace("\\", "/")
        except (ValueError, PermissionError) as e:
            return {"valid": False, "error": f"Security violation: {str(e)}", "hallucinations": []}

        if content is None:
            if not os.path.exists(full_path):
                return {"valid": False, "error": f"File not found: {file_path}", "hallucinations": []}
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                return {"valid": False, "error": str(e), "hallucinations": []}

        lang = CodeParser.detect_language(norm_file)
        if lang != "python":
            return {"valid": True, "language": lang, "hallucinations": [], "note": "Guard currently deep-verifies Python AST"}

        try:
            tree = ast.parse(content, filename=norm_file)
        except SyntaxError as e:
            return {
                "valid": False,
                "error": f"Syntax error at line {e.lineno}: {e.msg}",
                "hallucinations": [],
            }

        hallucinations = []
        all_indexed_symbols = list(self.cart.symbol_index.keys())

        # 1. Check imports: `from mod import X`
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                # Skip stdlib or external top-level packages
                first_part = mod.split(".")[0]
                if first_part in self.COMMON_STDLIB:
                    continue

                # Try to resolve module file
                target_file = self.cart._resolve_module_to_file(mod)
                if target_file and target_file in self.cart.file_results:
                    file_res = self.cart.file_results[target_file]
                    file_sym_names = {s.name for s in file_res.symbols}

                    for alias in node.names:
                        sym_name = alias.name
                        if sym_name == "*":
                            continue
                        if sym_name not in file_sym_names:
                            # Fuzzy match suggestion
                            best = self._find_best_match(sym_name, list(file_sym_names))
                            suggestion = f" Did you mean `{best}`?" if best else ""
                            hallucinations.append({
                                "type": "import_not_found",
                                "line": node.lineno,
                                "symbol": sym_name,
                                "module": mod,
                                "file": target_file,
                                "message": f"Symbol `{sym_name}` is not defined in `{target_file}`.{suggestion}",
                                "suggested": best,
                                "suggested_match": best,
                            })

        # 2. Check function / method calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_info = self._extract_call_details(node)
                if not call_info:
                    continue

                fn_name, receiver = call_info
                # Ignore builtins and common standard library methods
                if fn_name in self.BUILTIN_NAMES or fn_name in self.BUILTIN_METHODS:
                    continue

                # If receiver is specified e.g. cart.get_outline
                if receiver:
                    if fn_name in self.BUILTIN_METHODS:
                        continue
                    if any(receiver.startswith(p) for p in ["os.", "sys.", "json.", "re.", "subparsers.", "parser."]):
                        continue

                    # Only flag if receiver looks like an internal project class or instance
                    target_receivers = ["self.cart", "cart", "cartographer", "self.memory", "memory", "radar", "packer", "guard", "sandbox", "sentinel", "planner"]
                    if any(r in receiver for r in target_receivers):
                        if fn_name not in self.cart.symbol_index:
                            best = self._find_best_match(fn_name, all_indexed_symbols)
                            suggestion = f" Did you mean `{best}`?" if best else ""
                            hallucinations.append({
                                "type": "unknown_method",
                                "line": node.lineno,
                                "symbol": f"{receiver}.{fn_name}",
                                "message": f"Method `{fn_name}` on `{receiver}` was not found in codebase index.{suggestion}",
                                "suggested": best,
                                "suggested_match": best,
                            })

        is_clean = len(hallucinations) == 0
        return {
            "file": norm_file,
            "valid": is_clean,
            "is_clean": is_clean,
            "hallucination_count": len(hallucinations),
            "flagged_count": len(hallucinations),
            "hallucinations": hallucinations,
        }

    def _extract_call_details(self, node: ast.Call) -> Optional[Tuple[str, Optional[str]]]:
        if isinstance(node.func, ast.Name):
            return node.func.id, None
        elif isinstance(node.func, ast.Attribute):
            receiver_name = self._unparse_receiver(node.func.value)
            return node.func.attr, receiver_name
        return None

    def _unparse_receiver(self, node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:
            return ""

    def _find_best_match(self, name: str, candidates: List[str]) -> Optional[str]:
        if not candidates:
            return None
        match = rapidfuzz.process.extractOne(name, candidates, scorer=rapidfuzz.fuzz.token_sort_ratio)
        if match and match[1] >= 65:
            return match[0]
        return None

    # Alias for MCP server and API compatibility
    verify_patch_hallucinations = verify_file
