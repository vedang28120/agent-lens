import os
import shutil
import subprocess
import time
import uuid
import shlex
import sys
from typing import Dict, List, Optional, Any
from .cartography import CodebaseCartographer
from .security import resolve_safe_path


class GitShadowSandbox:
    """
    Executes actual test suites against proposed patches in an ephemeral,
    isolated Git worktree without modifying the developer's working directory.
    """

    def __init__(self, cartographer: CodebaseCartographer):
        self.cart = cartographer
        self.worktree_base = os.path.join(self.cart.root_path, ".agentlens", "shadow_worktrees")

    def run_shadow_test(
        self,
        file_patches: Dict[str, str],
        test_command: str = "pytest",
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Applies file_patches in an ephemeral git worktree or temporary clone,
        executes test_command, captures results, and cleans up.
        
        Args:
            file_patches: Dict of relative_file_path -> proposed_new_content
            test_command: Test command to execute (e.g. "pytest tests/test_parser.py")
            timeout: Timeout in seconds
        """
        sandbox_id = f"shadow-{uuid.uuid4().hex[:8]}"
        sandbox_path = os.path.join(self.worktree_base, sandbox_id)
        os.makedirs(self.worktree_base, exist_ok=True)

        is_git_worktree = False
        start_time = time.time()

        try:
            # 1. Attempt to create ephemeral Git worktree from HEAD
            git_res = subprocess.run(
                ["git", "worktree", "add", "--detach", sandbox_path, "HEAD"],
                cwd=self.cart.root_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if git_res.returncode == 0:
                is_git_worktree = True
            else:
                # Fallback: file copy if not a git repo or worktree fails
                shutil.copytree(
                    self.cart.root_path,
                    sandbox_path,
                    ignore=shutil.ignore_patterns(".git", ".agentlens", "node_modules", "__pycache__", ".pytest_cache")
                )

            # 2. Apply proposed file patches
            patched_files = []
            for rel_file, content in file_patches.items():
                safe_target = resolve_safe_path(sandbox_path, rel_file)
                os.makedirs(os.path.dirname(safe_target), exist_ok=True)
                with open(safe_target, "w", encoding="utf-8") as f:
                    f.write(content)
                patched_files.append(rel_file)

            # 3. Security check: validate test command does not attempt raw shell invocation
            if isinstance(test_command, str):
                cmd_args = shlex.split(test_command, posix=True)
            else:
                cmd_args = list(test_command)

            if not cmd_args:
                return {
                    "success": False,
                    "exit_code": -1,
                    "duration_seconds": 0.0,
                    "sandbox_id": sandbox_id,
                    "patched_files": patched_files,
                    "test_command": test_command,
                    "stdout": "",
                    "stderr": "Security rejection: Empty test command.",
                }

            binary_name = os.path.basename(cmd_args[0]).lower()
            if binary_name in ["cmd.exe", "powershell.exe", "pwsh.exe", "bash.exe", "sh.exe", "cmd", "powershell", "pwsh", "bash", "sh"]:
                return {
                    "success": False,
                    "exit_code": -1,
                    "duration_seconds": 0.0,
                    "sandbox_id": sandbox_id,
                    "patched_files": patched_files,
                    "test_command": test_command,
                    "stdout": "",
                    "stderr": f"Security rejection: Direct invocation of shell binary '{binary_name}' is disallowed in shadow sandbox.",
                }

            run_res = subprocess.run(
                cmd_args,
                cwd=sandbox_path,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            duration = round(time.time() - start_time, 3)

            return {
                "success": run_res.returncode == 0,
                "exit_code": run_res.returncode,
                "duration_seconds": duration,
                "sandbox_id": sandbox_id,
                "patched_files": patched_files,
                "test_command": test_command,
                "stdout": run_res.stdout.strip()[-2000:],  # Tail output
                "stderr": run_res.stderr.strip()[-1000:],
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "exit_code": -1,
                "duration_seconds": round(time.time() - start_time, 3),
                "sandbox_id": sandbox_id,
                "patched_files": list(file_patches.keys()),
                "test_command": test_command,
                "stdout": "",
                "stderr": f"Test execution timed out after {timeout} seconds.",
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "duration_seconds": round(time.time() - start_time, 3),
                "sandbox_id": sandbox_id,
                "patched_files": list(file_patches.keys()),
                "test_command": test_command,
                "stdout": "",
                "stderr": f"Shadow sandbox error: {str(e)}",
            }
        finally:
            # 4. Rigorous Cleanup
            if is_git_worktree:
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", "--force", sandbox_path],
                        cwd=self.cart.root_path,
                        capture_output=True,
                        timeout=10,
                    )
                except Exception:
                    pass

            if os.path.exists(sandbox_path):
                try:
                    shutil.rmtree(sandbox_path, ignore_errors=True)
                except Exception:
                    pass
