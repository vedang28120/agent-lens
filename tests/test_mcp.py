import os
import tempfile
import pytest
from agent_lens.mcp.server import AgentLensMCPServer


def test_mcp_server_tool_definitions():
    with tempfile.TemporaryDirectory() as tmpdir:
        server = AgentLensMCPServer(root_dir=tmpdir)
        tools = server.get_tool_definitions()

        tool_names = [t["name"] for t in tools]
        assert "lens_get_symbol_card" in tool_names
        assert "lens_pack_context" in tool_names
        assert "lens_blast_radius" in tool_names
        assert "lens_ghost_patch" in tool_names
        assert "lens_verify_hallucinations" in tool_names
        assert "lens_plan_refactor" in tool_names
        assert "lens_manage_memory" in tool_names
        assert "lens_get_repo_map" in tool_names
        assert "lens_audit_dynamic_risk" in tool_names
        assert "lens_kill_port" in tool_names


def test_mcp_server_tool_call_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_file = os.path.join(tmpdir, "core.py")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("def sample_function():\n    return 'test_slice'\n")

        server = AgentLensMCPServer(root_dir=tmpdir)

        # Call lens_pack_context
        res = server.handle_call_tool("lens_pack_context", {"query": "sample_function", "token_budget": 500})
        assert "content" in res
        assert len(res["content"]) > 0
        assert "AGENTLENS CONTEXT SLICE" in res["content"][0]["text"]

        # Call lens_manage_memory
        mem_res = server.handle_call_tool("lens_manage_memory", {
            "action": "add_hypothesis",
            "statement": "Testing MCP server",
            "status": "exploring"
        })
        assert "Created hypothesis" in mem_res["content"][0]["text"]

        # Call lens_get_repo_map
        map_res = server.handle_call_tool("lens_get_repo_map", {"token_budget": 500})
        assert "content" in map_res
        assert "REPOSITORY STRUCTURE MAP" in map_res["content"][0]["text"]

        # Call lens_audit_dynamic_risk
        risk_res = server.handle_call_tool("lens_audit_dynamic_risk", {"symbol": "sample_function"})
        assert "content" in risk_res
        assert "dynamic_risk_level" in risk_res["content"][0]["text"]

        # Call lens_kill_port without confirmation (should require confirmation)
        kill_res = server.handle_call_tool("lens_kill_port", {"port": 9999, "confirm": False})
        assert "content" in kill_res
