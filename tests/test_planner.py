import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.planner import RefactorPlanner


def test_refactor_planner_sequence():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Base: types.py
        types_path = os.path.join(tmpdir, "types.py")
        with open(types_path, "w", encoding="utf-8") as f:
            f.write("class UserPayload:\n    pass\n")

        # Service: auth.py imports types.py
        auth_path = os.path.join(tmpdir, "auth.py")
        with open(auth_path, "w", encoding="utf-8") as f:
            f.write("from types import UserPayload\ndef login():\n    return UserPayload()\n")

        # Caller: server.py imports auth.py
        server_path = os.path.join(tmpdir, "server.py")
        with open(server_path, "w", encoding="utf-8") as f:
            f.write("from auth import login\ndef run():\n    return login()\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        planner = RefactorPlanner(cart)

        plan = planner.plan_refactor("types.py", target_symbol="UserPayload", objective="Add JWT expiry")

        assert plan["target_file"] == "types.py"
        assert plan["target_symbol"] == "UserPayload"
        assert plan["total_steps"] >= 3

        step_files = [s["file"] for s in plan["execution_steps"]]
        # types.py should precede auth.py which precedes server.py
        assert step_files.index("types.py") < step_files.index("auth.py")
        assert step_files.index("auth.py") < step_files.index("server.py")

        # Markdown representation
        md = planner.format_plan_markdown(plan)
        assert "[REFACTOR PLAN]" in md
