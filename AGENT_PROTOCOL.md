# 🤖 AgentLens Autonomous Agent Protocol

This guide defines the standardized operational protocol for AI coding agents connecting to AgentLens via the Model Context Protocol (MCP) or CLI.

Follow this sequence to minimize token waste, prevent regressions, and verify patches safely:

```
1. MACRO ORIENTATION       ──► lens_get_repo_map(budget=1024)
2. MESO INSPECTION         ──► lens_get_symbol_card(symbol="...")
3. RISK AUDITING           ──► lens_blast_radius(file="...") & lens_audit_dynamic_risk(symbol="...")
4. CONTEXT SLICING         ──► lens_pack_context(query="...", budget=1000)
5. IN-MEMORY VALIDATION    ──► lens_ghost_patch_diff(file="...", search="...", replace="...")
6. SHADOW VERIFICATION     ──► lens_shadow_test_sandbox(file_patches={...}, test_command="pytest ...")
7. FLIGHT RECORDING        ──► lens_manage_memory(action="add_decision", ...)
```

---

## 🛠️ Step-by-Step Tool Protocol

### Step 1: Macro Orientation (Where is everything?)
- **Tool**: `lens_get_repo_map`
- **When**: Starting work on a new task or unfamiliar repository.
- **Arguments**: `{"token_budget": 1024}`
- **Why**: PageRank centrality ranks the most critical architecture nodes and files in a compact tree under 1,024 tokens. Avoids blindly reading `ls` or random files.

### Step 2: Meso Inspection (How does this symbol connect?)
- **Tool**: `lens_get_symbol_card`
- **When**: Locating a specific function, class, or method to inspect or modify.
- **Arguments**: `{"symbol": "<symbol_name>", "file_hint": "<optional_path>"}`
- **Why**: Provides docstrings, parameter signatures, exact line bounds, and inbound callers in ~50 tokens (97.6% savings vs. reading the full file).

### Step 3: Risk & Blast Radius Assessment
- **Tools**:
  - `lens_blast_radius`: `{"file": "<target_file>", "symbol": "<symbol_name>"}`
  - `lens_audit_dynamic_risk`: `{"symbol": "<symbol_name>"}`
- **When**: Before making any modification to a symbol or file.
- **Why**:
  - `lens_blast_radius` reveals all downstream caller files and auto-discovers relevant test files.
  - `lens_audit_dynamic_risk` flags runtime reflection (`getattr`, `hasattr`), dynamic string dispatch, or duck typing that static AST analysis cannot guarantee.

### Step 4: Micro Context Slicing (Targeted Code Editing)
- **Tool**: `lens_pack_context`
- **When**: Ready to write code.
- **Arguments**: `{"query": "<symbol_or_module_name>", "token_budget": 1200}`
- **Why**: Produces a syntax-valid slice containing the complete implementation of the target function/class, necessary imports, and stubbed sibling bodies (90.1% token savings).

### Step 5: In-Memory Ghost Patch Validation
- **Tool**: `lens_ghost_patch_diff` (or `lens_ghost_patch` for full file)
- **When**: You have generated the replacement code block.
- **Arguments**:
  - Search & replace: `{"file": "path/file.py", "search_block": "old_code", "replace_block": "new_code"}`
  - Or unified diff: `{"file": "path/file.py", "diff_patch": "--- a/...\n+++ b/...\n@@..."}`
- **Why**: Validates syntax in AST, verifies surrounding code preservation, and checks if any downstream caller signatures were broken before writing to disk.

### Step 6: Ephemeral Shadow Test Verification
- **Tool**: `lens_shadow_test_sandbox`
- **When**: Before reporting task completion to the user.
- **Arguments**:
  - `file_patches`: `{"path/to/file.py": "<full_patched_code>"}`
  - `test_command`: `"pytest tests/test_target.py"` (or `npm test`, `cargo test`)
  - `timeout`: `30`
- **Why**: Runs in an isolated, detached Git worktree with live uncommitted changes synced. Zero risk of dirtying the developer's working directory.

### Step 7: Flight Recording & Memory
- **Tool**: `lens_manage_memory`
- **When**: Concluding an architectural milestone or resolving a debugging hypothesis.
- **Arguments**:
  - Record decision: `{"action": "add_decision", "title": "...", "rationale": "...", "tradeoffs": "..."}`
  - Track hypothesis: `{"action": "add_hypothesis", "statement": "...", "status": "confirmed", "evidence": "..."}`
- **Why**: Stores state in `.agentlens/memory.db`, ensuring context is preserved across context window compaction, resets, or subagent handoffs.
