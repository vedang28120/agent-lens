import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.sandbox import GhostPatchSandbox


def test_ghost_patch_syntax_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "mod.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("def valid_fn():\n    return 42\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        sandbox = GhostPatchSandbox(cart)

        # Propose broken patch
        broken_code = "def broken():\n    print('unclosed"
        verdict = sandbox.dry_run_patch("mod.py", broken_code)

        assert verdict["verdict"] == "REJECTED"
        assert verdict["safety_score"] == 0
        assert "Syntax error" in verdict["breakages"][0]


def test_ghost_patch_caller_breakage_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # File A: core.py
        core_path = os.path.join(tmpdir, "core.py")
        with open(core_path, "w", encoding="utf-8") as f:
            f.write("def shared_util():\n    return 'OK'\n")

        # File B: app.py calls core.py
        app_path = os.path.join(tmpdir, "app.py")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write("from core import shared_util\ndef run():\n    return shared_util()\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        sandbox = GhostPatchSandbox(cart)

        # Propose patch that removes shared_util
        deleted_patch = "def new_different_util():\n    return 'NEW'\n"
        verdict = sandbox.dry_run_patch("core.py", deleted_patch)

        assert verdict["verdict"] == "DANGEROUS"
        assert any("shared_util" in b for b in verdict["breakages"])
        assert "new_different_util" in verdict["added_symbols"]
        assert "shared_util" in verdict["removed_symbols"]
