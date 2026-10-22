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
            "symbol": "detect_language",
            "desc": "Agent fixing file extension mappings"
        },
        {
            "id": "TASK_2",
            "name": "Audit do_GET route handling in app.py",
            "file": "agent_lens/server/app.py",
            "symbol": "do_GET",
            "desc": "Agent inspecting HTTP routes and security"
        },
        {
            "id": "TASK_3",
            "name": "Update calculate_blast_radius in cartography.py",
            "file": "agent_lens/core/cartography.py",
            "symbol": "calculate_blast_radius",
            "desc": "Agent tuning BFS graph traversal logic"
        },
    ]

    total_baseline_tokens = 0
    total_lens_tokens = 0

    print(f"{'Task':<8} | {'Target Symbol':<25} | {'Baseline (Whole File)':<22} | {'AgentLens Symbol Card':<22} | {'Reduction'}")
    print("-" * 95)

    for t in tasks:
        full_path = os.path.join(root_dir, t["file"])
        with open(full_path, "r", encoding="utf-8") as f:
            full_content = f.read()

        baseline_chars = len(full_content)
        baseline_tokens = measure_tokens(full_content)

        # AgentLens Symbol Card
        card = warm_cart.get_symbol_card(t["symbol"])
        card_text = warm_cart.format_card_markdown(card) if card else ""
        card_chars = len(card_text)
        card_tokens = measure_tokens(card_text)

        # Context slice with target implementation
        slice_res = packer.pack(t["symbol"], token_budget=1000)
        slice_tokens = slice_res["estimated_tokens"]

        reduction_pct = ((baseline_tokens - card_tokens) / baseline_tokens) * 100
        total_baseline_tokens += baseline_tokens
        total_lens_tokens += card_tokens

        print(f"{t['id']:<8} | {t['symbol']:<25} | {baseline_tokens:>6} tokens ({baseline_chars}c)  | {card_tokens:>6} tokens ({card_chars}c)   | -{reduction_pct:.1f}%")

    avg_reduction = ((total_baseline_tokens - total_lens_tokens) / total_baseline_tokens) * 100
    print("-" * 95)
    print(f"TOTALS   | 3 Representative Tasks    | {total_baseline_tokens:>6} tokens ({total_baseline_tokens * 3.8:.0f}c)  | {total_lens_tokens:>6} tokens ({total_lens_tokens * 3.8:.0f}c)   | -{avg_reduction:.1f}% average")

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
