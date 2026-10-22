# 🔬 AgentLens

> **The Code Cartography Engine & Safe Testing Exoskeleton for AI Coding Assistants.**

[![CI](https://github.com/agent-lens/agent-lens/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-lens/agent-lens/actions)
[![MCP](https://img.shields.io/badge/MCP-JSON--RPC%202.0-blue.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Token Reduction](https://img.shields.io/badge/token_savings--97.6%25-brightgreen.svg)](#-empirical-benchmarks)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ⚡ The Problem

When autonomous AI coding agents (Google Antigravity, Claude, Cursor, Codex) operate in complex codebases, they suffer from three chronic failure modes:

1. **Context Starvation**: Reading entire 1,500-line files to find a single signature burns thousands of tokens and causes needle-in-a-haystack amnesia.
2. **Blast Radius Blindness**: Refactoring a function breaks distant callers and unrun test suites the agent never knew existed.
3. **Dirty Tree Syndrome**: Speculative patches and tests executed directly in your working directory corrupt uncommitted work, break dependencies, and leave behind orphaned dev servers.

**AgentLens equips AI agents with empirical AST cartography, calibrated blast-radius safety, and ephemeral git shadow worktrees.**

---

## ✨ Features at a Glance

| Feature | What It Does | Why It Matters |
|---|---|---|
| 🗺️ **PageRank Repo Maps** | Generates PageRank-weighted architectural trees under strict token limits. | Agents understand codebase structure in `<1,024 tokens` without reading every directory. |
| 📇 **Symbol Cards** | Extracts signatures, docstrings, exact line bounds, and inbound callers. | **97.6% token reduction** compared to reading full source files. |
| 💥 **Blast Radius Engine** | Transitive BFS caller graph linking modified symbols to downstream consumers. | Automatically identifies all affected caller files and relevant test suites. |
| ⚠️ **Dynamic Risk Audit** | Heuristic detector for Python `getattr`, `hasattr`, string dispatch, and duck typing. | Prevents false confidence from naive static tools; surfaces runtime caveats. |
| 👻 **Ghost Patch Dry-Runs** | Validates AST syntax, diff hunks, and caller contracts in-memory before disk writes. | Catches syntax errors and broken signatures before touching user files. |
| 🛡️ **Git Shadow Worktrees** | Executes tests in detached, ephemeral worktrees (`git worktree add --detach`). | Tests run against live uncommitted changes; **your active workspace stays 100% clean**. |
| 🧠 **Agent Flight Recorder** | SQLite-backed journal for hypotheses, architectural decisions, and tasks. | Preserves agent memory and intent across context window compaction and resets. |
| 🎛️ **Mission Control UI** | Modern web dashboard (port 4141) with interactive force-directed architecture graphs. | Human-in-the-loop visualization, port monitoring, and live telemetry. |

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/agent-lens/agent-lens.git
cd agent-lens
pip install -e .
```

*Requirements: Python 3.9+ (includes standard library AST parser; optional tree-sitter bindings for JS/TS/Go/Rust/Java).*

### 2. Connect to Your AI Assistant (MCP)

AgentLens runs natively as a Model Context Protocol (MCP) server over stdio.

Add to your assistant's MCP configuration (`~/.gemini/config/mcp_config.json`, `claude_desktop_config.json`, or Cursor):

```json
{
  "mcpServers": {
    "agent-lens": {
      "command": "agent-lens",
      "args": ["mcp", "--root", "."]
    }
  }
}
```

> 📖 **Agent Handbook**: For complete MCP schemas, prompt templates, and multi-agent delegation playbooks, see [**`AGENT_GUIDE.md`**](AGENT_GUIDE.md).

### 3. Launch Mission Control Dashboard

```bash
agent-lens serve --port 4141
```
Open **[http://localhost:4141](http://localhost:4141)** in your browser for the real-time architectural graph, blast radius simulator, and port sentinel.

---

## 💻 CLI Cheat Sheet

```bash
# 🗺️ Macro: Generate PageRank repository map under 1,024 tokens
agent-lens repomap --budget 1024

# 📇 Meso: Inspect a symbol (~50-token card instead of whole file)
agent-lens card CodebaseCartographer

# 💥 Blast: Check downstream callers and affected test suites
agent-lens blast --file agent_lens/core/cartography.py --symbol calculate_blast_radius

# ⚠️ Audit: Scan for runtime reflection and duck typing
agent-lens dynamic-risk calculate_blast_radius

# ✂️ Slice: Pack a token-budgeted prompt slice with stubbed siblings
agent-lens pack calculate_blast_radius --budget 1000

# 👻 Dry-Run: Test a search/replace patch in memory without writing to disk
agent-lens diff-patch agent_lens/core/parser.py --search "old_code" --replace "new_code"

# 🛡️ Shadow: Run tests in an isolated Git worktree (zero dirty files)
agent-lens shadow-test agent_lens/core/parser.py --patch fix.py --cmd "pytest tests/test_parser.py"

# 🚪 Sentinel: Safely inspect and terminate orphaned dev servers (requires --confirm)
agent-lens ports
agent-lens kill-port 3000 --confirm
```

---

## 📊 Empirical Benchmarks

*Measured on an active repository (61 files, 11,621 LOC, 598 indexed symbols):*

### 1. Token Economy
| Operation | Traditional Approach | AgentLens Compressed | Savings |
|---|---|---|---|
| **Symbol Inspection** | Read full file: 21,461 tokens | Symbol Card: 511 tokens | **-97.6% tokens** |
| **Code Editing** | Target + Callers: 30,486 tokens | Packed AST Slice: 3,004 tokens | **-90.1% tokens** |
| **AST Indexing** | Cold Parse: 310.10 ms | Warm CAS Cache: 25.75 ms | **12.0x faster** |

### 2. End-to-End Task Verification
| Task | Description | Baseline Read | AgentLens Read | Token Savings | Working Tree Status |
|---|---|---|---|---|---|
| **TASK-1** | Bug Fix: Add JSX/TSX support | 11,353 tokens | 1,842 tokens | **83.8%** | **CLEAN (0 dirty files)** |
| **TASK-2** | Refactor: Add traversal depth | 6,497 tokens | 2,453 tokens | **62.2%** | **CLEAN (0 dirty files)** |
| **TASK-3** | Patch: Update HTTP status route | 12,636 tokens | 1,369 tokens | **89.2%** | **CLEAN (0 dirty files)** |
| **TOTAL** | **3 Real Engineering Tasks** | **30,486 tokens** | **5,664 tokens** | **81.4%** | **100% UNTOUCHED** |

*Reproduce anytime via `python benchmarks/run_benchmark.py` and `python benchmarks/e2e_evaluation.py`.*

---

## 📚 Documentation & Architecture

- 🤖 [**AI Agent Guide (`AGENT_GUIDE.md`)**](AGENT_GUIDE.md) — Comprehensive 13-tool MCP reference, prompt engineering mental model, and surgical bug-fixing playbooks.
- 🛡️ [**Adversarial Review & Hardening (`docs/ADVERSARIAL_REVIEW.md`)**](docs/ADVERSARIAL_REVIEW.md) — Security disclosures, shell injection defenses, and worktree synchronization mechanics.

---

## 🧪 Testing

```bash
pytest tests/ -v
# 37 passed in 6.58s (100% pass rate)
```

AgentLens is continuously tested across **Ubuntu**, **macOS**, and **Windows** on Python 3.9, 3.10, 3.11, and 3.12.

---

## 📄 License

[MIT License](LICENSE) © 2026 AgentLens Contributors.
