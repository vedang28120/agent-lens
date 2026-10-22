import ast
import os
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Set

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_javascript
    import tree_sitter_typescript
    TREE_SITTER_AVAILABLE = True
except Exception:
    TREE_SITTER_AVAILABLE = False


@dataclass
class Symbol:
    name: str
    kind: str  # function, async_function, class, method, interface, variable
    line_start: int
    line_end: int
    signature: str = ""
    docstring: Optional[str] = None
    parent: Optional[str] = None  # class or namespace
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImportInfo:
    module: str
    names: List[str]
    is_from: bool
    alias: Optional[str] = None
    line: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FileParseResult:
    file_path: str
    language: str
    line_count: int
    imports: List[ImportInfo] = field(default_factory=list)
    symbols: List[Symbol] = field(default_factory=list)
    all_calls: List[str] = field(default_factory=list)
    parse_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "line_count": self.line_count,
            "imports": [i.to_dict() for i in self.imports],
            "symbols": [s.to_dict() for s in self.symbols],
            "all_calls": self.all_calls,
            "parse_error": self.parse_error,
        }


class PythonASTVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: List[str]):
        self.source_lines = source_lines
        self.symbols: List[Symbol] = []
        self.imports: List[ImportInfo] = []
        self.all_calls: Set[str] = set()
        self.current_class: Optional[str] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(
                ImportInfo(
                    module=alias.name,
                    names=[alias.name],
                    is_from=False,
                    alias=alias.asname,
                    line=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        if node.level and node.level > 0:
            mod = ("." * node.level) + mod
        names = [alias.name for alias in node.names]
        self.imports.append(
            ImportInfo(
                module=mod,
                names=names,
                is_from=True,
                line=node.lineno,
            )
        )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    is_const = target.id.isupper()
                    self.symbols.append(
                        Symbol(
                            name=target.id,
                            kind="constant" if is_const else "variable",
                            line_start=node.lineno,
                            line_end=node.end_lineno or node.lineno,
                            signature=f"{target.id} = ...",
                        )
                    )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if self.current_class is None and isinstance(node.target, ast.Name):
            is_const = node.target.id.isupper()
            ann_str = ast.unparse(node.annotation) if node.annotation else ""
            self.symbols.append(
                Symbol(
                    name=node.target.id,
                    kind="constant" if is_const else "variable",
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    signature=f"{node.target.id}: {ann_str}",
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        decorators = [ast.unparse(d) for d in node.decorator_list]
        bases = [ast.unparse(b) for b in node.bases]
        sig = f"class {node.name}" + (f"({', '.join(bases)})" if bases else "")
        doc = ast.get_docstring(node)

        calls_in_class = self._extract_calls(node)

        sym = Symbol(
            name=node.name,
            kind="class",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=sig,
            docstring=doc.strip() if doc else None,
            parent=self.current_class,
            decorators=decorators,
            calls=list(calls_in_class),
        )
        self.symbols.append(sym)

        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node, is_async=True)

    def _handle_function(self, node, is_async: bool):
        kind = "method" if self.current_class else ("async_function" if is_async else "function")
        decorators = [ast.unparse(d) for d in node.decorator_list]

        # Extract arguments
        params = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            params.append(arg_str)
        if node.args.vararg:
            params.append(f"*{node.args.vararg.arg}")
        if node.args.kwarg:
            params.append(f"**{node.args.kwarg.arg}")

        ret_type = ast.unparse(node.returns) if node.returns else None

        prefix = "async def " if is_async else "def "
        sig = f"{prefix}{node.name}({', '.join(params)})"
        if ret_type:
            sig += f" -> {ret_type}"

        doc = ast.get_docstring(node)
        calls_inside = self._extract_calls(node)

        sym = Symbol(
            name=node.name,
            kind=kind,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=sig,
            docstring=doc.strip() if doc else None,
            parent=self.current_class,
            parameters=params,
            return_type=ret_type,
            decorators=decorators,
            calls=list(calls_inside),
        )
        self.symbols.append(sym)
        self.generic_visit(node)

    def _extract_calls(self, node) -> Set[str]:
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self._resolve_call_name(child.func)
                if name:
                    calls.add(name)
                    self.all_calls.add(name)
        return calls

    def _resolve_call_name(self, func_node) -> Optional[str]:
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            val = self._resolve_call_name(func_node.value)
            return f"{val}.{func_node.attr}" if val else func_node.attr
        return None


class CodeParser:
    """Unified AST Parser supporting Python, JavaScript, TypeScript, and fallback formats."""

    @staticmethod
    def detect_language(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".py":
            return "python"
        elif ext in [".js", ".jsx", ".mjs", ".cjs"]:
            return "javascript"
        elif ext == ".tsx":
            return "tsx"
        elif ext in [".ts", ".mts", ".cts"]:
            return "typescript"
        elif ext == ".go":
            return "go"
        elif ext == ".rs":
            return "rust"
        elif ext in [".json", ".yaml", ".yml", ".toml", ".md"]:
            return ext[1:]
        return "unknown"

    @classmethod
    def parse_file(cls, file_path: str, content: Optional[str] = None) -> FileParseResult:
        if content is None:
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                return FileParseResult(
                    file_path=file_path,
                    language="unknown",
                    line_count=0,
                    parse_error=f"File read error: {str(e)}",
                )

        lang = cls.detect_language(file_path)
        lines = content.splitlines()

        if lang == "python":
            return cls._parse_python(file_path, content, lines)
        elif lang in ["javascript", "typescript", "tsx"]:
            return cls._parse_js_ts(file_path, content, lines, lang)
        else:
            return cls._parse_generic(file_path, content, lines, lang)

    @classmethod
    def _parse_python(cls, file_path: str, content: str, lines: List[str]) -> FileParseResult:
        try:
            tree = ast.parse(content, filename=file_path)
            visitor = PythonASTVisitor(lines)
            visitor.visit(tree)
            return FileParseResult(
                file_path=file_path,
                language="python",
                line_count=len(lines),
                imports=visitor.imports,
                symbols=visitor.symbols,
                all_calls=sorted(list(visitor.all_calls)),
            )
        except SyntaxError as e:
            return FileParseResult(
                file_path=file_path,
                language="python",
                line_count=len(lines),
                parse_error=f"SyntaxError at line {e.lineno}: {e.msg}",
            )
        except Exception as e:
            return FileParseResult(
                file_path=file_path,
                language="python",
                line_count=len(lines),
                parse_error=f"Parse error: {str(e)}",
            )

    @classmethod
    def _parse_js_ts(cls, file_path: str, content: str, lines: List[str], lang: str) -> FileParseResult:
        symbols: List[Symbol] = []
        imports: List[ImportInfo] = []
        all_calls: Set[str] = set()

        if TREE_SITTER_AVAILABLE:
            try:
                if lang == "tsx":
                    ts_lang = Language(tree_sitter_typescript.language_tsx())
                    parser = Parser(ts_lang)
                elif lang == "typescript":
                    ts_lang = Language(tree_sitter_typescript.language_typescript())
                    parser = Parser(ts_lang)
                else:
                    js_lang = Language(tree_sitter_javascript.language())
                    parser = Parser(js_lang)

                tree = parser.parse(content.encode("utf-8"))
                root = tree.root_node

                def traverse(node, current_parent=None, current_symbol=None):
                    nonlocal symbols, imports, all_calls

                    node_type = node.type
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1

                    # Imports
                    if node_type == "import_statement":
                        text = content[node.start_byte:node.end_byte]
                        mod_match = re.search(r"from\s+['\"]([^'\"]+)['\"]", text)
                        mod = mod_match.group(1) if mod_match else text

                        # Extract imported names
                        imp_names = []
                        for child in node.children:
                            if child.type == "import_clause":
                                for clause_child in child.children:
                                    if clause_child.type == "identifier":
                                        imp_names.append(content[clause_child.start_byte:clause_child.end_byte])
                                    elif clause_child.type == "named_imports":
                                        for spec in clause_child.children:
                                            if spec.type == "import_specifier":
                                                name_node = spec.child_by_field_name("name") or spec.children[0]
                                                imp_names.append(content[name_node.start_byte:name_node.end_byte])
                        imports.append(ImportInfo(module=mod, names=imp_names, is_from=True, line=start_line))

                    # Function declarations
                    elif node_type in ["function_declaration", "generator_function_declaration"]:
                        name_node = node.child_by_field_name("name")
                        name = content[name_node.start_byte:name_node.end_byte] if name_node else "anonymous"
                        params_node = node.child_by_field_name("parameters")
                        params = content[params_node.start_byte:params_node.end_byte] if params_node else "()"
                        sym = Symbol(
                            name=name,
                            kind="function",
                            line_start=start_line,
                            line_end=end_line,
                            signature=f"function {name}{params}",
                            parent=current_parent,
                        )
                        symbols.append(sym)
                        for child in node.children:
                            traverse(child, current_parent=current_parent, current_symbol=sym)
                        return

                    # Variable-bound arrow functions or function expressions
                    elif node_type in ["lexical_declaration", "variable_declaration"]:
                        for declarator in node.children:
                            if declarator.type == "variable_declarator":
                                name_node = declarator.child_by_field_name("name")
                                value_node = declarator.child_by_field_name("value")
                                if name_node and value_node and value_node.type in ["arrow_function", "function_expression"]:
                                    name = content[name_node.start_byte:name_node.end_byte]
                                    params_node = value_node.child_by_field_name("parameters")
                                    params = content[params_node.start_byte:params_node.end_byte] if params_node else "()"
                                    sym = Symbol(
                                        name=name,
                                        kind="function",
                                        line_start=start_line,
                                        line_end=end_line,
                                        signature=f"const {name} = {params} => ...",
                                        parent=current_parent,
                                    )
                                    symbols.append(sym)
                                    for child in value_node.children:
                                        traverse(child, current_parent=current_parent, current_symbol=sym)
                                    continue
                        for child in node.children:
                            traverse(child, current_parent=current_parent, current_symbol=current_symbol)
                        return

                    # Interfaces (TypeScript / TSX)
                    elif node_type == "interface_declaration":
                        name_node = node.child_by_field_name("name")
                        name = content[name_node.start_byte:name_node.end_byte] if name_node else "AnonymousInterface"
                        symbols.append(
                            Symbol(
                                name=name,
                                kind="interface",
                                line_start=start_line,
                                line_end=end_line,
                                signature=f"interface {name}",
                                parent=current_parent,
                            )
                        )

                    # Type Aliases (TypeScript / TSX)
                    elif node_type == "type_alias_declaration":
                        name_node = node.child_by_field_name("name")
                        name = content[name_node.start_byte:name_node.end_byte] if name_node else "AnonymousType"
                        symbols.append(
                            Symbol(
                                name=name,
                                kind="interface",
                                line_start=start_line,
                                line_end=end_line,
                                signature=f"type {name} = ...",
                                parent=current_parent,
                            )
                        )

                    # Class declarations
                    elif node_type == "class_declaration":
                        name_node = node.child_by_field_name("name")
                        name = content[name_node.start_byte:name_node.end_byte] if name_node else "AnonymousClass"
                        symbols.append(
                            Symbol(
                                name=name,
                                kind="class",
                                line_start=start_line,
                                line_end=end_line,
                                signature=f"class {name}",
                                parent=current_parent,
                            )
                        )
                        for child in node.children:
                            traverse(child, current_parent=name, current_symbol=None)
                        return

                    # Method definitions
                    elif node_type == "method_definition":
                        name_node = node.child_by_field_name("name")
                        name = content[name_node.start_byte:name_node.end_byte] if name_node else "anonymous"
                        params_node = node.child_by_field_name("parameters")
                        params = content[params_node.start_byte:params_node.end_byte] if params_node else "()"
                        sym = Symbol(
                            name=name,
                            kind="method",
                            line_start=start_line,
                            line_end=end_line,
                            signature=f"{name}{params}",
                            parent=current_parent,
                        )
                        symbols.append(sym)
                        for child in node.children:
                            traverse(child, current_parent=current_parent, current_symbol=sym)
                        return

                    # Call expressions
                    elif node_type == "call_expression":
                        fn_node = node.child_by_field_name("function")
                        if fn_node:
                            call_name = content[fn_node.start_byte:fn_node.end_byte]
                            all_calls.add(call_name)
                            if current_symbol:
                                current_symbol.calls.append(call_name)

                    for child in node.children:
                        traverse(child, current_parent=current_parent, current_symbol=current_symbol)

                traverse(root)

                return FileParseResult(
                    file_path=file_path,
                    language=lang,
                    line_count=len(lines),
                    imports=imports,
                    symbols=symbols,
                    all_calls=sorted(list(all_calls)),
                )
            except Exception:
                pass  # Fallback to regex if tree-sitter parse raises

        # Regex fallback for JS/TS
        for idx, line in enumerate(lines, 1):
            imp_match = re.search(r"import\s+(?:\{([^}]+)\}|\s*([a-zA-Z0-9_$]+))?\s*from\s+['\"]([^'\"]+)['\"]", line)
            if imp_match:
                names = []
                if imp_match.group(1):
                    names = [n.strip() for n in imp_match.group(1).split(",") if n.strip()]
                elif imp_match.group(2):
                    names = [imp_match.group(2).strip()]
                imports.append(ImportInfo(module=imp_match.group(3), names=names, is_from=True, line=idx))

            fn_match = re.search(r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\((.*?)\)", line)
            if fn_match:
                symbols.append(
                    Symbol(
                        name=fn_match.group(1),
                        kind="function",
                        line_start=idx,
                        line_end=idx,
                        signature=fn_match.group(0).strip(),
                    )
                )

            arrow_match = re.search(r"(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\((.*?)\)\s*=>", line)
            if arrow_match:
                symbols.append(
                    Symbol(
                        name=arrow_match.group(1),
                        kind="function",
                        line_start=idx,
                        line_end=idx,
                        signature=f"const {arrow_match.group(1)} = (...) => ...",
                    )
                )

            cls_match = re.search(r"(?:export\s+)?class\s+([a-zA-Z0-9_$]+)", line)
            if cls_match:
                symbols.append(
                    Symbol(
                        name=cls_match.group(1),
                        kind="class",
                        line_start=idx,
                        line_end=idx,
                        signature=cls_match.group(0).strip(),
                    )
                )

        return FileParseResult(
            file_path=file_path,
            language=lang,
            line_count=len(lines),
            imports=imports,
            symbols=symbols,
            all_calls=sorted(list(all_calls)),
        )

    @classmethod
    def _parse_generic(cls, file_path: str, content: str, lines: List[str], lang: str) -> FileParseResult:
        return FileParseResult(
            file_path=file_path,
            language=lang,
            line_count=len(lines),
            imports=[],
            symbols=[],
            all_calls=[],
        )
