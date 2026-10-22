# 🛡️ AgentLens Adversarial Review & Self-Correction Log

During development, the AgentLens architecture was evaluated through multi-pass adversarial reviews to discover edge cases, security risks, and protocol vulnerabilities before deployment.

This document records the vulnerabilities identified and the engineering remediations applied to resolve them.

---

## 🔬 Remediated Vulnerabilities & Improvements

### 1. JSON-RPC 2.0 Protocol Compliance & Exception Isolation
- **Finding**: Standard MCP clients (Claude, Antigravity, Cursor) send periodic `ping` frames and `notifications/initialized` notifications. Unhandled tool exceptions previously risked dropping the stdio communication pipe.
- **Remediation**:
  - Implemented standard `ping` response (`{"result": {}}`).
  - Added silent consumption of `notifications/*`.
  - Added standard JSON-RPC error codes `-32601` (*Method not found*) and `-32700` (*Parse error*).
  - Wrapped `handle_call_tool` in a per-tool exception shield that translates runtime errors into `{isError: True}` payloads, guaranteeing the stdio connection never terminates unexpectedly.

### 2. Process Safety in Ephemeral Sandboxes
- **Finding**: Speculative test execution using `shell=True` created a potential command injection vector if agent prompts contained unsanitized commands or malicious shell chaining operators (`;`, `&&`, `|`).
- **Remediation**:
  - Completely stripped `shell=True` in favor of `shell=False`.
  - Arguments are safely tokenized via `shlex.split`.
  - Normalizes Windows backslashes (`\`) to forward slashes (`/`) prior to splitting to prevent path stripping.
  - Added strict blacklisting of direct interactive shell binary invocations (`cmd.exe`, `powershell.exe`, `pwsh.exe`, `bash.exe`, `sh.exe`).

### 3. Detached Git Worktree Syncing with Uncommitted Working Trees
- **Finding**: `git worktree add --detach` creates a worktree from `HEAD`. If the developer had uncommitted modifications or new untracked files in their active working tree, tests would run against stale `HEAD` rather than `WorkingTree + proposed_patch`.
- **Remediation**:
  - Added automatic working-tree diff capture (`git diff HEAD`) and patch application (`git apply`) inside the ephemeral worktree.
  - Synchronizes new untracked files (`git status --porcelain`).
  - Guarantees tests run against the true live state of the project.

### 4. Diff Patch Hunk Reconstruction
- **Finding**: Dry-running multi-hunk unified diffs naively previously risked stripping surrounding unedited file content.
- **Remediation**:
  - Re-engineered `dry_run_patch_diff` with a unified diff hunk parser that reconstructs `(old_hunk, new_hunk)` blocks.
  - Matches targets against original content with line-ending normalization (CRLF vs. LF).
  - Rejects cleanly on hunk mismatch without modifying or truncating untouched code.

### 5. False Positive Reduction on Common Symbol Names
- **Finding**: Dynamic risk auditing for common symbol names (e.g. `get`, `run`, `items`) generated false positives on generic dictionary or object lookups (`dict.get()`).
- **Remediation**:
  - Expanded `COMMON_NOISY_SYMBOLS` to encompass standard library and built-in object methods.
  - Suppressed generic attribute duck-typing alerts for common names unless explicit dynamic reflection (`getattr`, dictionary registry lookups) is detected.

### 6. Opt-In Port Termination with Two-Phase Confirmation
- **Finding**: Automatically terminating listening processes risks killing active developer servers or background tasks without user consent.
- **Remediation**:
  - Made port killing strictly opt-in.
  - Defaults to dry-run mode previewing the process name, PID, and port.
  - Requires explicit `--confirm` (CLI) or `confirm=True` (MCP).
