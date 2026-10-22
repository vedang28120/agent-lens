# 🔬 AgentLens: Codebase Cartography & Safe Patch Testing for AI Agents

> **An empirical toolkit for token-budgeted code navigation, blast radius auditing, and isolated shadow-worktree test execution.**

When an AI coding assistant operates in a codebase, it faces real operational bottlenecks:
1. **Token Starvation**: Reading full files to extract signatures or call hierarchies consumes thousands of tokens per task.
2. **Blast Radius Blindness**: Modifying a symbol without knowing downstream callers or affected test files leads to regressions.
3. **Dirty Git Trees**: Running speculative patches directly in the user's working tree risks unstaged file corruption and merge conflicts.
4. **Dynamic Language Leaks**: Python static analysis cannot guarantee safety against `getattr`, `**kwargs`, or duck typing.

**AgentLens** addresses these challenges with transparent, token-budgeted tools built for both CLI and Model Context Protocol (MCP) integrations.

---

## 🛠️ How It Works Internally

### 1. Unified AST & Tree-Sitter Parsing
- **Python**: Uses Python's native `ast` module (`ast.NodeVisitor`) to extract classes, functions, decorators, line bounds, and call hierarchies.
- **Polyglot Grammars**: Integrates official `tree-sitter` grammars (`tree-sitter-javascript`, `tree-sitter-typescript`, `tree-sitter-go`, `tree-sitter-rust`, `tree-sitter-java`) to parse syntax trees without language runtimes installed.
- **Content-Addressable Cache (CAS)**: Hashes file content (`SHA-256`) and mtime into `.agentlens/ast_cache.db` (SQLite with WAL mode). Subsequent scans skip unchanged files, reducing re-index latency by over 11x.

### 2. Directed Call Graph & PageRank Cartography
- Builds a directed dependency graph (`networkx.DiGraph`) where nodes are files and edges represent static imports and symbol calls.
- Computes PageRank centrality to identify architectural god nodes and generate token-budgeted repository maps (<1,024 tokens) sorted by architectural importance.
- Calculates transitive blast radius via breadth-first search (BFS) over incoming caller edges, ranking downstream risk into `CRITICAL`, `HIGH`, `MODERATE`, and `LOW`.

### 3. Ephemeral Git Shadow-Worktrees
- Rather than running test suites in the user's working tree, `GitShadowSandbox` creates a detached, isolated worktree (`git worktree add --detach <tempdir> HEAD`).
- Proposed patches are written strictly inside the temporary worktree.
- The test runner (e.g. `pytest`) executes in isolation. Once tests finish, the worktree is pruned (`git worktree remove --force <tempdir>`). The developer's working directory is never touched.

---

## ⚠️ Limitations & Real-World Realities

We believe in honest scoping over marketing claims:

1. **Python Dynamic Leaks**:
   Static AST analysis cannot resolve `getattr()`, `hasattr()`, dynamic string dispatch, or unimported duck typing. AgentLens never issues an unchecked "SAFE" verdict; it outputs `NO_STATIC_BREAKAGES` (capped at 90/100) and explicitly flags unverified dynamic occurrences. Runtime tests in a shadow worktree remain the only definitive proof of correctness.

2. **Tree-Sitter Syntax Outlines vs. Language Servers (LSP)**:
   For Go, Rust, and Java, Tree-sitter provides syntax-level definition extraction. However, AgentLens does **not** run a compiler or Language Server Protocol (LSP) daemon; cross-module call resolution outside Python relies on symbol matching rather than compiler type inference.

3. **Token Reduction in Practice**:
   While Symbol Cards reduce token consumption by ~97% for symbol lookup, an agent that needs to rewrite a function body cannot rely on a 50-token card alone. For code modification tasks, AgentLens provides **ContextPacker**, which preserves the target function's full implementation and imports while pruning sibling function bodies, yielding a realistic ~90% token reduction per edit.

4. **Port Sentinel Safety**:
   Process termination is strictly opt-in. The `kill-port` command defaults to dry-run mode and requires an explicit `--confirm` flag (or `confirm=True` in MCP) to prevent accidental service interruption.

---

## 📊 Empirical Benchmarks

Measured on the active 56-file repository (8,887 LOC, 535 indexed symbols):

### 1. Cartography & Cache Latency
- **Cold Scan** (Parsing all ASTs from scratch): **260.99 ms**
- **Warm Scan** (CAS-AST SQLite cache): **22.31 ms** (11.7x speedup)

### 2. Token Economy
- **Lookup Phase** (Symbol Card vs. Reading Full Target File):
  - Whole file read: 21,377 tokens
  - AgentLens Symbol Cards: 506 tokens (**-97.6% token reduction**)
- **Edit Phase** (Full Target + Caller/Test Files vs. Packed AST Slice):
  - Standard agent read: 30,402 tokens
  - Packed AST Slice (full target code + imports + sibling stubs): 3,003 tokens (**-90.1% token reduction**)

---

## 🚀 Quick Start

```bash
# 1. Scan codebase and populate AST cache
python run.py scan

# 2. Get an ultra-dense Symbol Card (<100 tokens)
python run.py card detect_language

# 3. Generate Aider-style PageRank repo map (<1024 tokens)
python run.py repomap --budget 1024

# 4. Pack token-budgeted prompt slice with full target implementation
python run.py pack calculate_blast_radius --budget 800

# 5. Audit dynamic dispatch & duck-typing caveats
python run.py dynamic-risk calculate_blast_radius

# 6. Calculate blast radius and downstream callers
python run.py blast --file agent_lens/core/cartography.py --symbol calculate_blast_radius

# 7. Check listening dev ports (safe read-only)
python run.py ports

# 8. Terminate rogue process (requires explicit confirmation)
python run.py kill-port 3000 --confirm

# 9. Launch Mission Control Web UI
python run.py serve --port 4141
```

---

## 🔌 Model Context Protocol (MCP) Server

AgentLens exposes its capabilities as standard JSON-RPC 2.0 tools for coding agents:

- `lens_get_symbol_card`: Returns dense signature, line bounds, and callers.
- `lens_get_repo_map`: Returns token-budgeted PageRank structural tree.
- `lens_pack_context`: Returns syntax-valid prompt slice with target implementation.
- `lens_blast_radius`: Calculates downstream files and related test suites.
- `lens_audit_dynamic_risk`: Scans for reflection, getattr, and duck typing risks.
- `lens_ghost_patch`: Simulates AST replacement in-memory before disk writes.
- `lens_shadow_test_sandbox`: Executes test suite in an isolated Git worktree.
- `lens_kill_port`: Port terminator with mandatory `confirm=True` guard.

---

## 🧪 Test Suite

```bash
pytest tests/ -v
# 35 passed in 6.44s
```
