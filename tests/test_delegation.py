import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.delegation import DelegationContractGenerator


def test_delegation_briefing_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        # File A: auth.py
        auth_file = os.path.join(tmpdir, "auth.py")
        with open(auth_file, "w", encoding="utf-8") as f:
            f.write("""
def authenticate_user(token: str) -> bool:
    \"\"\"Validates authentication token against session store.\"\"\"
    return True
""")

        # File B: server.py
        server_file = os.path.join(tmpdir, "server.py")
        with open(server_file, "w", encoding="utf-8") as f:
            f.write("""
from auth import authenticate_user

def handle_login(token: str):
    return authenticate_user(token)
""")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        delegator = DelegationContractGenerator(cart)

        brief = delegator.generate_briefing(
            objective="Add OAuth2 token expiry validation",
            target_files=["auth.py"],
            target_symbols=["authenticate_user"],
            test_command="pytest tests/test_auth.py",
        )

        assert brief["objective"] == "Add OAuth2 token expiry validation"
        assert "auth.py" in brief["scoped_files"]
        assert "server.py" in brief["forbidden_files"]
        assert len(brief["symbol_contracts"]) > 0
        assert brief["symbol_contracts"][0]["name"] == "authenticate_user"
        assert brief["estimated_tokens"] < 600

        # Markdown verification
        md = brief["markdown"]
        assert "[SUBAGENT DELEGATION CONTRACT]" in md
        assert "SCOPE & BOUNDARIES" in md
        assert "DEFINITION OF DONE" in md
        assert "pytest tests/test_auth.py" in md
