import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.guard import HallucinationGuard


def test_hallucination_guard_detects_bad_import_and_suggests():
    with tempfile.TemporaryDirectory() as tmpdir:
        # File A: service.py defines get_user_profile
        service_path = os.path.join(tmpdir, "service.py")
        with open(service_path, "w", encoding="utf-8") as f:
            f.write("def get_user_profile(user_id: int):\n    return {'id': user_id}\n")

        # File B: app.py imports hallucinated `get_user_profle` (typo)
        app_path = os.path.join(tmpdir, "app.py")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write("from service import get_user_profle\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        guard = HallucinationGuard(cart)

        res = guard.verify_file("app.py")

        assert res["valid"] is False
        assert res["hallucination_count"] == 1
        issue = res["hallucinations"][0]
        assert issue["symbol"] == "get_user_profle"
        assert issue["suggested"] == "get_user_profile"
