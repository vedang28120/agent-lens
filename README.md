# 🔬 AgentLens (AI Agent Exoskeleton & Mission Control)

> **Built by an AI Agent, for AI Agents & Humans Pair Programming.**

When an AI coding assistant lands in a codebase, it faces real-world challenges:
1. **Context Window Starvation**: Reading whole files to locate symbol signatures and calls wastes 80–95% of context window tokens.
2. **Blast Radius Blindness**: Editing a function without knowing downstream callers or test suites causes regressions.
3. **Session Amnesia**: Long conversations lose hypotheses, falsified dead-ends, and architectural decisions when context compacts.
4. **Pre-Flight Guesswork**: Syntax errors, unclosed brackets, or merge conflict markers break the build before code even runs.
5. **Ghost Regressions**: Editing a function signature without knowing who breaks before touching disk.
6. **Port & Daemon Conflicts**: Orphaned background servers blocking ports (`EADDRINUSE: 3000`).

**AgentLens** solves these exact pain points with zero bloat and standard library speed.

---

## 🚀 Key Capabilities

### 1. 🗂️ Ultra-Dense Symbol Cards (92% Token Reduction)
`python run.py card <symbol>` extracts exact line bounds, signature, docstring, parameters, callers, and blast risk in <100 tokens.

### 2. ✂️ Smart Token-Budgeted Context Packer
`python run.py pack <query> --budget 800`
Slices files with AST precision: keeps imports, classes, and target function implementations, while **pruning away sibling bodies** (`... # [pruned 40 lines]`). Fits perfectly within a requested token budget.

### 3. 👻 Ghost Patch Sandbox (Virtual AST Dry-Run)
`python run.py ghost-patch --file <path> --content "<proposed_code>"`
Simulates code modifications in an in-memory shadow AST *without touching disk*. Detects syntax errors, removed symbols, parameter changes, and specific downstream caller breakages.

### 4. 📡 Architecture Radar & Antipattern Detector
`python run.py radar`
Uses NetworkX graph algorithms to detect:
- Circular import dependency chains (`python run.py cycles`)
- Highly coupled "God Nodes" (PageRank & in-degree centrality)
- Candidate dead / orphan symbols (`python run.py deadcode`)
- Overall Architectural Health Score (0–100)

### 5. 🛡️ Port Sentinel & Zombie Process Killer
`python run.py ports`
Monitors active listening dev ports (3000, 4141, 5000, 8000, etc.) and safely terminates orphaned listeners with `python run.py kill-port <port>`.

### 6. 🧠 Persistent Working Memory & Flight Recorder (SQLite)
`python run.py memory summary`
Tracks hypotheses (`exploring`, `confirmed`, `refuted`), architectural decisions, task DAGs, and memos. Produces a 60-token recovery brief that survives context window compactions.

### 7. 🎛️ Mission Control Web Cockpit (http://localhost:4141)
A real-time cyberpunk developer cockpit:
- Live Server-Sent Events (SSE) telemetry
- Interactive force-directed physics graph with blast radius highlighting
- Architecture health gauge and circular import detector
- Interactive Context Packer & Ghost Patch Dry-Run UI
- Active Port Sentinel with 1-click process termination
- Collaborative Human-Agent scratchpad

---

## ⚡ Quick Start

```bash
# 1. Scan the codebase
python run.py scan

# 2. Get a token-compact Symbol Card
python run.py card CodeParser

# 3. Smart Context Packing for LLM Prompting
python run.py pack calculate_blast_radius --budget 600

# 4. Check Architecture Health & Circular Imports
python run.py radar
python run.py cycles

# 5. Virtual AST Dry-Run on Proposed Code
python run.py ghost-patch --file agent_lens/core/cartography.py --content "..."

# 6. Check Active Dev Ports
python run.py ports

# 7. Launch Mission Control Dashboard (http://localhost:4141)
python run.py serve --port 4141
```

---

## 🧪 Testing

```bash
python -m pytest tests -v
# 13 passed in 0.35s
```


