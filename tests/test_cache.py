import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer


def test_ast_persistent_cache_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a few files
        for i in range(5):
            path = os.path.join(tmpdir, f"module_{i}.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"def func_{i}():\n    return {i}\n")

        # 1. Cold Scan (Empty cache)
        cart = CodebaseCartographer(tmpdir)
        m1 = cart.scan()
        assert m1["files_scanned"] == 5
        assert m1["cache_hits"] == 0
        assert m1["cache_misses"] == 5
        assert os.path.exists(cart.cache_db_path)

        # 2. Warm Scan (Should hit 100% cache)
        cart2 = CodebaseCartographer(tmpdir)
        m2 = cart2.scan()
        assert m2["files_scanned"] == 5
        assert m2["cache_hits"] == 5
        assert m2["cache_misses"] == 0

        # Verify symbols were restored properly from cache
        assert "func_0" in cart2.symbol_index
        assert "func_4" in cart2.symbol_index
