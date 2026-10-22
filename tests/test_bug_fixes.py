import os
import time
import sqlite3
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.guard import HallucinationGuard


def test_bug1_dependencies_declared_in_pyproject():
    """Bug 1: pyproject.toml must declare rapidfuzz and networkx as dependencies."""
    pyproject_path = os.path.join(os.path.dirname(__file__), "..", "pyproject.toml")
    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must be declared under dependencies list
    assert "rapidfuzz" in content, "rapidfuzz missing from pyproject.toml dependencies"
    assert "networkx" in content, "networkx missing from pyproject.toml dependencies"


def test_bug2_guard_schema_compatibility(tmp_path):
    """Bug 2: HallucinationGuard.verify_file() must include is_clean, flagged_count, and suggested_match."""
    test_file = tmp_path / "sample.py"
    # Create file with an unresolved import that triggers a suggestion
    test_file.write_text("import json_fake_module\n", encoding="utf-8")

    cart = CodebaseCartographer(str(tmp_path))
    cart.scan()
    guard = HallucinationGuard(cart)

    res = guard.verify_file(str(test_file))

    # Verify top-level keys expected by web/app.js
    assert "is_clean" in res, "verify_file() must return 'is_clean' for web/app.js"
    assert "flagged_count" in res, "verify_file() must return 'flagged_count' for web/app.js"
    assert "valid" in res
    assert "hallucination_count" in res

    # Verify clean file case
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("import json\n", encoding="utf-8")
    clean_res = guard.verify_file(str(clean_file))
    assert clean_res["is_clean"] is True
    assert clean_res["flagged_count"] == 0


def test_bug3_sse_activity_event_and_payload():
    """Bug 3: SSE activity broadcast must use event name 'file_change' and include 'event_type' in payload."""
    import inspect
    from agent_lens.server import app as server_app

    src = inspect.getsource(server_app.start_mission_control_server)
    # Must broadcast file_change so web/app.js evtSource listener triggers
    assert 'broadcaster.broadcast("file_change"' in src, "server must broadcast 'file_change' for app.js"
    # Payload must include event_type for act.event_type rendering
    assert '"event_type":' in src, "activity dict must contain 'event_type' key"


def test_bug4_graph_export_node_has_label(tmp_path):
    """Bug 4: get_graph_export() nodes must include 'label' property for web/app.js canvas & drawer."""
    f1 = tmp_path / "module_a.py"
    f1.write_text("def hello(): pass\n", encoding="utf-8")

    cart = CodebaseCartographer(str(tmp_path))
    cart.scan()
    export = cart.get_graph_export()

    nodes = export.get("nodes", [])
    assert len(nodes) > 0
    for node in nodes:
        assert "label" in node, f"Node {node.get('id')} missing 'label' property"
        assert node["label"] == os.path.basename(node["id"])


def test_bug5_ast_cache_sha256_cas(tmp_path):
    """Bug 5: AST cache must store sha256 and achieve cache hits across mtime changes when content is identical."""
    f = tmp_path / "service.py"
    f.write_text("def run(): return 42\n", encoding="utf-8")

    cart = CodebaseCartographer(str(tmp_path), cache_enabled=True)
    scan1 = cart.scan()
    assert scan1["files_scanned"] == 1
    assert scan1["cache_hits"] == 0

    # Verify SQLite schema has sha256 column
    with sqlite3.connect(cart.cache_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(ast_cache)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "sha256" in columns, "ast_cache table must include 'sha256' column"

    # Simulate git checkout / touch by modifying mtime WITHOUT changing content
    old_mtime = os.path.getmtime(str(f))
    new_mtime = old_mtime + 100.0
    os.utime(str(f), (new_mtime, new_mtime))

    # Scan again with a new cartographer instance
    cart2 = CodebaseCartographer(str(tmp_path), cache_enabled=True)
    scan2 = cart2.scan()
    # Should be a cache hit because SHA-256 hash matches
    assert scan2["cache_hits"] == 1, "AST cache must hit when content SHA-256 is unchanged despite mtime shift"


def test_issue6_ci_checkout_full_depth():
    """Issue #6 (Major): CI workflow must specify fetch-depth: 0 for worktree operations."""
    ci_path = os.path.join(os.path.dirname(__file__), "..", ".github", "workflows", "ci.yml")
    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "fetch-depth: 0" in content, "ci.yml must specify fetch-depth: 0 under actions/checkout"


def test_issue7_guard_explicit_method_indexed():
    """Issue #7 (Minor): verify_patch_hallucinations must be an indexed method on HallucinationGuard."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cart = CodebaseCartographer(repo_root)
    cart.scan()
    assert "verify_patch_hallucinations" in cart.symbol_index, (
        "verify_patch_hallucinations must be indexed as a method in AST symbol_index"
    )

    guard = HallucinationGuard(cart)
    res = guard.verify_file(os.path.join(repo_root, "agent_lens", "mcp", "server.py"))
    assert res["is_clean"] is True, f"mcp/server.py should be clean of hallucinations: {res.get('hallucinations')}"


def test_issue8_preflight_directory_support(tmp_path):
    """Issue #8 (Minor): PreflightChecker.check_file must support directory paths without crashing."""
    from agent_lens.core.preflight import PreflightChecker

    sub = tmp_path / "subpkg"
    sub.mkdir()
    (sub / "mod1.py").write_text("def fn1(): pass\n", encoding="utf-8")
    (sub / "mod2.json").write_text('{"key": "value"}', encoding="utf-8")

    res = PreflightChecker.check_file(str(tmp_path))
    assert res.get("is_directory") is True, "Preflight result should indicate is_directory"
    assert res["valid"] is True, "Directory preflight check should pass for valid files"
    assert res.get("checked_files", 0) >= 2, "Directory preflight should check contained code files"
