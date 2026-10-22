import subprocess
import re
import os
import sys
from typing import Dict, List, Optional, Any


class PortSentinel:
    """Monitors listening developer ports and terminates rogue/zombie processes."""

    COMMON_DEV_PORTS = {
        3000, 3001, 4141, 4200, 5000, 5173, 5174, 8000, 8080, 8081, 8888, 9000
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
                    is_dev = port in cls.COMMON_DEV_PORTS or "python" in proc_name.lower() or "node" in proc_name.lower()

                    results.append({
                        "port": port,
                        "pid": pid,
                        "process_name": proc_name,
                        "is_dev_port": is_dev,
                    })
            else:
                # Unix fallback (lsof or ss)
                res = subprocess.run(
                    ["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in res.stdout.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 9:
                        proc_name = parts[0]
                        pid = int(parts[1]) if parts[1].isdigit() else 0
                        addr = parts[8]
                        port_match = re.search(r":(\d+)$", addr)
                        port = int(port_match.group(1)) if port_match else 0
                        if port:
                            results.append({
                                "port": port,
                                "pid": pid,
                                "process_name": proc_name,
                                "is_dev_port": port in cls.COMMON_DEV_PORTS,
                            })

            # Sort: dev ports first, then by port number
            results.sort(key=lambda x: (not x["is_dev_port"], x["port"]))
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
    def kill_port(cls, port: int) -> Dict[str, Any]:
        """Finds process on given port and terminates it."""
        ports = cls.list_listening_ports()
        target = next((p for p in ports if p.get("port") == port), None)
        if not target:
            return {"success": False, "message": f"No active process found listening on port {port}."}

        pid = target["pid"]
        proc_name = target["process_name"]

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
