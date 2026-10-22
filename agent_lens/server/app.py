import http.server
import socketserver
import json
import os
import mimetypes
import time
import queue
import threading
from collections import deque
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any, Optional

from ..core.cartography import CodebaseCartographer
from ..core.memory import AgentMemory
from ..core.radar import ArchitectureRadar
from ..core.packer import ContextPacker
from ..core.sandbox import GhostPatchSandbox
from ..core.sentinel import PortSentinel
from ..core.guard import HallucinationGuard
from ..core.planner import RefactorPlanner
from ..core.watcher import CodebaseWatcher
from ..core.report import ArchitectureReporter
from ..core.security import resolve_safe_path
from ..core.repomap import RepoMapGenerator
from ..core.dynamic_risk import DynamicRiskDetector


class SSEBroadcaster:
    """Non-blocking Server-Sent Events broadcaster with per-client queues."""
    def __init__(self):
        self.client_queues: Dict[Any, queue.Queue] = {}
        self.lock = threading.Lock()

    def register(self, client_id) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=100)
        with self.lock:
            self.client_queues[client_id] = q
        return q

    def unregister(self, client_id):
        with self.lock:
            self.client_queues.pop(client_id, None)

    def broadcast(self, event_type: str, data: dict):
        payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
        with self.lock:
            for client_id, q in list(self.client_queues.items()):
                try:
                    q.put_nowait(payload)
                except queue.Full:
                    # Drop payload if consumer is stalled to avoid blocking broadcaster
                    pass


class ThreadSafeActivityBuffer:
    def __init__(self, maxlen: int = 50):
        self.buffer = deque(maxlen=maxlen)
        self.lock = threading.Lock()

    def append(self, activity: dict):
        with self.lock:
            self.buffer.append(activity)

    def get_recent(self, count: int = 30) -> list:
        with self.lock:
            return list(self.buffer)[-count:]


broadcaster = SSEBroadcaster()
activity_buffer = ThreadSafeActivityBuffer(maxlen=50)


class MissionControlHandler(http.server.SimpleHTTPRequestHandler):
    cartographer: CodebaseCartographer = None
    memory: AgentMemory = None
    web_dir: str = ""

    def log_message(self, format, *args):
        # Quiet standard HTTP access logs to keep terminal clean
        pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AgentLens-Token")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. Server-Sent Events Stream (Non-blocking queue driven)
        if path == "/api/events":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            client_q = broadcaster.register(self)
            try:
                self.wfile.write(b": heartbeat\n\n")
                self.wfile.flush()
                while True:
                    try:
                        msg = client_q.get(timeout=15.0)
                        self.wfile.write(msg)
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            finally:
                broadcaster.unregister(self)
            return

        # 2. API: System Status & Metrics
        if path == "/api/status":
            symbols_count = sum(len(v) for v in self.cartographer.symbol_index.values())
            res = {
                "status": "online",
                "root_path": self.cartographer.root_path,
                "files_count": len(self.cartographer.file_results),
                "symbols_count": symbols_count,
                "version": "1.1.0",
                "timestamp": time.time(),
            }
            self._send_json(res)
            return

        # 3. API: Architecture Graph
        if path == "/api/graph":
            graph_data = self.cartographer.get_graph_export()
            self._send_json(graph_data)
            return

        # 4. API: Architecture Radar Antipatterns
        if path == "/api/radar":
            radar = ArchitectureRadar(self.cartographer)
            analysis = radar.analyze()
            self._send_json(analysis)
            return

        # 5. API: Listening Developer Ports
        if path == "/api/ports":
            ports = PortSentinel.list_listening_ports()
            self._send_json({"ports": ports})
            return

        # 6. API: Recent File System & Agent Activities
        if path == "/api/activity":
            self._send_json({"activities": activity_buffer.get_recent(30)})
            return

        # 7. API: Agent Working Memory
        if path == "/api/memory":
            res = {
                "hypotheses": self.memory.get_hypotheses(),
                "decisions": self.memory.get_decisions(),
                "tasks": self.memory.get_tasks(),
                "memos": self.memory.get_all_memos(),
                "scratchpad": self.memory.get_scratchpad(),
                "compact_summary": self.memory.get_compact_summary(),
            }
            self._send_json(res)
            return

        # 8. API: Symbol Card
        if path == "/api/card":
            sym = query.get("symbol", [""])[0]
            f_hint = query.get("file", [None])[0]
            if not sym:
                self._send_error(400, "Missing symbol parameter")
                return
            card = self.cartographer.get_symbol_card(sym, file_hint=f_hint)
            if not card:
                self._send_error(404, f"Symbol '{sym}' not found")
                return
            self._send_json(card)
            return

        # 9. API: Blast Radius
        if path == "/api/blast":
            f_target = query.get("file", [""])[0]
            sym = query.get("symbol", [None])[0]
            if not f_target:
                self._send_error(400, "Missing file parameter")
                return
            blast = self.cartographer.calculate_blast_radius(f_target, symbol_name=sym)
            self._send_json(blast)
            return

        # 10. API: Full Architecture Report
        if path == "/api/report":
            reporter = ArchitectureReporter(self.cartographer, memory=self.memory)
            self._send_json({"report": reporter.generate_report()})
            return

        # 11. API: PageRank RepoMap
        if path == "/api/repomap":
            budget = int(query.get("budget", [1024])[0])
            generator = RepoMapGenerator(self.cartographer)
            res = generator.generate_repo_map(token_budget=budget)
            self._send_json(res)
            return

        # 12. API: Dynamic Risk Audit
        if path == "/api/dynamic-risk":
            sym = query.get("symbol", [""])[0]
            f_hint = query.get("file", [None])[0]
            if not sym:
                self._send_error(400, "Missing symbol parameter")
                return
            detector = DynamicRiskDetector(self.cartographer)
            res = detector.audit_symbol_dynamic_risk(sym, target_file=f_hint)
            self._send_json(res)
            return

        # 13. Static Web Assets (Strictly hardened against path traversal)
        rel_req = path.lstrip("/")
        if not rel_req:
            rel_req = "index.html"

        try:
            file_on_disk = resolve_safe_path(self.web_dir, rel_req)
        except (ValueError, PermissionError) as e:
            self._send_error(403, f"Forbidden: {str(e)}")
            return

        if os.path.exists(file_on_disk) and os.path.isfile(file_on_disk):
            mime_type, _ = mimetypes.guess_type(file_on_disk)
            try:
                with open(file_on_disk, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", mime_type or "text/plain")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                self._send_error(500, f"Error reading static file: {str(e)}")
                return

        # Fallback 404
        self._send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._send_error(400, "Invalid JSON payload")
            return

        if path == "/api/memory/hypo":
            action = payload.get("action", "add")
            if action == "add":
                hid = self.memory.add_hypothesis(
                    statement=payload.get("statement", ""),
                    status=payload.get("status", "exploring"),
                    evidence=payload.get("evidence", ""),
                    agent_id=payload.get("agent_id", "default"),
                )
                broadcaster.broadcast("memory_update", {"type": "hypothesis_added", "id": hid})
                self._send_json({"success": True, "id": hid})
            elif action == "update":
                self.memory.update_hypothesis(
                    hypo_id=payload.get("id"),
                    status=payload.get("status"),
                    evidence=payload.get("evidence"),
                )
                broadcaster.broadcast("memory_update", {"type": "hypothesis_updated", "id": payload.get("id")})
                self._send_json({"success": True})
            return

        elif path == "/api/memory/task":
            action = payload.get("action", "add")
            if action == "add":
                tid = self.memory.add_task(
                    title=payload.get("title", ""),
                    status=payload.get("status", "pending"),
                    priority=payload.get("priority", 1),
                    notes=payload.get("notes", ""),
                    agent_id=payload.get("agent_id", "default"),
                )
                broadcaster.broadcast("memory_update", {"type": "task_added", "id": tid})
                self._send_json({"success": True, "id": tid})
            elif action == "update":
                self.memory.update_task(
                    task_id=payload.get("id"),
                    status=payload.get("status"),
                    notes=payload.get("notes"),
                    priority=payload.get("priority"),
                )
                broadcaster.broadcast("memory_update", {"type": "task_updated", "id": payload.get("id")})
                self._send_json({"success": True})
            return

        elif path == "/api/memory/scratchpad":
            content = payload.get("content", "")
            by = payload.get("updated_by", "human")
            self.memory.update_scratchpad(content, updated_by=by)
            broadcaster.broadcast("memory_update", {"type": "scratchpad_updated", "by": by})
            self._send_json({"success": True})
            return

        elif path == "/api/scan":
            metrics = self.cartographer.scan()
            broadcaster.broadcast("scan_complete", metrics)
            self._send_json(metrics)
            return

        elif path == "/api/pack":
            query = payload.get("query", "")
            budget = int(payload.get("budget", 1200))
            packer = ContextPacker(self.cartographer)
            res = packer.pack(query, token_budget=budget)
            self._send_json(res)
            return

        elif path == "/api/ghost-patch":
            target_file = payload.get("file", "")
            content = payload.get("content")
            search_block = payload.get("search_block")
            replace_block = payload.get("replace_block")
            diff_patch = payload.get("diff_patch")

            sandbox = GhostPatchSandbox(self.cartographer)
            if search_block is not None or diff_patch is not None:
                verdict = sandbox.dry_run_patch_diff(
                    target_file,
                    search_block=search_block,
                    replace_block=replace_block,
                    diff_patch=diff_patch,
                )
            else:
                verdict = sandbox.dry_run_patch(target_file, content or "")
            self._send_json(verdict)
            return

        elif path == "/api/verify":
            target_file = payload.get("file", "")
            content = payload.get("content")
            guard = HallucinationGuard(self.cartographer)
            res = guard.verify_patch_hallucinations(target_file, content=content)
            self._send_json(res)
            return

        elif path == "/api/plan":
            target_file = payload.get("file", "")
            target_sym = payload.get("symbol")
            obj = payload.get("objective", "Refactor")
            planner = RefactorPlanner(self.cartographer)
            plan = planner.plan_refactor(target_file, target_symbol=target_sym, objective=obj)
            self._send_json(plan)
            return

        elif path == "/api/ports/kill":
            port = int(payload.get("port", 0))
            confirm = bool(payload.get("confirm", False))
            force = bool(payload.get("force_non_dev", False))
            res = PortSentinel.kill_port(port, force_non_dev=force, confirm=confirm)
            broadcaster.broadcast("ports_update", res)
            self._send_json(res)
            return

        self._send_error(404, "Unknown POST endpoint")

    def _send_json(self, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, code: int, message: str):
        body = json.dumps({"error": message, "code": code}).encode("utf-8")
        self.send_response(code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def start_mission_control_server(port: int = 4141, root_dir: str = "."):
    cart = CodebaseCartographer(root_dir)
    print(f"[*] AgentLens: Scanning '{os.path.abspath(root_dir)}'...")
    metrics = cart.scan()
    print(f"[+] Scan complete: {metrics['files_scanned']} files, {metrics['symbols_indexed']} symbols.")

    mem = AgentMemory()

    web_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

    MissionControlHandler.cartographer = cart
    MissionControlHandler.memory = mem
    MissionControlHandler.web_dir = web_path

    # Start live background file watcher
    def on_file_event(rel_path: str, event_type: str):
        activity = {
            "file": rel_path,
            "type": event_type,
            "timestamp": time.time(),
        }
        activity_buffer.append(activity)
        broadcaster.broadcast("file_activity", activity)

    watcher = CodebaseWatcher(cart, on_change_callback=on_file_event)
    watcher.start(interval=1.0)
    print(f"[*] Hot-Reload File Watcher active on '{os.path.abspath(root_dir)}'.")

    server = ThreadedHTTPServer(("127.0.0.1", port), MissionControlHandler)
    print(f"[*] AgentLens Mission Control running at: http://localhost:{port}")
    print(f"[*] Live telemetry & working memory active. Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down Mission Control server...")
        watcher.stop()
        server.server_close()
