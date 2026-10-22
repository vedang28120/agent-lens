import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.shadow import GitShadowSandbox


def test_shadow_sandbox_execution_and_cleanup():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample test file
        test_file = os.path.join(tmpdir, "calc.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("def add(a, b):\n    return a + b\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        shadow = GitShadowSandbox(cart)

        # Propose patch to calc.py
        patched_code = "def add(a, b):\n    return a + b + 1\n"
        cmd = "python -c \"from calc import add; assert add(2, 2) == 5\""

        res = shadow.run_shadow_test(
            file_patches={"calc.py": patched_code},
            test_command=cmd,
            timeout=10,
        )

        assert res["success"] is True
        assert res["exit_code"] == 0
        assert "shadow-" in res["sandbox_id"]

        # Verify sandbox was completely cleaned up
        sandbox_path = os.path.join(shadow.worktree_base, res["sandbox_id"])
        assert not os.path.exists(sandbox_path)

        # Verify original file was completely untouched
        with open(test_file, "r") as f:
            assert f.read() == "def add(a, b):\n    return a + b\n"
