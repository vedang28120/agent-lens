import os
import ast
import re
import subprocess
from typing import Dict, List, Optional, Any
from .parser import CodeParser


class PreflightChecker:
    """Pre-flight safety inspection for code files prior to execution or commit."""

    CONFLICT_MARKERS = [
        re.compile(r"^<<<<<<<", re.MULTILINE),
        re.compile(r"^=======$", re.MULTILINE),
        re.compile(r"^>>>>>>>", re.MULTILINE),
    ]

    @classmethod
    def check_file(cls, file_path: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Runs syntax validation, conflict detection, and import sanity checks."""
        if content is None:
            if not os.path.exists(file_path):
                return {
                    "file_path": file_path,
                    "valid": False,
                    "errors": [f"File does not exist: {file_path}"],
                    "warnings": [],
                }
            if os.path.isdir(file_path):
                return cls.check_directory(file_path)
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                return {
                    "file_path": file_path,
                    "valid": False,
                    "errors": [f"Could not read file: {str(e)}"],
                    "warnings": [],
                }

        errors = []
        warnings = []

        # 1. Check for merge conflict markers
        for marker in cls.CONFLICT_MARKERS:
            match = marker.search(content)
            if match:
                # Find line number
                line_no = content[:match.start()].count("\n") + 1
                errors.append(f"Git conflict marker found at line {line_no}: `{match.group(0)}`")

        # 2. Syntax Validation
        lang = CodeParser.detect_language(file_path)
        if lang == "python":
            cls._check_python_syntax(file_path, content, errors, warnings)
        elif lang in ["javascript", "typescript"]:
            cls._check_js_ts_syntax(file_path, content, errors, warnings)
        elif lang == "json":
            cls._check_json_syntax(content, errors)

        return {
            "file_path": file_path,
            "language": lang,
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    @classmethod
    def _check_python_syntax(cls, file_path: str, content: str, errors: List[str], warnings: List[str]):
        try:
            tree = ast.parse(content, filename=file_path)
            # Check for common missing imports (e.g. using json, os, sys, math without import)
            imported_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        imported_names.add(a.asname or a.name)
                elif isinstance(node, ast.ImportFrom):
                    for a in node.names:
                        imported_names.add(a.asname or a.name)

            # Common stdlib modules that are frequently forgotten
            common_modules = {"os", "sys", "json", "re", "math", "time", "datetime", "uuid", "pathlib", "subprocess"}
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_names.add(node.id)

            unimported_common = (common_modules & used_names) - imported_names
            for mod in unimported_common:
                warnings.append(f"Potentially unimported standard library module `{mod}` is referenced.")

        except SyntaxError as e:
            errors.append(f"Python SyntaxError at line {e.lineno}:{e.offset} - {e.msg}")
        except Exception as e:
            errors.append(f"Python parse error: {str(e)}")

    @classmethod
    def _check_js_ts_syntax(cls, file_path: str, content: str, errors: List[str], warnings: List[str]):
        # 1. Use real Tree-Sitter AST parser if available
        lang = CodeParser.detect_language(file_path)
        if lang in ["javascript", "typescript", "tsx"]:
            res = CodeParser.parse_file(file_path, content=content)
            if res.parse_error:
                errors.append(f"{lang.capitalize()} syntax error: {res.parse_error}")
                return
            # If Tree-sitter parsed it successfully with symbols or no error, accept it
            if not res.parse_error and len(res.symbols) > 0:
                return

        # 2. Heuristic fallback when Tree-Sitter is unavailable
        cleaned = re.sub(r"/\*[\s\S]*?\*/", "", content)
        cleaned = re.sub(r"//.*", "", cleaned)
        # Strip regex literals e.g. /"/[gimsuy]* so quotes inside regex don't trigger string state
        cleaned = re.sub(r"/(?:\\/|[^/\n])+/[a-z]*", "''", cleaned)

        # Balanced brackets check as a robust baseline
        brackets = {"(": ")", "{": "}", "[": "]"}
        stack = []
        in_string = None
        escaped = False

        for idx, char in enumerate(cleaned):
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if in_string:
                if char == in_string:
                    in_string = None
                continue
            if char in ["'", '"', "`"]:
                in_string = char
                continue

            if char in brackets:
                stack.append((char, idx))
            elif char in brackets.values():
                if not stack:
                    line_no = cleaned[:idx].count("\n") + 1
                    errors.append(f"Unmatched closing bracket `{char}` at line {line_no}")
                    return
                top, _ = stack.pop()
                if brackets[top] != char:
                    line_no = cleaned[:idx].count("\n") + 1
                    errors.append(f"Mismatched bracket: expected `{brackets[top]}`, got `{char}` at line {line_no}")
                    return

        if stack:
            top, pos = stack[-1]
            line_no = cleaned[:pos].count("\n") + 1
            errors.append(f"Unclosed bracket `{top}` opened at line {line_no}")

    @classmethod
    def _check_json_syntax(cls, content: str, errors: List[str]):
        import json
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"JSONDecodeError at line {e.lineno}:{e.colno} - {e.msg}")

    @classmethod
    def check_git_diff_safety(cls, repo_path: str = ".") -> Dict[str, Any]:
        """Inspects git unstaged changes for suspicious mass deletions."""
        try:
            res = subprocess.run(
                ["git", "diff", "--numstat"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
            )
            if res.returncode != 0:
                return {"status": "skipped", "reason": "Not a git repository or git error"}

            lines = res.stdout.strip().splitlines()
            warnings = []
            total_added = 0
            total_deleted = 0

            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 3:
                    added = int(parts[0]) if parts[0].isdigit() else 0
                    deleted = int(parts[1]) if parts[1].isdigit() else 0
                    file = parts[2]
                    total_added += added
                    total_deleted += deleted

                    if deleted > 100 and deleted > (added * 3):
                        warnings.append(
                            f"Suspicious mass deletion in `{file}`: -{deleted} lines, +{added} lines."
                        )

            return {
                "status": "ok",
                "total_added": total_added,
                "total_deleted": total_deleted,
                "warnings": warnings,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    @classmethod
    def check_directory(cls, dir_path: str) -> Dict[str, Any]:
        """Recursively inspects code and configuration files within a directory."""
        all_errors = []
        all_warnings = []
        checked_count = 0
        failed_count = 0
        details = []

        ignore_dirs = {
            ".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build",
            ".pytest_cache", ".mypy_cache", ".agentlens"
        }
        valid_exts = {".py", ".json", ".js", ".ts", ".tsx", ".jsx", ".toml", ".yaml", ".yml"}

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_exts:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, dir_path).replace("\\", "/")
                    res = cls.check_file(full_p)
                    checked_count += 1
                    if not res["valid"]:
                        failed_count += 1
                        for err in res["errors"]:
                            all_errors.append(f"{rel_p}: {err}")
                    for warn in res["warnings"]:
                        all_warnings.append(f"{rel_p}: {warn}")
                    details.append(res)

        return {
            "file_path": dir_path,
            "is_directory": True,
            "checked_files": checked_count,
            "failed_files": failed_count,
            "valid": failed_count == 0,
            "errors": all_errors,
            "warnings": all_warnings,
            "details": details,
        }
