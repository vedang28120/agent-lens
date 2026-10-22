import sys
import json
import os
from typing import Dict, Any, List, Optional

from ..core.cartography import CodebaseCartographer
from ..core.memory import AgentMemory
from ..core.packer import ContextPacker
from ..core.sandbox import GhostPatchSandbox
from ..core.guard import HallucinationGuard
from ..core.radar import ArchitectureRadar
from ..core.planner import RefactorPlanner
from ..core.preflight import PreflightChecker
from ..core.shadow import GitShadowSandbox
from ..core.delegation import DelegationContractGenerator


class AgentLensMCPServer:
    """Implements JSON-RPC 2.0 MCP (Model Context Protocol) Server for AgentLens."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = os.path.realpath(os.path.abspath(root_dir))
        self.cart = CodebaseCartographer(self.root_dir)
        self.cart.scan()
        self.memory = AgentMemory()
        self.packer = ContextPacker(self.cart)
        self.sandbox = GhostPatchSandbox(self.cart)
        self.guard = HallucinationGuard(self.cart)
        self.radar = ArchitectureRadar(self.cart)
        self.planner = RefactorPlanner(self.cart)
        self.shadow = GitShadowSandbox(self.cart)
        self.delegation = DelegationContractGenerator(self.cart)

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "lens_get_symbol_card",
                "description": "Returns a 92% token-reduced Symbol Card containing signature, docstring, callers, line bounds, and blast radius risk.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "The function, class, or method name to look up."},
                        "file_hint": {"type": "string", "description": "Optional file path hint if symbol is overloaded."},
                        "format": {"type": "string", "enum": ["compact", "json"], "description": "Output format: 'compact' (dense text, default) or 'json'."}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "lens_pack_context",
                "description": "Prunes sibling function bodies into a token-budgeted prompt slice, keeping imports, target implementation, and callers without syntax corruption.",
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
                        "symbol": {"type": "string", "description": "Optional specific symbol name inside the file."},
                        "format": {"type": "string", "enum": ["compact", "json"], "description": "Output format: 'compact' or 'json'."}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "lens_ghost_patch",
                "description": "Simulates modifying a full file in shadow AST without touching disk. Detects syntax errors, removed symbols, and specific caller breakages.",
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
                "name": "lens_ghost_patch_diff",
                "description": "Token-efficient patch dry-run: applies a localized search-and-replace block or unified diff in-memory to detect regressions without sending full files.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "description": "Target file path."},
                        "search_block": {"type": "string", "description": "Exact text block to replace."},
                        "replace_block": {"type": "string", "description": "Proposed new text replacement."},
                        "diff_patch": {"type": "string", "description": "Optional unified diff hunk to apply."}
                    },
                    "required": ["file"]
                }
            },
            {
                "name": "lens_shadow_test_sandbox",
                "description": "Executes actual test suite (pytest) against proposed patches in an ephemeral, isolated Git worktree without touching developer's working directory.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_patches": {"type": "object", "description": "Dict of file_path -> proposed_content."},
                        "test_command": {"type": "string", "description": "Command to run (default: 'pytest')."},
                        "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)."}
                    },
                    "required": ["file_patches"]
                }
            },
            {
                "name": "lens_generate_delegation_briefing",
                "description": "Generates a token-budgeted (<600 tokens) subagent work contract specifying exact symbol contracts, scoped file boundaries, and verification criteria.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "objective": {"type": "string", "description": "Subagent task goal."},
                        "target_files": {"type": "array", "items": {"type": "string"}, "description": "Allowed files to modify."},
                        "target_symbols": {"type": "array", "items": {"type": "string"}, "description": "Optional specific symbols."},
                        "test_command": {"type": "string", "description": "Verification command."}
                    },
                    "required": ["objective", "target_files"]
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
                "description": "Stores and retrieves persistent hypotheses, decisions, tasks, memos, scratchpad, and session recovery briefings.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": [
                                "get_summary", "add_hypothesis", "update_hypothesis", "get_hypotheses",
                                "add_task", "update_task", "get_tasks",
                                "add_decision", "get_decisions",
                                "set_memo", "get_memo", "get_scratchpad", "update_scratchpad"
                            ]
                        },
                        "id": {"type": "integer", "description": "Task or Hypothesis ID for updates."},
                        "statement": {"type": "string", "description": "Hypothesis statement."},
                        "status": {"type": "string", "description": "Status (exploring, confirmed, refuted, pending, in_progress, done, blocked)."},
                        "evidence": {"type": "string", "description": "Supporting evidence or proof."},
                        "title": {"type": "string", "description": "Task or Decision title."},
                        "notes": {"type": "string", "description": "Task notes."},
                        "priority": {"type": "integer", "description": "Task priority (1: Normal, 2: High, 3: Critical)."},
                        "rationale": {"type": "string", "description": "Decision rationale."},
                        "key": {"type": "string", "description": "Memo key."},
                        "value": {"type": "string", "description": "Memo value."},
                        "content": {"type": "string", "description": "Scratchpad content."}
                    },
                    "required": ["action"]
                }
            }
        ]

    def handle_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        fmt = arguments.get("format", "compact")

        if tool_name == "lens_get_symbol_card":
            card = self.cart.get_symbol_card(arguments["symbol"], file_hint=arguments.get("file_hint"))
            if not card:
                return {"content": [{"type": "text", "text": f"Symbol '{arguments['symbol']}' not found."}], "isError": True}
            text = self.cart.format_card_markdown(card) if fmt == "compact" else json.dumps(card, indent=2)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "lens_pack_context":
            res = self.packer.pack(arguments["query"], token_budget=arguments.get("token_budget", 1000))
            return {"content": [{"type": "text", "text": res["slice_content"]}]}

        elif tool_name == "lens_blast_radius":
            blast = self.cart.calculate_blast_radius(arguments["file"], symbol_name=arguments.get("symbol"))
            if fmt == "compact":
                tests_str = ", ".join(blast["related_tests"][:4]) if blast["related_tests"] else "None"
                text = (
                    f"### Blast Radius: `{blast['target_file']}` (Risk: **{blast['risk_level']}**)\n"
                    f"- Impacted Files ({len(blast['impacted_files'])}): {', '.join(blast['impacted_files'][:8])}\n"
                    f"- Related Tests: {tests_str}\n"
                    f"- Impacted Callers ({len(blast['impacted_symbols'])}): {', '.join(blast['impacted_symbols'][:6])}"
                )
            else:
                text = json.dumps(blast, indent=2)
            return {"content": [{"type": "text", "text": text}]}

        elif tool_name == "lens_ghost_patch":
            verdict = self.sandbox.dry_run_patch(arguments["file"], arguments["proposed_content"])
            return {"content": [{"type": "text", "text": json.dumps(verdict, indent=2)}]}

        elif tool_name == "lens_ghost_patch_diff":
            verdict = self.sandbox.dry_run_patch_diff(
                arguments["file"],
                search_block=arguments.get("search_block"),
                replace_block=arguments.get("replace_block"),
                diff_patch=arguments.get("diff_patch"),
            )
            return {"content": [{"type": "text", "text": json.dumps(verdict, indent=2)}]}

        elif tool_name == "lens_shadow_test_sandbox":
            res = self.shadow.run_shadow_test(
                arguments["file_patches"],
                test_command=arguments.get("test_command", "pytest"),
                timeout=arguments.get("timeout", 30),
            )
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif tool_name == "lens_generate_delegation_briefing":
            briefing = self.delegation.generate_briefing(
                objective=arguments["objective"],
                target_files=arguments["target_files"],
                target_symbols=arguments.get("target_symbols"),
                test_command=arguments.get("test_command"),
            )
            return {"content": [{"type": "text", "text": briefing["markdown"]}]}

        elif tool_name == "lens_verify_hallucinations":
            res = self.guard.verify_patch_hallucinations(arguments["file"], content=arguments.get("content"))
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}

        elif tool_name == "lens_plan_refactor":
            plan = self.planner.plan_refactor(
                arguments["file"],
                target_symbol=arguments.get("symbol"),
                objective=arguments.get("objective", "Refactor")
            )
            return {"content": [{"type": "text", "text": self.planner.format_plan_markdown(plan)}]}

        elif tool_name == "lens_manage_memory":
            act = arguments["action"]

            # Summary
            if act == "get_summary":
                return {"content": [{"type": "text", "text": self.memory.get_compact_summary()}]}

            # Hypotheses
            elif act == "add_hypothesis":
                hid = self.memory.add_hypothesis(
                    arguments["statement"],
                    status=arguments.get("status", "exploring"),
                    evidence=arguments.get("evidence", "")
                )
                return {"content": [{"type": "text", "text": f"Created hypothesis #{hid}"}]}
            elif act == "update_hypothesis":
                self.memory.update_hypothesis(
                    arguments["id"],
                    status=arguments.get("status"),
                    evidence=arguments.get("evidence")
                )
                return {"content": [{"type": "text", "text": f"Updated hypothesis #{arguments['id']}"}]}
            elif act == "get_hypotheses":
                hypos = self.memory.get_hypotheses(status=arguments.get("status"))
                return {"content": [{"type": "text", "text": json.dumps(hypos, indent=2)}]}

            # Tasks
            elif act == "add_task":
                tid = self.memory.add_task(
                    arguments["title"],
                    status=arguments.get("status", "pending"),
                    priority=arguments.get("priority", 1),
                    notes=arguments.get("notes", "")
                )
                return {"content": [{"type": "text", "text": f"Created task #{tid}"}]}
            elif act == "update_task":
                self.memory.update_task(
                    arguments["id"],
                    status=arguments.get("status"),
                    notes=arguments.get("notes"),
                    priority=arguments.get("priority")
                )
                return {"content": [{"type": "text", "text": f"Updated task #{arguments['id']}"}]}
            elif act == "get_tasks":
                tasks = self.memory.get_tasks(status=arguments.get("status"))
                return {"content": [{"type": "text", "text": json.dumps(tasks, indent=2)}]}

            # Decisions
            elif act == "add_decision":
                did = self.memory.add_decision(
                    arguments["title"],
                    arguments.get("rationale", ""),
                    tradeoffs=arguments.get("tradeoffs", "")
                )
                return {"content": [{"type": "text", "text": f"Recorded decision #{did}"}]}
            elif act == "get_decisions":
                decs = self.memory.get_decisions()
                return {"content": [{"type": "text", "text": json.dumps(decs, indent=2)}]}

            # Memos
            elif act == "set_memo":
                self.memory.set_memo(arguments["key"], arguments["value"])
                return {"content": [{"type": "text", "text": f"Stored memo '{arguments['key']}'"}]}
            elif act == "get_memo":
                val = self.memory.get_memo(arguments["key"])
                return {"content": [{"type": "text", "text": val or "None"}]}

            # Scratchpad
            elif act == "get_scratchpad":
                pad = self.memory.get_scratchpad()
                return {"content": [{"type": "text", "text": pad["content"]}]}
            elif act == "update_scratchpad":
                self.memory.update_scratchpad(arguments["content"], updated_by="agent")
                return {"content": [{"type": "text", "text": "Scratchpad updated."}]}

        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}

    def run_stdio(self):
        """Standard IO JSON-RPC 2.0 loop for Model Context Protocol."""
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
                        "serverInfo": {"name": "agent-lens", "version": "1.1.0"}
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
