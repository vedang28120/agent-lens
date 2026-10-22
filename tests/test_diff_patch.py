import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.sandbox import GhostPatchSandbox


def test_dry_run_patch_diff_search_replace():
    with tempfile.TemporaryDirectory() as tmpdir:
        # File A: api.py
        api_file = os.path.join(tmpdir, "api.py")
        with open(api_file, "w", encoding="utf-8") as f:
            f.write("""
def public_endpoint():
    return "OLD_RESULT"
""")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        sandbox = GhostPatchSandbox(cart)

        # 1. Successful search-and-replace
        verdict = sandbox.dry_run_patch_diff(
            "api.py",
            search_block='return "OLD_RESULT"',
            replace_block='return "NEW_RESULT"',
        )
        assert verdict["verdict"] == "SAFE"
        assert verdict["safety_score"] >= 85

        # 2. Search block mismatch rejection
        bad_verdict = sandbox.dry_run_patch_diff(
            "api.py",
            search_block='return "NONEXISTENT_TEXT"',
            replace_block='return "ANYTHING"',
        )
        assert bad_verdict["verdict"] == "REJECTED"
        assert "not found" in bad_verdict["error"].lower()

        # 3. Unified diff hunk application (ensuring surrounding file content is preserved)
        diff_patch = """--- a/api.py
+++ b/api.py
@@ -1,3 +1,3 @@
 def public_endpoint():
-    return "OLD_RESULT"
+    return "HUNK_RESULT"
"""
        diff_verdict = sandbox.dry_run_patch_diff(
            "api.py",
            diff_patch=diff_patch,
        )
        assert diff_verdict["verdict"] == "SAFE"
        assert diff_verdict["safety_score"] >= 85
        # Ensure the file still has def public_endpoint() intact and didn't truncate
        assert diff_verdict["net_lines"] == 0
