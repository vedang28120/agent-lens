import argparse
import json
import sys
import os
from .core.cartography import CodebaseCartographer
from .core.memory import AgentMemory
from .core.preflight import PreflightChecker
from .core.radar import ArchitectureRadar
from .core.packer import ContextPacker
from .core.sandbox import GhostPatchSandbox
from .core.sentinel import PortSentinel
from .core.guard import HallucinationGuard
from .core.planner import RefactorPlanner


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        prog="agent-lens",
        description="AgentLens - Autonomous AI Coding Assistant Exoskeleton & Mission Control",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Scan codebase and build AST & dependency graph")
    scan_parser.add_argument("path", nargs="?", default=".", help="Root directory to scan (default: .)")
    scan_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # card
    card_parser = subparsers.add_parser("card", help="Get ultra-dense token-optimized Symbol Card")
    card_parser.add_argument("symbol", help="Symbol name (function, class, method)")
    card_parser.add_argument("--file", "-f", help="File hint if symbol name is ambiguous")
    card_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    card_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # blast
    blast_parser = subparsers.add_parser("blast", help="Calculate blast radius and transitive impacts")
    blast_parser.add_argument("--file", "-f", required=True, help="Target file path")
    blast_parser.add_argument("--symbol", "-s", help="Target symbol name inside file")
    blast_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    blast_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # outline
    outline_parser = subparsers.add_parser("outline", help="Get structural outline of a file")
    outline_parser.add_argument("file", help="File to inspect")
    outline_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    outline_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # pack (Context Packer)
    pack_parser = subparsers.add_parser("pack", help="Intelligently slice codebase for prompt context")
    pack_parser.add_argument("query", help="Symbol name or search query to slice")
    pack_parser.add_argument("--budget", "-b", type=int, default=1200, help="Maximum token budget (default: 1200)")
    pack_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    pack_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # radar (Architecture Radar)
    radar_parser = subparsers.add_parser("radar", help="Architecture health, circular dependencies, God Nodes")
    radar_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    radar_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # cycles
    cycles_parser = subparsers.add_parser("cycles", help="Find circular import dependency chains")
    cycles_parser.add_argument("--root", default=".", help="Root directory (default: .)")

    # deadcode
    dead_parser = subparsers.add_parser("deadcode", help="Find dead / orphan symbols")
    dead_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    dead_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # verify (Hallucination Guard)
    verify_parser = subparsers.add_parser("verify", help="Check file for hallucinated method calls and non-existent imports")
    verify_parser.add_argument("file", help="File path to verify")
    verify_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    verify_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # plan (Refactor Planner)
    plan_parser = subparsers.add_parser("plan", help="Generate topologically sorted step-by-step refactor DAG")
    plan_parser.add_argument("file", help="Target file to refactor")
    plan_parser.add_argument("--symbol", "-s", help="Target symbol inside file")
    plan_parser.add_argument("--objective", "-o", default="Refactor", help="Refactoring objective")
    plan_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    plan_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # ghost-patch (Virtual Dry Run)
    patch_parser = subparsers.add_parser("ghost-patch", help="Simulate a code patch in shadow AST before touching disk")
    patch_parser.add_argument("--file", "-f", required=True, help="File to patch")
    patch_parser.add_argument("--content", "-c", help="New file content string")
    patch_parser.add_argument("--from-file", help="Read new content from file")
    patch_parser.add_argument("--root", default=".", help="Root directory (default: .)")
    patch_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # ports (Port Sentinel)
    ports_parser = subparsers.add_parser("ports", help="List active dev ports and processes")
    ports_parser.add_argument("--all", action="store_true", help="Show all ports, not just dev ports")
    ports_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # kill-port
    kill_parser = subparsers.add_parser("kill-port", help="Terminate process occupying a port")
    kill_parser.add_argument("port", type=int, help="Port to terminate")

    # preflight
    preflight_parser = subparsers.add_parser("preflight", help="Validate file syntax, imports, and conflict markers")
    preflight_parser.add_argument("file", help="File to validate")
    preflight_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # diff-check
    diff_parser = subparsers.add_parser("diff-check", help="Check git diff for accidental mass deletions")
    diff_parser.add_argument("--path", default=".", help="Git repo path (default: .)")

    # memory
    mem_parser = subparsers.add_parser("memory", help="Agent working memory and flight recorder")
    mem_subs = mem_parser.add_subparsers(dest="mem_action")

    # memory summary
    mem_subs.add_parser("summary", help="Compact briefing for agent context recovery")

    # memory hypo
    hypo_parser = mem_subs.add_parser("hypo", help="Manage hypotheses")
    hypo_parser.add_argument("action", choices=["list", "add", "update"])
    hypo_parser.add_argument("--id", type=int, help="Hypothesis ID (for update)")
    hypo_parser.add_argument("--statement", help="Hypothesis statement (for add)")
    hypo_parser.add_argument("--status", choices=["exploring", "confirmed", "refuted"], help="Status")
    hypo_parser.add_argument("--evidence", help="Supporting evidence or log proof")

    # memory decision
    dec_parser = mem_subs.add_parser("decision", help="Manage architectural decisions")
    dec_parser.add_argument("action", choices=["list", "add"])
    dec_parser.add_argument("--title", help="Decision title")
    dec_parser.add_argument("--rationale", help="Decision rationale")
    dec_parser.add_argument("--tradeoffs", default="", help="Tradeoffs considered")

    # memory memo
    memo_parser = mem_subs.add_parser("memo", help="Key-value fact store")
    memo_parser.add_argument("action", choices=["list", "set", "get"])
    memo_parser.add_argument("--key", help="Memo key")
    memo_parser.add_argument("--value", help="Memo value")

    # memory task
    task_parser = mem_subs.add_parser("task", help="Task checklist")
    task_parser.add_argument("action", choices=["list", "add", "update"])
    task_parser.add_argument("--id", type=int, help="Task ID")
    task_parser.add_argument("--title", help="Task title")
    task_parser.add_argument("--status", choices=["pending", "in_progress", "done", "blocked"])
    task_parser.add_argument("--priority", type=int, default=1)
    task_parser.add_argument("--notes", default="")

    # memory scratchpad
    scratch_parser = mem_subs.add_parser("scratchpad", help="Shared human-agent scratchpad")
    scratch_parser.add_argument("action", choices=["get", "set"])
    scratch_parser.add_argument("--content", help="New scratchpad text content")

    # mcp
    mcp_parser = subparsers.add_parser("mcp", help="Run AgentLens Model Context Protocol (MCP) server")
    mcp_parser.add_argument("--root", default=".", help="Root directory of codebase to expose")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch AgentLens Mission Control web dashboard")
    serve_parser.add_argument("--port", type=int, default=4141, help="Port to run server on (default: 4141)")
    serve_parser.add_argument("--root", default=".", help="Root directory of project to monitor (default: .)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch commands
    if args.command == "scan":
        cart = CodebaseCartographer(args.path)
        metrics = cart.scan()
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print(f"=== AgentLens Codebase Scan ===")
            print(f"Root: {metrics['root_path']}")
            print(f"Files Scanned: {metrics['files_scanned']}")
            print(f"Total Lines: {metrics['total_lines']}")
            print(f"Symbols Indexed: {metrics['symbols_indexed']} ({metrics['unique_symbol_names']} unique)")

    elif args.command == "card":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        card = cart.get_symbol_card(args.symbol, file_hint=args.file)
        if not card:
            print(f"Error: Symbol '{args.symbol}' not found in index.", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(card, indent=2))
        else:
            print(cart.format_card_markdown(card))

    elif args.command == "blast":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        blast = cart.calculate_blast_radius(args.file, symbol_name=args.symbol)
        if args.json:
            print(json.dumps(blast, indent=2))
        else:
            target = f"{blast['target_file']}" + (f":::{blast['target_symbol']}" if blast['target_symbol'] else "")
            print(f"=== Blast Radius Analysis: {target} ===")
            print(f"Risk Level: {blast['risk_level']}")
            print(f"Impacted Files ({len(blast['impacted_files'])}):")
            for f in blast['impacted_files']:
                print(f"  - {f}")
            if blast['related_tests']:
                print(f"Related Test Suites ({len(blast['related_tests'])}):")
                for t in blast['related_tests']:
                    print(f"  - {t}")

    elif args.command == "outline":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        outline = cart.get_file_outline(args.file)
        if not outline:
            print(f"Error: File '{args.file}' not found or parsed.", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(outline, indent=2))
        else:
            print(cart.format_outline_markdown(outline))

    elif args.command == "pack":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        packer = ContextPacker(cart)
        res = packer.pack(args.query, token_budget=args.budget)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"=== Context Slice for '{args.query}' (Est. Tokens: ~{res['estimated_tokens']} / Budget: {args.budget}) ===")
            print(res["slice_content"])

    elif args.command == "radar":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        radar = ArchitectureRadar(cart)
        report = radar.analyze()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"=== AgentLens Architecture Radar ===")
            print(f"Health Score: {report['health_score']}/100 [{report['status']}]")
            print(f"Circular Dependencies: {report['circular_count']}")
            for cycle in report["circular_dependencies"]:
                print(f"  [CYCLE] {' -> '.join(cycle)}")
            print(f"God Nodes Identified ({len(report['god_nodes'])}):")
            for g in report["god_nodes"][:5]:
                print(f"  - {g['file']} (in-degree: {g['in_degree']}, lines: {g['lines']}, risk: {g['risk']})")
            print(f"Orphan Symbols: {report['orphan_count']}")
            for o in report["orphan_symbols"][:5]:
                print(f"  - {o['symbol']} ({o['file']}:{o['line']})")

    elif args.command == "cycles":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        radar = ArchitectureRadar(cart)
        report = radar.analyze()
        if not report["circular_dependencies"]:
            print("✓ No circular dependencies detected across codebase.")
        else:
            print(f"Alert: {len(report['circular_dependencies'])} circular dependency chain(s) found:")
            for c in report["circular_dependencies"]:
                print(f"  Loop: {' -> '.join(c)}")

    elif args.command == "deadcode":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        radar = ArchitectureRadar(cart)
        report = radar.analyze()
        if args.json:
            print(json.dumps(report["orphan_symbols"], indent=2))
        else:
            print(f"Orphan Symbols ({report['orphan_count']} candidate dead symbols):")
            for o in report["orphan_symbols"]:
                print(f"  - `{o['symbol']}` ({o['kind']}) in {o['file']}:{o['line']}")

    elif args.command == "verify":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        guard = HallucinationGuard(cart)
        res = guard.verify_file(args.file)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            status_str = "✓ VERIFIED CLEAN" if res["valid"] else f"✗ {res['hallucination_count']} ISSUE(S) DETECTED"
            print(f"=== Hallucination Guard: {args.file} [{status_str}] ===")
            for h in res["hallucinations"]:
                print(f"  [L{h['line']}] {h['message']}")

    elif args.command == "plan":
        cart = CodebaseCartographer(args.root)
        cart.scan()
        planner = RefactorPlanner(cart)
        plan = planner.plan_refactor(args.file, target_symbol=args.symbol, objective=args.objective)
        if args.json:
            print(json.dumps(plan, indent=2))
        else:
            print(planner.format_plan_markdown(plan))

    elif args.command == "ghost-patch":
        content = args.content
        if args.from_file:
            with open(args.from_file, "r", encoding="utf-8") as f:
                content = f.read()
        if not content:
            print("Error: --content or --from-file is required.", file=sys.stderr)
            sys.exit(1)

        cart = CodebaseCartographer(args.root)
        cart.scan()
        sandbox = GhostPatchSandbox(cart)
        verdict = sandbox.dry_run_patch(args.file, content)
        if args.json:
            print(json.dumps(verdict, indent=2))
        else:
            print(f"=== Ghost Patch Verdict: [{verdict['verdict']}] (Safety Score: {verdict['safety_score']}/100) ===")
            if verdict["added_symbols"]:
                print(f"Added Symbols: {', '.join(verdict['added_symbols'])}")
            if verdict["removed_symbols"]:
                print(f"Removed Symbols: {', '.join(verdict['removed_symbols'])}")
            if verdict["modified_symbols"]:
                print(f"Modified Symbols: {len(verdict['modified_symbols'])}")
            for b in verdict["breakages"]:
                print(f"  [BREAKAGE] {b}")
            for w in verdict["warnings"]:
                print(f"  [WARNING]  {w}")

    elif args.command == "ports":
        ports = PortSentinel.list_listening_ports()
        if not args.all:
            ports = [p for p in ports if p.get("is_dev_port")]
        if args.json:
            print(json.dumps(ports, indent=2))
        else:
            print("=== Active Listening Developer Ports ===")
            if not ports:
                print("No active developer ports detected.")
            for p in ports:
                print(f"Port {p['port']:<6} | PID {p['pid']:<6} | {p['process_name']}")

    elif args.command == "kill-port":
        res = PortSentinel.kill_port(args.port)
        status_sym = "✓" if res["success"] else "✗"
        print(f"[{status_sym}] {res['message']}")

    elif args.command == "preflight":
        res = PreflightChecker.check_file(args.file)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            status_str = "✓ PASS" if res["valid"] else "✗ FAIL"
            print(f"Preflight Check: {args.file} [{status_str}]")
            for err in res["errors"]:
                print(f"  [ERROR] {err}")
            for warn in res["warnings"]:
                print(f"  [WARN]  {warn}")
            if not res["valid"]:
                sys.exit(1)

    elif args.command == "diff-check":
        res = PreflightChecker.check_git_diff_safety(args.path)
        print(f"Git Diff Safety: {res.get('status')}")
        if "total_added" in res:
            print(f"Lines Added: +{res['total_added']} | Lines Deleted: -{res['total_deleted']}")
        for warn in res.get("warnings", []):
            print(f"  [ALERT] {warn}")

    elif args.command == "memory":
        mem = AgentMemory()
        if args.mem_action == "summary" or not args.mem_action:
            print(mem.get_compact_summary())
        elif args.mem_action == "hypo":
            if args.action == "list":
                print(json.dumps(mem.get_hypotheses(), indent=2))
            elif args.action == "add":
                if not args.statement:
                    print("Error: --statement is required", file=sys.stderr)
                    sys.exit(1)
                hid = mem.add_hypothesis(args.statement, status=args.status or "exploring", evidence=args.evidence or "")
                print(f"Created hypothesis #{hid}")
            elif args.action == "update":
                if not args.id:
                    print("Error: --id is required", file=sys.stderr)
                    sys.exit(1)
                mem.update_hypothesis(args.id, status=args.status, evidence=args.evidence)
                print(f"Updated hypothesis #{args.id}")
        elif args.mem_action == "decision":
            if args.action == "list":
                print(json.dumps(mem.get_decisions(), indent=2))
            elif args.action == "add":
                if not args.title or not args.rationale:
                    print("Error: --title and --rationale are required", file=sys.stderr)
                    sys.exit(1)
                did = mem.add_decision(args.title, args.rationale, tradeoffs=args.tradeoffs)
                print(f"Recorded decision #{did}")
        elif args.mem_action == "memo":
            if args.action == "list":
                print(json.dumps(mem.get_all_memos(), indent=2))
            elif args.action == "set":
                if not args.key or args.value is None:
                    print("Error: --key and --value are required", file=sys.stderr)
                    sys.exit(1)
                mem.set_memo(args.key, args.value)
                print(f"Stored memo '{args.key}'")
            elif args.action == "get":
                if not args.key:
                    print("Error: --key is required", file=sys.stderr)
                    sys.exit(1)
                val = mem.get_memo(args.key)
                print(val if val is not None else "(nil)")
        elif args.mem_action == "task":
            if args.action == "list":
                print(json.dumps(mem.get_tasks(), indent=2))
            elif args.action == "add":
                if not args.title:
                    print("Error: --title is required", file=sys.stderr)
                    sys.exit(1)
                tid = mem.add_task(args.title, status=args.status or "pending", priority=args.priority, notes=args.notes)
                print(f"Created task #{tid}")
            elif args.action == "update":
                if not args.id:
                    print("Error: --id is required", file=sys.stderr)
                    sys.exit(1)
                mem.update_task(args.id, status=args.status, notes=args.notes)
                print(f"Updated task #{args.id}")
        elif args.mem_action == "scratchpad":
            if args.action == "get":
                scratch = mem.get_scratchpad()
                print(scratch["content"])
            elif args.action == "set":
                if args.content is None:
                    print("Error: --content is required", file=sys.stderr)
                    sys.exit(1)
                mem.update_scratchpad(args.content, updated_by="agent")
                print("Scratchpad updated.")

    elif args.command == "mcp":
        from .mcp.server import AgentLensMCPServer
        server = AgentLensMCPServer(root_dir=args.root)
        server.run_stdio()

    elif args.command == "serve":
        from .server.app import start_mission_control_server
        start_mission_control_server(port=args.port, root_dir=args.root)


if __name__ == "__main__":
    main()
