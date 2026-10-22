import os
import time
import threading
from typing import Dict, Callable, Optional, Set
from .cartography import CodebaseCartographer, IGNORE_DIRS, IGNORE_EXTENSIONS
from .parser import CodeParser


class CodebaseWatcher:
    """Watches codebase for file changes and triggers incremental AST re-indexing and notifications."""

    def __init__(self, cartographer: CodebaseCartographer, on_change_callback: Optional[Callable[[str, str], None]] = None):
        self.cart = cartographer
        self.on_change = on_change_callback
        self.file_mtimes: Dict[str, float] = {}
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, interval: float = 1.0):
        """Starts background file monitoring thread."""
        self._init_file_mtimes()
        self.running = True
        self._thread = threading.Thread(target=self._watch_loop, args=(interval,), daemon=True)
        self._thread.start()

    def stop(self):
        """Stops background file monitoring thread."""
        self.running = False

    def _init_file_mtimes(self):
        self.file_mtimes.clear()
        for root, dirs, files in os.walk(self.cart.root_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in IGNORE_EXTENSIONS:
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.cart.root_path).replace("\\", "/")
                try:
                    self.file_mtimes[rel_path] = os.path.getmtime(full_path)
                except OSError:
                    pass

    def _watch_loop(self, interval: float):
        while self.running:
            time.sleep(interval)
            current_files: Set[str] = set()

            for root, dirs, files in os.walk(self.cart.root_path):
                dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in IGNORE_EXTENSIONS:
                        continue

                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.cart.root_path).replace("\\", "/")
                    current_files.add(rel_path)

                    try:
                        mtime = os.path.getmtime(full_path)
                        last_mtime = self.file_mtimes.get(rel_path)

                        if last_mtime is None:
                            # New file created
                            self.file_mtimes[rel_path] = mtime
                            self._handle_file_event(rel_path, "created")
                        elif mtime > last_mtime:
                            # File modified
                            self.file_mtimes[rel_path] = mtime
                            self._handle_file_event(rel_path, "modified")
                    except OSError:
                        pass

            # Detect deleted files
            deleted = set(self.file_mtimes.keys()) - current_files
            for del_file in deleted:
                del self.file_mtimes[del_file]
                self._handle_file_event(del_file, "deleted")

    def _handle_file_event(self, rel_path: str, event_type: str):
        full_path = os.path.join(self.cart.root_path, rel_path)

        if event_type in ["created", "modified"]:
            # Incrementally re-parse the file
            res = CodeParser.parse_file(full_path)
            self.cart.file_results[rel_path] = res

            # Update imports
            mod_set = {imp.module for imp in res.imports}
            self.cart.file_imports[rel_path] = mod_set

            # Re-index symbol entries for this file
            self._update_symbol_index_for_file(rel_path, res)
            self.cart._build_dependency_links()

        elif event_type == "deleted":
            if rel_path in self.cart.file_results:
                del self.cart.file_results[rel_path]
            if rel_path in self.cart.file_imports:
                del self.cart.file_imports[rel_path]
            self._purge_symbol_index_for_file(rel_path)
            self.cart._build_dependency_links()

        if self.on_change:
            try:
                self.on_change(rel_path, event_type)
            except Exception:
                pass

    def _update_symbol_index_for_file(self, rel_path: str, res):
        self._purge_symbol_index_for_file(rel_path)
        for sym in res.symbols:
            if sym.name not in self.cart.symbol_index:
                self.cart.symbol_index[sym.name] = []
            self.cart.symbol_index[sym.name].append((rel_path, sym))

    def _purge_symbol_index_for_file(self, rel_path: str):
        for sym_name, locs in list(self.cart.symbol_index.items()):
            new_locs = [loc for loc in locs if loc[0] != rel_path]
            if new_locs:
                self.cart.symbol_index[sym_name] = new_locs
            else:
                del self.cart.symbol_index[sym_name]
