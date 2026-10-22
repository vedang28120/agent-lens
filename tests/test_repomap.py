import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.repomap import RepoMapGenerator


def test_repomap_generation_and_token_budget():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a few inter-connected files
        f1 = os.path.join(tmpdir, "service.py")
        with open(f1, "w", encoding="utf-8") as f:
            f.write(
                "from utils import helper\n\n"
                "class AuthService:\n"
                "    def login(self, user: str) -> bool:\n"
                "        return helper(user)\n\n"
                "    def logout(self, user: str) -> None:\n"
                "        pass\n"
            )

        f2 = os.path.join(tmpdir, "utils.py")
        with open(f2, "w", encoding="utf-8") as f:
            f.write(
                "def helper(name: str) -> bool:\n"
                "    return len(name) > 0\n"
            )

        cart = CodebaseCartographer(tmpdir)
        cart.scan()

        generator = RepoMapGenerator(cart)
        res = generator.generate_repo_map(token_budget=500)

        assert res["token_budget"] == 500
        assert res["files_included"] >= 2
        assert "AuthService" in res["map_content"]
        assert "helper" in res["map_content"]
        assert "login" in res["map_content"]
        assert res["estimated_tokens"] <= 500
