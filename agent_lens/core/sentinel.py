import subprocess
import re
import os
import sys
from typing import Dict, List, Optional, Any, Set


class PortSentinel:
    """Monitors listening developer ports and safely terminates rogue/zombie processes with strict guards."""

    COMMON_DEV_PORTS: Set[int] = {
        3000, 3001, 4141, 4200, 5000, 5173, 5174, 8000, 8080, 8081, 8888, 9000
    }

    # Critical OS system processes that must NEVER be terminated under any circumstances
    CRITICAL_PROCESS_NAMES: Set[str] = {
        "system", "system idle process", "init", "systemd", "svchost.exe",
        "lsass.exe", "csrss.exe", "smss.exe", "services.exe", "winlogon.exe",
        "explorer.exe", "kernel_task", "launchd"
    }

    @classmethod
    def list_listening_ports(cls) -> List[Dict[str, Any]]:
        """Scans system for active listening TCP ports and resolves process names."""
        results = []
        try:
            if sys.platform == "win32":
                res = subprocess.run(
                    ["netstat", "-ano", "-p", "tcp"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=5,
                )
                output = res.stdout
                # Match lines: TCP  0.0.0.0:4141  0.0.0.0:0  LISTENING  1234
                pattern = re.compile(r"TCP\s+(?:\[::\]|0\.0\.0\.0|127\.0\.0\.1):(\d+)\s+.*?\s+LISTENING\s+(\d+)", re.IGNORECASE)
                pid_map: Dict[int, str] = {}

                for match in pattern.finditer(output):
                    port = int(match.group(1))
                    pid = int(match.group(2))

                    if pid not in pid_map:
                        pid_map[pid] = cls._resolve_process_name(pid)

                    proc_name = pid_map[pid]
                    is_dev = port in cls.COMMON_DEV_PORTS

                    results.append({
                        "port": port,
                        "pid": pid,
                        "process_name": proc_name,
                        "is_dev_port": is_dev,
                        "status": "LISTENING",
                    })

                # Deduplicate by port
                seen_ports = set()
                deduped = []
                for r in sorted(results, key=lambda x: x["port"]):
                    if r["port"] not in seen_ports:
                        seen_ports.add(r["port"])
                        deduped.append(r)
                return deduped

            else:
                # POSIX fallback
                res = subprocess.run(
                    ["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                lines = res.stdout.strip().split("\n")
                if len(lines) > 1:
                    for line in lines[1:]:
                        parts = line.split()
                        if len(parts) >= 9:
                            proc_name = parts[0]
                            pid = int(parts[1]) if parts[1].isdigit() else 0
                            address_part = parts[8]
                            port_match = re.search(r":(\d+)$", address_part)
                            if port_match and pid > 0:
                                port = int(port_match.group(1))
                                results.append({
                                    "port": port,
                                    "pid": pid,
                                    "process_name": proc_name,
                                    "is_dev_port": port in cls.COMMON_DEV_PORTS,
                                    "status": "LISTENING",
                                })
                return results

        except Exception as e:
            return [{"error": f"Failed to inspect ports: {str(e)}"}]

    @classmethod
    def _resolve_process_name(cls, pid: int) -> str:
        if pid <= 4:
            return "System"
        try:
            res = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=2,
            )
            line = res.stdout.strip()
            if line and line.startswith('"'):
                # Extract first CSV column
                return line.split('","')[0].replace('"', '')
            return f"PID {pid}"
        except Exception:
            return f"PID {pid}"

    @classmethod
    def kill_port(cls, port: int, force_non_dev: bool = False, confirm: bool = False) -> Dict[str, Any]:
        """Safely finds process on given port and terminates it with comprehensive security validations."""
        # 1. Port boundary check
        if not (1 <= port <= 65535):
            return {"success": False, "message": f"Invalid port number: {port}"}

        # 2. Privileged system ports (0-1023)
        if port < 1024 and not force_non_dev:
            return {"success": False, "message": f"Refusing to kill privileged system port {port}."}

        # 3. Locate target process
        ports = cls.list_listening_ports()
        target = next((p for p in ports if p.get("port") == port), None)
        if not target:
            return {"success": False, "message": f"No active process found listening on port {port}."}

        pid = target.get("pid")
        proc_name = str(target.get("process_name", "")).strip()
        proc_name_lower = proc_name.lower()

        # 4. Strict PID Sanity Checks
        if not isinstance(pid, int) or pid <= 4:
            return {"success": False, "message": f"Refusing to terminate protected system PID {pid}."}

        # 5. Prevent Self-Termination / Parent Termination
        current_pid = os.getpid()
        parent_pid = os.getppid() if hasattr(os, "getppid") else None

        if pid == current_pid:
            return {"success": False, "message": f"Self-termination prevented: Port {port} is occupied by this AgentLens process (PID {pid})."}

        if parent_pid and pid == parent_pid:
            return {"success": False, "message": f"Parent-termination prevented: Port {port} is occupied by parent agent process (PID {pid})."}

        # 6. Critical OS service blacklist check
        if any(crit in proc_name_lower for crit in cls.CRITICAL_PROCESS_NAMES):
            return {"success": False, "message": f"Security block: Cannot terminate critical OS process '{proc_name}' (PID {pid})."}

        # 7. Dev port policy enforcement
        if port not in cls.COMMON_DEV_PORTS and not force_non_dev:
            return {"success": False, "message": f"Port {port} is not in COMMON_DEV_PORTS. Pass force_non_dev=True to override."}

        # 8. Explicit Confirmation Guard (Opt-in Safety)
        if not confirm:
            return {
                "success": False,
                "requires_confirmation": True,
                "message": (
                    f"Action requires explicit confirmation. Process '{proc_name}' (PID {pid}) "
                    f"is listening on port {port}. Pass confirm=True (or --confirm in CLI) to terminate."
                ),
                "port": port,
                "pid": pid,
                "process": proc_name,
            }

        try:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True, timeout=5)
            else:
                subprocess.run(["kill", "-9", str(pid)], check=True, timeout=5)

            return {
                "success": True,
                "message": f"Successfully killed {proc_name} (PID {pid}) on port {port}.",
                "port": port,
                "pid": pid,
                "process": proc_name,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to kill process {pid}: {str(e)}"}
