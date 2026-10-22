# 🔬 AgentLens: Codebase Cartography & Safe Testing Exoskeleton for AI Agents

[![Tests](https://img.shields.io/badge/tests-36%20passed-brightgreen.svg)](tests/)
[![CI](https://img.shields.io/badge/CI-Ubuntu%20%7C%20macOS%20%7C%20Windows-blue.svg)](.github/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-JSON--RPC%202.0-blue.svg)](agent_lens/mcp/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> **AgentLens** is a developer exoskeleton, code cartography engine, and safe patch testing suite designed specifically for AI coding agents and human-agent pair programming. It runs natively as a CLI, a Model Context Protocol (MCP) server, and an interactive real-time Mission Control web dashboard.

---

## 🧭 Why AgentLens Exists

When an AI coding assistant operates inside a software codebase, it routinely encounters four critical operational failure modes:

1. **Token Starvation & Context Dilution**: Reading entire 1,500-line files just to inspect a single function signature or class interface consumes thousands of tokens and degrades attention on the core task.
2. **Blast Radius Blindness**: Blind refactors break distant callers, downstream modules, and test suites that the agent was unaware existed.
3. **Dirty Working Trees & Side-Effect Disasters**: Running speculative fixes and test commands directly in the developer's working directory risks uncommitted changes, broken dependencies, and shell injection.
4. **The Static Analysis Illusion**: Naive static tools claim code is "100% SAFE", blinding agents to dynamic dispatch (`getattr`), reflection, duck typing, and monkeypatching.

**AgentLens replaces guesswork with empirical cartography, token budgeting, and calibrated safety.**

---

## 🏛️ System Architecture

```
                                 ┌─────────────────────────────────┐
                                 │       AI Coding Assistant       │
                                 │ (Antigravity / Cursor / Claude) │
                                 └───────────────┬─────────────────┘
                                                 │
                                                 │ MCP (JSON-RPC 2.0 stdio)
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             AGENTLENS MCP SERVER                                 │
│  • Per-Tool Exception Translation (Shielded) • JSON-RPC 2.0 Compliance          │
│  • stdio / Local IPC Transport               • Scoped SQLite Working Memory      │
└───────────────┬────────────────────────────────┬─────────────────────────────────┘
                │                                │
                ▼                                ▼
┌───────────────────────────────┐ ┌────────────────────────────────────────────────┐
│      CORE CARTOGRAPHY         │ │                 SAFETY SUITE                   │
│  • Tree-Sitter & Python AST   │ │  • GhostPatch In-Memory AST Dry-Run            │
│  • Content-Addressable Cache  │ │  • Unified Diff Hunk Matcher & Validator       │
│  • PageRank Structural Maps   │ │  • Ephemeral Git Shadow-Worktrees (shell=False)│
│  • Transitive Blast Radius    │ │  • Dynamic Risk Auditor (getattr/reflection)   │
│  • ContextPacker (~90% cut)   │ │  • Hallucination Guard (Imports & Methods)     │
└───────────────┬───────────────┘ └────────────────┬───────────────────────────────┘
                │                                  │
                └─────────────────┬────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        MISSION CONTROL DASHBOARD (Web UI)                        │
│  • Force-Directed Dependency Graph         • Outlined High-Contrast Labels       │
│  • Interactive Blast Radius Simulator      • Responsive Multi-Tab Navigation     │
│  • Live Port Sentinel with Safe Confirm    • Real-Time Agent Memory Inspector    │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Capabilities

### 1. Token-Budgeted Code Cartography
- **Ultra-Dense Symbol Cards**: Generates token-compressed summaries (~50 tokens) containing function signatures, docstrings, exact line bounds, and known callers, achieving a **97.6% token reduction** over whole-file reads during lookup.
- **ContextPacker**: For code editing tasks, prunes sibling function bodies to stubs while preserving the target implementation, imports, and enclosing classes for a **90.1% token reduction**.
- **PageRank Repository Maps**: Analyzes codebase connectivity with NetworkX to generate Aider-style structural trees prioritized by architectural centrality under a strict token budget (e.g. <1,024 tokens).
- **CAS AST Caching**: SQLite-backed Content-Addressable Storage (CAS) caches parsed ASTs using file SHA-256 hashes, yielding an **11.7x indexing speedup** on warm scans.

### 2. Calibrated Blast Radius & Dynamic Risk
- **Transitive Impact Graph**: Breadth-first search (BFS) maps downstream callers and automatically identifies associated test files before an edit is made.
- **Dynamic Risk Auditing**: Scans for Python dynamic leaks (`getattr`, `hasattr`, `globals()`, string-literal symbol dispatch, duck typing) with heuristic noise filtering for common method names (`get`, `run`, `items`).
- **Hallucination Guard**: Cross-references imported modules and method calls against stdlib and project exports, proposing nearest-match corrections with Levenshtein distance.

### 3. Ephemeral Git Shadow-Worktrees & In-Memory Patching
- **GhostPatch AST Dry-Run**: Validates syntax and caller contract preservation in-memory without touching disk. Supports search/replace blocks and multi-hunk unified diffs with line-ending tolerance.
- **Detached Git Shadow Worktrees**: Executes test suites (`pytest`, `npm test`, `cargo test`) in an isolated ephemeral worktree (`git worktree add --detach`). Uncommitted modifications in the working tree are automatically synced into the sandbox, ensuring tests evaluate `WorkingTree + proposed_patch` while keeping the developer's working directory 100% clean.
- **Hardened Process Execution**: Commands execute with `shell=False`, argument vectorization (`shlex.split`), Windows path normalization, and blacklisting of raw interactive shells (`cmd.exe`, `powershell.exe`, `bash.exe`).

### 4. Agent Working Memory & Flight Recorder
- **Local SQLite Flight Recorder**: Stored in `.agentlens/memory.db`, tracking hypotheses, architectural decisions, task checklists, key-value memos, and a shared human-agent scratchpad.
- **Compact Briefing Generator**: Generates concise markdown summaries under 300 tokens to restore agent context after context window truncation or compaction.

### 5. Safe Port Sentinel
- **Dev Server Management**: Scans and identifies orphaned dev processes (Vite, Next.js, Flask, FastAPI) listening on common ports.
- **Two-Phase Confirmation**: Never terminates processes automatically; requires explicit `--confirm` (or `confirm=True` in MCP) with previewed PID, process name, and port numbers.

---

## 📊 Empirical Benchmarks & Evaluation

We evaluate AgentLens across two dimensions: **token compression** and **end-to-end task execution**.

### 1. Token & AST Compression Measurements
*Measured on an active 56-file repository (8,887 LOC, 544 indexed symbols):*

| Operation | Baseline Read | AgentLens Compressed | Compression |
|---|---|---|---|
| **Symbol Lookup Phase** | Full target file: 21,377 tokens | Symbol Card: 506 tokens | **-97.6% tokens** |
| **Code Editing Phase** | Target + Callers: 30,402 tokens | Packed AST Slice: 3,003 tokens | **-90.1% tokens** |
| **Codebase Indexing** | Cold Parse: 260.99 ms | Warm CAS Cache: 22.31 ms | **11.7x faster** |

*Reproduce via `python benchmarks/run_benchmark.py`.*

### 2. End-to-End Workflow Evaluation (Baseline vs. AgentLens)
*Simulating real developer bug fixes and refactor tasks end-to-end with automated test verification:*

| Task ID | Description | Baseline Tokens (Whole Files + Callers) | AgentLens Tokens (Card + Blast + Pack) | Net Token Savings | Test Verification | Working Tree Status |
|---|---|---|---|---|---|---|
| **TASK-1** | Bug Fix: Add JSX/TSX support to parser | 11,353 tokens | 1,763 tokens | **84.5%** | **PASS** (100%) | **CLEAN** (0 dirty files) |
| **TASK-2** | Refactor: Add traversal depth parameter | 6,497 tokens | 2,367 tokens | **63.6%** | **PASS** (100%) | **CLEAN** (0 dirty files) |
| **TASK-3** | Safe Patch: Update HTTP status route | 12,636 tokens | 1,285 tokens | **89.8%** | **PASS** (100%) | **CLEAN** (0 dirty files) |
| **TOTALS** | **3 End-to-End Engineering Tasks** | **30,486 tokens** | **5,415 tokens** | **82.2%** | **ALL PASS** | **100% CLEAN** |

*Reproduce via `python benchmarks/e2e_evaluation.py`.*

---

## 🔌 Model Context Protocol (MCP) Integration

AgentLens includes a standard JSON-RPC 2.0 MCP server for AI coding assistants (Google Antigravity, Claude Desktop, Cursor).

### Configuration
Add `agent-lens` to your MCP configuration file (e.g. `~/.gemini/config/mcp_config.json` or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "agent-lens": {
      "command": "python",
      "args": [
        "/path/to/agent-lens/run.py",
        "mcp",
        "--root",
        "."
      ]
    }
  }
}
```

> **Agent Protocol**: For recommended tool invocation ordering, see [`AGENT_PROTOCOL.md`](AGENT_PROTOCOL.md).

### Available MCP Tools

| Tool Name | Parameters | Purpose |
|---|---|---|
| `lens_get_symbol_card` | `symbol`, `file_hint?`, `format?` | Ultra-dense signature, docstring, bounds, and callers (~50 tokens). |
| `lens_pack_context` | `query`, `token_budget?` | AST-pruned syntax slice with target implementation. |
| `lens_get_repo_map` | `token_budget?` | PageRank-prioritized repository structure map (<1,024 tokens). |
| `lens_blast_radius` | `file`, `symbol?`, `format?` | Downstream impact radius, callers, and test files. |
| `lens_ghost_patch` | `file`, `proposed_content` | In-memory AST syntax and contract verification. |
| `lens_ghost_patch_diff` | `file`, `search_block?`, `replace_block?`, `diff_patch?` | Search-and-replace or unified diff hunk dry-run. |
| `lens_shadow_test_sandbox` | `file_patches`, `test_command?`, `timeout?` | Executes tests in an isolated, ephemeral Git worktree. |
| `lens_audit_dynamic_risk` | `symbol`, `file?` | Heuristic check for reflection, getattr, and duck typing. |
| `lens_verify_hallucinations` | `file`, `content?` | Checks imported modules and methods against valid exports. |
| `lens_plan_refactor` | `file`, `symbol?`, `objective?` | Generates dependency-ordered refactoring sequence. |
| `lens_generate_delegation_briefing` | `objective`, `target_files`, `test_command?` | Generates tight contract briefing for subagents (<600 tokens). |
| `lens_manage_memory` | `action`, `...` | SQLite working memory (hypotheses, tasks, decisions, memos). |
| `lens_kill_port` | `port`, `confirm`, `force_non_dev?` | Two-phase confirmed termination of orphaned dev servers. |

---

## 🖥️ Mission Control Web UI

Launch the real-time interactive dashboard:

```bash
python run.py serve --port 4141
```
Open **[http://localhost:4141](http://localhost:4141)** in your browser.

### Key Capabilities:
- **Interactive Cartography Graph**: Visualizes codebase topology, dependency clusters, and god nodes with force-directed physics and high-contrast outlined labels.
- **Symbol Explorer**: Instant search and token-efficient symbol card inspection.
- **Blast Radius Simulator**: Visualizes transitive downstream impact before making refactors.
- **Dynamic Risk Auditor**: Scans for reflection, dynamic string dispatch, and duck typing.
- **Refactor Planner**: Interactive step-by-step dependency-ordered refactoring guide.
- **Memory Flight Recorder**: Track hypotheses, architectural decisions, and tasks in real-time.
- **Port Sentinel**: Monitor listening dev ports with safe, two-phase termination confirmation.

---

## 🚀 CLI Quick Start

```bash
# 1. Scan codebase and index into SQLite AST cache
python run.py scan

# 2. Inspect a symbol with an ultra-dense Symbol Card
python run.py card CodebaseCartographer

# 3. Generate a PageRank repository map under 1,024 tokens
python run.py repomap --budget 1024

# 4. Pack a context-pruned prompt slice
python run.py pack calculate_blast_radius --budget 800

# 5. Calculate downstream blast radius
python run.py blast --file agent_lens/core/cartography.py --symbol calculate_blast_radius

# 6. Audit dynamic language risks
python run.py dynamic-risk calculate_blast_radius

# 7. Dry-run a patch without touching disk
python run.py diff-patch agent_lens/core/cartography.py --search "old_code" --replace "new_code"

# 8. Run tests in an isolated Git worktree
python run.py shadow-test agent_lens/core/cartography.py --patch /path/to/patch.py --cmd "pytest"

# 9. Check listening developer ports
python run.py ports

# 10. Terminate an orphaned dev port (requires confirmation)
python run.py kill-port 3000 --confirm

# 11. Launch Mission Control dashboard
python run.py serve --port 4141
```

---

## ⚠️ Limitations & Honest Scoping

AgentLens prioritizes honest architectural guarantees over absolute claims:

1. **Python Dynamic Leaks**: Static AST analysis cannot guarantee detection of `getattr()`, `hasattr()`, or string dispatch. AgentLens outputs `NO_STATIC_BREAKAGES` (safety score capped at 90/100) and explicitly warns about unverified dynamic occurrences. Ephemeral shadow worktree test runs remain the definitive proof of correctness.
2. **Tree-Sitter Syntax Outlines vs. Language Servers (LSP)**: For Go, Rust, and Java, Tree-sitter provides syntax-level definition extraction. Cross-module call resolution outside Python relies on symbol matching rather than compiler type inference.
3. **Token Reduction in Practice**: While Symbol Cards save ~97% of tokens on lookup, code rewriting tasks require implementation bodies. For editing, use `ContextPacker` (~90% savings) rather than symbol cards alone.
4. **Port Sentinel Safety**: Process termination is strictly opt-in with previewed PIDs and mandatory confirmation flags.

> For the review history of these edge cases and their engineering remediations, see [ADVERSARIAL_REVIEW.md](docs/ADVERSARIAL_REVIEW.md).

---

## 🧪 Test Suite

```bash
pytest tests/ -v
# 37 passed in 6.85s (100% pass rate)
```

The test suite covers CAS caching, AST parsing (Python, TSX, Go, Rust, Java), call graphs, blast radius, diff patching, dynamic risk detection, hallucination guards, JSON-RPC protocol compliance, shadow worktrees (including uncommitted change syncing), security path traversal, and port sentinel confirmation.

---

## 📄 License

MIT License. Designed and crafted for AI agents and human developers who build together.
