import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.packer import ContextPacker


def test_context_packer_ast_pruning():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "heavy.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("""import os

def helper_one():
    # Long irrelevant body
    x = 10
    y = 20
    return x + y

def target_function(name: str) -> str:
    \"\"\"This is the critical function we want to inspect.\"\"\"
    return f"Hello, {name}!"

def helper_two():
    # Another long irrelevant body
    a = "foo"
    b = "bar"
    return a + b
""")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()

        packer = ContextPacker(cart)
        packed = packer.pack("target_function", token_budget=500)

        assert packed["target_symbol"] == "target_function"
        content = packed["slice_content"]

        # Target function body must be fully present
        assert 'return f"Hello, {name}!"' in content
        # Sibling bodies must be pruned
        assert "pruned" in content
        assert "x + y" not in content
        assert "a + b" not in content
        assert packed["estimated_tokens"] <= 500
