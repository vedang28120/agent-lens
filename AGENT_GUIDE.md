# 🤖 AgentLens: Complete Agent Handbook & Command Reference

> **The definitive operational manual for AI coding assistants (Google Antigravity, Claude, Cursor, Codex, Gemini) using AgentLens via the Model Context Protocol (MCP) or CLI.**

---

## 🧭 The Agent Mental Model

When working on a software codebase, standard tools (like `read_file`, `grep_search`, or modifying files directly) introduce severe penalties:

| Standard Action | Hidden Penalty | AgentLens Replacement | Benefit |
|---|---|---|---|
| Reading entire 1,500-line files to find a signature | Burns 5,000+ tokens; dilutes context | `lens_get_symbol_card` | **~50 tokens (-97.6% savings)** |
| Reading whole files + callers to edit a function | Consumes 20,000+ tokens; exceeds prompt budgets | `lens_pack_context` | **Syntax-pruned slice (-90.1% savings)** |
| Editing code directly without knowing callers | Unforeseen breakages and test failures | `lens_blast_radius` | **Full caller tree & test suites surfaced** |
| Relying solely on static analysis in Python | Blind to `getattr()`, reflection, and duck typing | `lens_audit_dynamic_risk` | **Identifies runtime reflection & caveats** |
| Writing speculative code directly to disk | Corrupts working tree; breaks user's uncommitted work | `lens_ghost_patch_diff` | **In-memory AST syntax & caller verification** |
| Running tests in the user's workspace | Leaves dirty git tree; risks merge conflicts | `lens_shadow_test_sandbox` | **Isolated Git worktree (100% clean disk)** |

---

## 🛠️ The 7-Stage Agent Operational Loop

Follow this sequence for any coding task:

```
1. ORIENT (Macro)       ──► lens_get_repo_map(token_budget=1024)
2. INSPECT (Meso)       ──► lens_get_symbol_card(symbol="...", file_hint="...")
3. ASSESS RISK          ──► lens_blast_radius(file="...") & lens_audit_dynamic_risk(symbol="...")
4. SLICE CONTEXT (Micro)──► lens_pack_context(query="...", token_budget=1200)
5. DRY-RUN IN-MEMORY    ──► lens_ghost_patch_diff(file="...", search_block="...", replace_block="...")
6. SHADOW TEST          ──► lens_shadow_test_sandbox(file_patches={...}, test_command="pytest ...")
7. RECORD DECISION      ──► lens_manage_memory(action="add_decision", ...)
```

---

## 📚 Exhaustive Tool & Command Reference

---

### 1. `lens_get_symbol_card` / `python run.py card`

**Purpose**: Fetches a token-dense summary of a function, class, or method (parameters, line bounds, docstring, callers). Replaces reading the full file.

#### MCP Request
```json
{
  "name": "lens_get_symbol_card",
  "arguments": {
    "symbol": "detect_language",
    "file_hint": "agent_lens/core/parser.py",
    "format": "compact"
  }
}
```

#### CLI Equivalent
```bash
python run.py card detect_language --file agent_lens/core/parser.py
```

#### Output Example
```markdown
### `detect_language` (`function`)
- **File**: `agent_lens/core/parser.py` (lines 35-52, 18 LOC)
- **Signature**: `def detect_language(file_path: str) -> str:`
- **Docstring**: Maps file extension to tree-sitter or native language grammar.
- **Known Callers**: `agent_lens/core/cartography.py:scan()`, `tests/test_parser.py`
```

#### When to Use
- You need to know the parameters, return type, or line bounds of a function.
- You want to see who calls a function before changing its signature.
- **Never read the whole file if a symbol card answers your question.**

---

### 2. `lens_get_repo_map` / `python run.py repomap`

**Purpose**: Produces a compact, PageRank-weighted structural map of the entire codebase under a strict token budget.

#### MCP Request
```json
{
  "name": "lens_get_repo_map",
  "arguments": {
    "token_budget": 1024
  }
}
```

#### CLI Equivalent
```bash
python run.py repomap --budget 1024
```

#### Output Example
```
# REPOSITORY STRUCTURE MAP (PageRank Centrality)

agent_lens/
  cli.py
    def main()
  core/
    cartography.py
      class CodebaseCartographer
        def scan(self)
        def calculate_blast_radius(self, target_file, symbol_name)
        def get_symbol_card(self, symbol_name, file_hint)
    parser.py
      def detect_language(file_path)
      class PythonASTVisitor
    shadow.py
      class GitShadowSandbox
        def run_shadow_test(self, file_patches, test_command, timeout)

[RepoMap: 18/56 files, 42 symbols, ~480 tokens]
```

#### When to Use
- Starting work on an unfamiliar project or task.
- Identifying architectural "god nodes" and key entry points without running recursive `ls` or directory walks.

---

### 3. `lens_pack_context` / `python run.py pack`

**Purpose**: Extracts the exact code slice needed for an edit. Preserves the target function implementation, imports, and enclosing classes while pruning sibling function bodies to stubs.

#### MCP Request
```json
{
  "name": "lens_pack_context",
  "arguments": {
    "query": "calculate_blast_radius",
    "token_budget": 1200
  }
}
```

#### CLI Equivalent
```bash
python run.py pack calculate_blast_radius --budget 1200
```

#### Output Example
```python
# === AGENTLENS CONTEXT SLICE: calculate_blast_radius ===
# File: agent_lens/core/cartography.py (140 LOC -> 38 lines sliced)

import os
from typing import Dict, List, Optional, Any
import networkx as nx

class CodebaseCartographer:
    def __init__(self, root_path: str):
        ...  # Sibling implementation pruned for token economy

    def scan(self) -> Dict[str, Any]:
        ...  # Sibling implementation pruned for token economy

    def calculate_blast_radius(self, target_file: str, symbol_name: Optional[str] = None) -> Dict[str, Any]:
        """Calculates transitive reverse dependencies and associated tests."""
        # FULL IMPLEMENTATION PRESERVED HERE
        norm_file = target_file.replace("\\", "/")
        impacted_files = set()
        ...
        return {
            "target_file": norm_file,
            "risk_level": risk,
            "impacted_files": sorted(list(impacted_files)),
            "related_tests": related_tests,
        }
```

#### When to Use
- You are ready to edit a function or class and need to inspect its full body without wasting tokens on unedited sibling functions in the same file.

---

### 4. `lens_blast_radius` / `python run.py blast`

**Purpose**: Calculates the transitive downstream blast radius of modifying a file or symbol via reverse Breadth-First Search (BFS) and auto-discovers relevant test files.

#### MCP Request
```json
{
  "name": "lens_blast_radius",
  "arguments": {
    "file": "agent_lens/core/cartography.py",
    "symbol": "calculate_blast_radius"
  }
}
```

#### CLI Equivalent
```bash
python run.py blast --file agent_lens/core/cartography.py --symbol calculate_blast_radius
```

#### Output Example
```json
{
  "target_file": "agent_lens/core/cartography.py",
  "target_symbol": "calculate_blast_radius",
  "risk_level": "HIGH",
  "in_degree": 6,
  "impacted_files": [
    "agent_lens/cli.py",
    "agent_lens/core/delegation.py",
    "agent_lens/core/planner.py",
    "agent_lens/mcp/server.py",
    "agent_lens/server/app.py",
    "tests/test_cartography.py"
  ],
  "impacted_symbols": [
    "cli.main",
    "DelegationContractGenerator.generate_briefing",
    "RefactorPlanner.plan_refactor",
    "AgentLensMCPServer.handle_call_tool"
  ],
  "related_tests": [
    "tests/test_cartography.py"
  ]
}
```

#### How to Act on This Output
- If `risk_level` is `HIGH` or `CRITICAL`, you MUST check if your proposed change changes the function's signature or return type.
- Note `related_tests` and run them using `lens_shadow_test_sandbox` before finalizing the task.

---

### 5. `lens_audit_dynamic_risk` / `python run.py dynamic-risk`

**Purpose**: Audits the repository for dynamic occurrences of a symbol (`getattr`, `hasattr`, dictionary registry lookups, duck typing) that static AST call graphs cannot guarantee.

#### MCP Request
```json
{
  "name": "lens_audit_dynamic_risk",
  "arguments": {
    "symbol": "calculate_blast_radius"
  }
}
```

#### CLI Equivalent
```bash
python run.py dynamic-risk calculate_blast_radius
```

#### Output Example
```json
{
  "target_symbol": "calculate_blast_radius",
  "dynamic_risk_level": "MODERATE",
  "total_unverified_references": 2,
  "findings": [
    {
      "file": "agent_lens/server/app.py",
      "line": 202,
      "type": "DUCK_TYPED_ATTRIBUTE_ACCESS",
      "detail": "Attribute `.calculate_blast_radius` accessed on dynamically injected instance",
      "snippet": "blast = self.cartographer.calculate_blast_radius(f_target)",
      "severity": "HIGH"
    }
  ],
  "caveats": [
    "Static AST call graphs cannot guarantee detection of runtime reflection or duck typing.",
    "Review findings above before assuming zero downstream impact."
  ]
}
```

#### How to Act on This Output
- If `findings` contains `DYNAMIC_REFLECTION` (`getattr(obj, 'sym')`) or `REGISTRY_DISPATCH_LOOKUP` (`handlers['sym']`), rename or refactor with caution.
- Always verify your change dynamically in a shadow worktree.

---

### 6. `lens_ghost_patch_diff` / `python run.py diff-patch`

**Purpose**: Performs an in-memory AST dry run of a proposed localized search/replace block or unified diff hunk. Validates syntax and checks if caller signatures break without touching disk.

#### MCP Request (Search & Replace Mode)
```json
{
  "name": "lens_ghost_patch_diff",
  "arguments": {
    "file": "agent_lens/core/parser.py",
    "search_block": "ext == \".js\":\n        return \"javascript\"",
    "replace_block": "ext in [\".js\", \".jsx\"]:\n        return \"javascript\""
  }
}
```

#### MCP Request (Unified Diff Mode)
```json
{
  "name": "lens_ghost_patch_diff",
  "arguments": {
    "file": "agent_lens/core/parser.py",
    "diff_patch": "--- a/agent_lens/core/parser.py\n+++ b/agent_lens/core/parser.py\n@@ -38,2 +38,2 @@\n-    if ext == \".js\":\n+    if ext in [\".js\", \".jsx\"]:\n"
  }
}
```

#### CLI Equivalent
```bash
python run.py diff-patch agent_lens/core/parser.py --search "ext == '.js'" --replace "ext in ['.js', '.jsx']"
```

#### Output Example
```json
{
  "verdict": "SAFE",
  "safety_score": 90,
  "confidence_assessment": "NO_STATIC_BREAKAGES",
  "file": "agent_lens/core/parser.py",
  "breakages": [],
  "warnings": [],
  "caveats": [
    "Static check only; runtime reflection and duck typing are unverified.",
    "Run tests via lens_shadow_test_sandbox for definitive proof."
  ],
  "net_lines": 0
}
```

#### How to Act on This Output
- If `verdict` is `REJECTED`, check `error` and `breakages`. Common reasons: syntax error in replacement code, or `search_block` not found in original file.
- If `verdict` is `SIGNATURE_DRIFT`, you modified parameters or deleted a symbol that existing callers still rely on. Review `breakages` to update callers.
- If `verdict` is `SAFE`, proceed to shadow testing.

---

### 7. `lens_shadow_test_sandbox` / `python run.py shadow-test`

**Purpose**: Executes your test suite against proposed file patches in a detached, ephemeral Git worktree (`git worktree add --detach`). Uncommitted changes in the user's working tree are automatically synced into the sandbox. **The user's working tree is never modified.**

#### MCP Request
```json
{
  "name": "lens_shadow_test_sandbox",
  "arguments": {
    "file_patches": {
      "agent_lens/core/parser.py": "<full_replacement_content_here>"
    },
    "test_command": "pytest tests/test_parser.py -k test_javascript_parsing",
    "timeout": 30
  }
}
```

#### CLI Equivalent
```bash
python run.py shadow-test agent_lens/core/parser.py --patch /tmp/patched_parser.py --cmd "pytest tests/test_parser.py"
```

#### Output Example
```json
{
  "success": true,
  "exit_code": 0,
  "duration_seconds": 1.42,
  "sandbox_id": "shadow-3f8a91b2",
  "patched_files": ["agent_lens/core/parser.py"],
  "test_command": "pytest tests/test_parser.py -k test_javascript_parsing",
  "stdout": "tests/test_parser.py::test_javascript_parsing PASSED [100%]\n\n1 passed in 0.35s",
  "stderr": ""
}
```

#### How to Act on This Output
- If `success` is `true`: The patch is mathematically and behaviorally verified. You may now apply it safely to the real working tree with complete confidence.
- If `success` is `false`: Inspect `stdout` and `stderr` for test failure tracebacks. Fix the patch and retry within the sandbox. The user's repo remains 100% clean.

---

### 8. `lens_verify_hallucinations` / `python run.py guard`

**Purpose**: Verifies that every module, class, and function imported in a file actually exists in the workspace or standard library, catching phantom AI hallucinations.

#### MCP Request
```json
{
  "name": "lens_verify_hallucinations",
  "arguments": {
    "file": "agent_lens/cli.py"
  }
}
```

#### CLI Equivalent
```bash
python run.py guard agent_lens/cli.py
```

#### Output Example
```json
{
  "file": "agent_lens/cli.py",
  "is_clean": true,
  "flagged_count": 0,
  "hallucinations": []
}
```

*(If a hallucination was detected):*
```json
{
  "file": "agent_lens/cli.py",
  "is_clean": false,
  "flagged_count": 1,
  "hallucinations": [
    {
      "symbol": "calculate_blast_radii",
      "type": "METHOD_HALLUCINATION",
      "suggested_match": "calculate_blast_radius",
      "distance": 1
    }
  ]
}
```

---

### 9. `lens_plan_refactor` / `python run.py plan`

**Purpose**: Generates a dependency-ordered, topologically sorted refactoring execution plan (updating definitions before callers, followed by test suites).

#### MCP Request
```json
{
  "name": "lens_plan_refactor",
  "arguments": {
    "file": "agent_lens/core/cartography.py",
    "symbol": "calculate_blast_radius",
    "objective": "Add max_depth parameter"
  }
}
```

#### CLI Equivalent
```bash
python run.py plan agent_lens/core/cartography.py --symbol calculate_blast_radius --objective "Add max_depth parameter"
```

---

### 10. `lens_generate_delegation_briefing` / `python run.py delegate`

**Purpose**: Produces an authoritative, token-compact work briefing contract (<600 tokens) for delegating a subtask to a subagent. Prevents subagents from wandering outside target files.

#### MCP Request
```json
{
  "name": "lens_generate_delegation_briefing",
  "arguments": {
    "objective": "Add JSX and TSX extension support to parser",
    "target_files": ["agent_lens/core/parser.py"],
    "target_symbols": ["detect_language"],
    "test_command": "pytest tests/test_parser.py"
  }
}
```

#### CLI Equivalent
```bash
python run.py delegate --objective "Add JSX support" --files agent_lens/core/parser.py --cmd "pytest tests/test_parser.py"
```

---

### 11. `lens_manage_memory` / `python run.py memory`

**Purpose**: Manages persistent working memory stored in `.agentlens/memory.db`. Preserves reasoning across context window compaction, resets, and subagent handoffs.

#### Available Actions:
- `add_hypothesis`: Records a hypothesis to test.
- `update_hypothesis`: Sets status (`exploring`, `confirmed`, `refuted`) and evidence.
- `add_decision`: Records an architectural choice, rationale, and trade-offs.
- `add_task` / `update_task`: Manages actionable checklists.
- `set_memo` / `get_memo`: Key-value store for facts, ports, or config values.
- `update_scratchpad` / `get_scratchpad`: Shared markdown buffer between human and agent.
- `get_summary`: Returns a compact markdown briefing (<300 tokens) to restore context.

#### MCP Request Examples
```json
// Add an architectural decision
{
  "name": "lens_manage_memory",
  "arguments": {
    "action": "add_decision",
    "title": "Use detached Git worktrees for sandbox testing",
    "rationale": "Keeps the user's working directory 100% clean and allows parallel test execution",
    "tradeoffs": "Requires git repository; fallback to directory copy if non-git"
  }
}

// Track a hypothesis
{
  "name": "lens_manage_memory",
  "arguments": {
    "action": "add_hypothesis",
    "statement": "Test failure caused by missing JSX extension in detect_language",
    "status": "confirmed",
    "evidence": "Shadow test passed once .jsx was added"
  }
}
```

---

### 12. `lens_kill_port` / `python run.py kill-port`

**Purpose**: Scans and safely terminates orphaned developer server processes (Vite, Next.js, Flask) listening on common ports.

#### MCP Request (Dry-Run / Preview)
```json
{
  "name": "lens_kill_port",
  "arguments": {
    "port": 3000,
    "confirm": false
  }
}
```
*Response*: Previews process name, PID, and warns that `confirm: true` is required.

#### MCP Request (Confirmed Termination)
```json
{
  "name": "lens_kill_port",
  "arguments": {
    "port": 3000,
    "confirm": true
  }
}
```

#### CLI Equivalent
```bash
python run.py kill-port 3000 --confirm
```

---

## 🎯 Real-World Agent Playbooks

### Playbook A: Fixing a Bug in a Function
1. **Identify**: Find where the bug is using `lens_get_symbol_card(symbol="...")`.
2. **Blast Radius**: Check callers using `lens_blast_radius(file="...", symbol="...")`.
3. **Slice Code**: Retrieve the pruned code slice using `lens_pack_context(query="...", token_budget=1000)`.
4. **Draft & Dry-Run**: Write the replacement block and test in-memory using `lens_ghost_patch_diff(file="...", search_block="...", replace_block="...")`.
5. **Shadow Test**: Run the test suite in isolation using `lens_shadow_test_sandbox(file_patches={...}, test_command="pytest ...")`.
6. **Apply to Disk**: Once `shadow_test` returns `success: true`, write the change to disk using standard write/edit tools.

### Playbook B: Context Restoration After Window Truncation
1. If your conversation history was truncated or compacted, call:
   `lens_manage_memory(action="get_summary")`.
2. This returns all active hypotheses, pending tasks, confirmed architectural decisions, and scratchpad notes in under 300 tokens.
3. Resume work seamlessly without asking the user to repeat requirements.
