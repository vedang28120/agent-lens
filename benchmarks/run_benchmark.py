"""
AgentLens Empirical Benchmark Suite
Measures real token economies and cold vs warm AST scan latency
using real files from the active repository.
"""

import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.realpath(os.path.abspath(".")))

from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.packer import ContextPacker
from agent_lens.core.sandbox import GhostPatchSandbox


def measure_tokens(text: str) -> int:
    """Standard LLM code token estimation (~3.8 characters per token)."""
    return max(1, int(len(text) / 3.8))


def run_benchmarks():
    root_dir = os.path.realpath(os.path.abspath("."))
    print("=" * 70)
    print("🔬 AGENTLENS EMPIRICAL MEASUREMENT & BENCHMARK SUITE")
    print(f"Target Repository: {root_dir}")
    print("=" * 70)

    # 1. Cold Scan vs Warm Scan Benchmark
    print("\n[1] CARTOGRAPHY & CACHE LATENCY BENCHMARK:")
    # Remove existing cache if any for clean test
    cache_file = os.path.join(root_dir, ".agentlens", "ast_cache.db")
    if os.path.exists(cache_file):
        try:
            os.remove(cache_file)
        except Exception:
            pass

    t0 = time.perf_counter()
    cold_cart = CodebaseCartographer(root_dir, cache_enabled=True)
    cold_metrics = cold_cart.scan()
    cold_ms = (time.perf_counter() - t0) * 1000

    t1 = time.perf_counter()
    warm_cart = CodebaseCartographer(root_dir, cache_enabled=True)
    warm_metrics = warm_cart.scan()
    warm_ms = (time.perf_counter() - t1) * 1000

    speedup = cold_ms / warm_ms if warm_ms > 0 else 0
    print(f"  • Files Scanned: {cold_metrics['files_scanned']} files ({cold_metrics['total_lines']} LOC, {cold_metrics['symbols_indexed']} symbols)")
    print(f"  • Cold Scan (Parse All ASTs): {cold_ms:.2f} ms")
    print(f"  • Warm Scan (CAS-AST Cache):  {warm_ms:.2f} ms ({warm_metrics['cache_hits']} cache hits)")
    print(f"  • Latency Reduction:          {speedup:.1f}x speedup")

    # 2. Token Reduction Benchmarks on Real Code
    print("\n[2] TOKEN ECONOMY BENCHMARK (REAL REPO TASKS):")
    packer = ContextPacker(warm_cart)

    tasks = [
        {
            "id": "TASK_1",
            "name": "Inspect & patch detect_language in parser.py",
            "file": "agent_lens/core/parser.py",
            "caller_file": "tests/test_parser.py",
            "symbol": "detect_language",
            "desc": "Agent fixing file extension mappings"
        },
        {
            "id": "TASK_2",
            "name": "Audit do_GET route handling in app.py",
            "file": "agent_lens/server/app.py",
            "caller_file": "agent_lens/cli.py",
            "symbol": "do_GET",
            "desc": "Agent inspecting HTTP routes and security"
        },
        {
            "id": "TASK_3",
            "name": "Update calculate_blast_radius in cartography.py",
            "file": "agent_lens/core/cartography.py",
            "caller_file": "tests/test_cartography.py",
            "symbol": "calculate_blast_radius",
            "desc": "Agent tuning BFS graph traversal logic"
        },
    ]

    print("\n  A. Symbol Lookup / Inspection Phase (Card vs. Reading Target File):")
    print(f"  {'Task':<8} | {'Target Symbol':<25} | {'Whole File Read':<18} | {'Symbol Card':<16} | {'Reduction'}")
    print("  " + "-" * 85)

    tot_lookup_base = 0
    tot_lookup_card = 0

    for t in tasks:
        full_path = os.path.join(root_dir, t["file"])
        with open(full_path, "r", encoding="utf-8") as f:
            full_content = f.read()

        baseline_tokens = measure_tokens(full_content)
        card = warm_cart.get_symbol_card(t["symbol"])
        card_text = warm_cart.format_card_markdown(card) if card else ""
        card_tokens = measure_tokens(card_text)

        reduc = ((baseline_tokens - card_tokens) / baseline_tokens) * 100
        tot_lookup_base += baseline_tokens
        tot_lookup_card += card_tokens
        print(f"  {t['id']:<8} | {t['symbol']:<25} | {baseline_tokens:>5} tokens       | {card_tokens:>5} tokens      | -{reduc:.1f}%")

    avg_lookup_reduc = ((tot_lookup_base - tot_lookup_card) / tot_lookup_base) * 100
    print("  " + "-" * 85)
    print(f"  {'TOTALS':<8} | {'3 Lookup Queries':<25} | {tot_lookup_base:>5} tokens       | {tot_lookup_card:>5} tokens      | -{avg_lookup_reduc:.1f}%\n")

    print("  B. Realistic Task Edit Phase (Full Target + Caller/Test Files vs. Packed AST Slice):")
    print("     * Note: Slices contain full implementation of target + imports + sibling stubs for syntax integrity.")
    print(f"  {'Task':<8} | {'Target Symbol':<25} | {'Realistic Read':<18} | {'Packed AST Slice':<16} | {'Reduction'}")
    print("  " + "-" * 85)

    tot_edit_base = 0
    tot_edit_slice = 0

    for t in tasks:
        # Realistic standard agent read: Target file + Caller / Test file
        full_path = os.path.join(root_dir, t["file"])
        caller_path = os.path.join(root_dir, t["caller_file"])
        with open(full_path, "r", encoding="utf-8") as f:
            c1 = f.read()
        with open(caller_path, "r", encoding="utf-8") as f:
            c2 = f.read()

        realistic_baseline_tokens = measure_tokens(c1) + measure_tokens(c2)

        # AgentLens workflow: AST Context Slice with full implementation + target lines
        slice_res = packer.pack(t["symbol"], token_budget=1000)
        slice_tokens = slice_res["estimated_tokens"]

        reduc = ((realistic_baseline_tokens - slice_tokens) / realistic_baseline_tokens) * 100
        tot_edit_base += realistic_baseline_tokens
        tot_edit_slice += slice_tokens
        print(f"  {t['id']:<8} | {t['symbol']:<25} | {realistic_baseline_tokens:>5} tokens       | {slice_tokens:>5} tokens      | -{reduc:.1f}%")

    avg_edit_reduc = ((tot_edit_base - tot_edit_slice) / tot_edit_base) * 100
    print("  " + "-" * 85)
    print(f"  {'TOTALS':<8} | {'3 End-to-End Tasks':<25} | {tot_edit_base:>5} tokens       | {tot_edit_slice:>5} tokens      | -{avg_edit_reduc:.1f}%\n")

    # 3. Dynamic Analysis & False Confidence Limits
    print("\n[3] CALIBRATED CONFIDENCE & DYNAMIC ANALYSIS LIMITS:")
    sb = GhostPatchSandbox(warm_cart)
    dry_res = sb.dry_run_patch("agent_lens/core/cartography.py", full_content)
    print(f"  • Static Safety Verdict:      {dry_res['verdict']} (Score: {dry_res['safety_score']}/100)")
    print(f"  • Confidence Assessment:      {dry_res['confidence_assessment']}")
    print("  • Disclosed Caveats:")
    for c in dry_res["caveats"]:
        print(f"     * {c}")

    print("\n" + "=" * 70)
    print("✅ Benchmark execution complete.")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmarks()
