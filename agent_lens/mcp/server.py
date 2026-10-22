import sys
import json
import os
from typing import Dict, Any, List

from ..core.cartography import CodebaseCartographer
from ..core.memory import AgentMemory
from ..core.packer import ContextPacker
from ..core.sandbox import GhostPatchSandbox
from ..core.guard import HallucinationGuard
from ..core.radar import ArchitectureRadar
from ..core.planner import RefactorPlanner
from ..core.preflight import PreflightChecker


class AgentLensMCPServer:
    """Implements JSON-RPC 2.0 MCP (Model Context Protocol) Server for AgentLens."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.abspath(root_dir)
        self.cart = CodebaseCartographer(self.root_dir)
        self.cart.scan()
        self.memory = AgentMemory()
        self.packer = ContextPacker(self.cart)
        self.sandbox = GhostPatchSandbox(self.cart)
        self.guard = HallucinationGuard(self.cart)
        self.radar = ArchitectureRadar(self.cart)
        self.planner = RefactorPlanner(self.cart)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "lens_get_symbol_card",
                "description": "Returns a 92% token-reduced Symbol Card containing signature, docstring, callers, line bounds, and blast radius risk.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The function, class, or method name to look up."},
                        "file_hint": {"type": "string", "description": "Optional file path hint if symbol is overloaded."}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "lens_pack_context",
                "description": "Prunes sibling function bodies into a token-budgeted prompt slice, keeping imports, target implementation, and callers.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Target symbol or function to pack."},
                        "token_budget": {"type": "integer", "description": "Maximum token budget (default: 1000)."}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "lens_blast_radius",
                "description": "Calculates all downstream callers, dependent modules, and test suites affected by modifying a file or symbol.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Target file path."},
                        "symbol": {"type": "string", "description": "Optional specific symbol name inside the file."}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "lens_ghost_patch",
                "description": "Simulates modifying a file in shadow AST without touching disk. Detects syntax errors, removed symbols, and specific caller breakages.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Target file path."},
                        "proposed_content": {"type": "string", "description": "The complete replacement code to test."}
                    },
                    "required": ["file", "proposed_content"]
                }
            },
            {
                "name": "lens_verify_hallucinations",
                "description": "Inspects a file for hallucinated method calls, non-existent imports, and symbol misspellings with fuzzy match suggestions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "File path to verify."},
                        "content": {"type": "string", "description": "Optional raw code snippet to check instead of reading disk."}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "lens_plan_refactor",
                "description": "Generates a topologically sorted, blast-ordered step-by-step refactor execution plan.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Target file path."},
                        "symbol": {"type": "string", "description": "Optional target symbol name."},
                        "objective": {"type": "string", "description": "Brief description of the refactor goal."}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "lens_manage_memory",
                "description": "Stores and retrieves persistent hypotheses, decisions, tasks, memos, and session recovery briefings.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["get_summary", "add_hypothesis", "update_hypothesis", "add_task", "update_task", "add_decision"]},
                        "statement": {"type": "string", "description": "Hypothesis statement (for add_hypothesis)."},
                        "status": {"type": "string", "description": "Status (exploring, confirmed, refuted, pending, done)."},
                        "evidence": {"type": "string", "description": "Supporting evidence or proof."},
                        "title": {"type": "string", "description": "Task or Decision title."},
                        "rationale": {"type": "string", "description": "Decision rationale."}
                    },
                    "required": ["action"]
                }
            }
        ]

    def handle_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "lens_get_symbol_card":
            card = self.cart.get_symbol_card(arguments["symbol"], file_hint=arguments.get("file_hint"))
            if not card:
                return {"content": [{"type": "text", "text": f"Symbol '{arguments['symbol']}' not found."}], "isError": True}
            return {"content": [{"type": "text", "text": self.cart.format_card_markdown(card)}]}

        elif tool_name == "lens_pack_context":
            res = self.packer.pack(arguments["query"], token_budget=arguments.get("token_budget", 1000))
            return {"content": [{"type": "text", "text": res["slice_content"]}]}

        elif tool_name == "lens_blast_radius":
            blast = self.cart.calculate_blast_radius(arguments["file"], symbol_name=arguments.get("symbol"))
            return {"content": [{"type": "text", "text": json.dumps(blast, indent=2)}]}

        elif tool_name == "lens_ghost_patch":
            verdict = self.sandbox.dry_run_patch(arguments["file"], arguments["proposed_content"])
            return {"content": [{"type": "text", "text": json.dumps(verdict, indent=2)}]}

        elif tool_name == "lens_verify_hallucinations":
            res = self.guard.verify_file(arguments["file"], content=arguments.get("content"))
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif tool_name == "lens_plan_refactor":
            plan = self.planner.plan_refactor(arguments["file"], target_symbol=arguments.get("symbol"), objective=arguments.get("objective", "Refactor"))
            return {"content": [{"type": "text", "text": self.planner.format_plan_markdown(plan)}]}

        elif tool_name == "lens_manage_memory":
            act = arguments["action"]
            if act == "get_summary":
                return {"content": [{"type": "text", "text": self.memory.get_compact_summary()}]}
            elif act == "add_hypothesis":
                hid = self.memory.add_hypothesis(arguments["statement"], status=arguments.get("status", "exploring"), evidence=arguments.get("evidence", ""))
                return {"content": [{"type": "text", "text": f"Created hypothesis #{hid}"}]}
            elif act == "add_task":
                tid = self.memory.add_task(arguments["title"], status=arguments.get("status", "pending"))
                return {"content": [{"type": "text", "text": f"Created task #{tid}"}]}
            elif act == "add_decision":
                did = self.memory.add_decision(arguments["title"], arguments.get("rationale", ""))
                return {"content": [{"type": "text", "text": f"Recorded decision #{did}"}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

    def run_stdio(self):
        """Standard JSON-RPC 2.0 loop over stdin/stdout."""
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "agent-lens", "version": "1.0.0"}
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": self.get_tool_definitions()}
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                res = self.handle_call_tool(tool_name, args)
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": res
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()


def run_mcp_server():
    server = AgentLensMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    run_mcp_server()
