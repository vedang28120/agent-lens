import os
import time
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.watcher import CodebaseWatcher


def test_codebase_watcher_detects_modification():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "service.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("def initial():\n    pass\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        assert "initial" in cart.symbol_index

        events = []
        def on_change(f, t):
            events.append((f, t))

        watcher = CodebaseWatcher(cart, on_change_callback=on_change)
        watcher._init_file_mtimes()

        # Simulate modification
        time.sleep(0.05)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("def modified_function():\n    pass\n")

        # Run one watch tick manually
        watcher._handle_file_event("service.py", "modified")

        assert "modified_function" in cart.symbol_index
        assert "initial" not in cart.symbol_index
        assert len(events) == 1
        assert events[0] == ("service.py", "modified")
