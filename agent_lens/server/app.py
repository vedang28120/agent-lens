import http.server
import socketserver
import json
import os
import mimetypes
import time
import threading
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Any

from ..core.cartography import CodebaseCartographer
from ..core.memory import AgentMemory
from ..core.radar import ArchitectureRadar
from ..core.packer import ContextPacker
from ..core.sandbox import GhostPatchSandbox
from ..core.sentinel import PortSentinel
from ..core.guard import HallucinationGuard
from ..core.planner import RefactorPlanner
from ..core.watcher import CodebaseWatcher


class SSEBroadcaster:
    """Manages Server-Sent Events subscribers for real-time dashboard updates."""
    def __init__(self):
        self.clients: List[http.server.BaseHTTPRequestHandler] = []
        self.lock = threading.Lock()

    def register(self, handler):
        with self.lock:
            self.clients.append(handler)

    def unregister(self, handler):
        with self.lock:
            if handler in self.clients:
                self.clients.remove(handler)

    def broadcast(self, event_type: str, data: dict):
        payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
        with self.lock:
            dead_clients = []
            for client in self.clients:
                try:
                    client.wfile.write(payload)
                    client.wfile.flush()
                except Exception:
                    dead_clients.append(client)
            for dead in dead_clients:
                if dead in self.clients:
                    self.clients.remove(dead)


broadcaster = SSEBroadcaster()
recent_activities: List[Dict[str, Any]] = []


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
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. API: Server-Sent Events
        if path == "/api/events":
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            broadcaster.register(self)
            try:
                self.wfile.write(b": heartbeat\n\n")
                self.wfile.flush()
                while True:
                    time.sleep(15)
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
            except Exception:
                broadcaster.unregister(self)
            return

        # 2. API: Status & Metrics
        if path == "/api/status":
            self._send_json({
                "status": "online",
                "root_path": self.cartographer.root_path,
                "files_count": len(self.cartographer.file_results),
                "symbols_count": sum(len(v) for v in self.cartographer.symbol_index.values()),
                "memos_count": len(self.memory.get_all_memos()),
                "tasks_count": len(self.memory.get_tasks()),
                "hypotheses_count": len(self.memory.get_hypotheses()),
            })
            return

        # 3. API: Graph Export
        if path == "/api/graph":
            data = self.cartographer.get_graph_export()
            self._send_json(data)
            return

        # 4. API: Working Memory State
        if path == "/api/memory":
            self._send_json({
                "hypotheses": self.memory.get_hypotheses(),
                "decisions": self.memory.get_decisions(),
                "memos": self.memory.get_all_memos(),
                "tasks": self.memory.get_tasks(),
                "scratchpad": self.memory.get_scratchpad(),
                "summary": self.memory.get_compact_summary(),
            })
            return

        # 5. API: Architecture Radar
        if path == "/api/radar":
            radar = ArchitectureRadar(self.cartographer)
            self._send_json(radar.analyze())
            return

        # 6. API: Port Sentinel
        if path == "/api/ports":
            ports = PortSentinel.list_listening_ports()
            self._send_json(ports)
            return

        # 7. API: Recent File Activities
        if path == "/api/activity":
            self._send_json(recent_activities[-30:])
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

        # 10. Static Web Assets
        rel_req = path.lstrip("/")
        if not rel_req:
            rel_req = "index.html"

        file_on_disk = os.path.join(self.web_dir, rel_req)
        if os.path.exists(file_on_disk) and os.path.isfile(file_on_disk):
            mime_type, _ = mimetypes.guess_type(file_on_disk)
            try:
                with open(file_on_disk, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", mime_type or "text/plain")
                self.send_header("Content-Length", str(len(content)))
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

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self._send_error(400, f"Invalid JSON payload: {str(e)}")
            return

        if path == "/api/memory/hypo":
            action = payload.get("action", "add")
            if action == "add":
                hid = self.memory.add_hypothesis(
                    statement=payload.get("statement", ""),
                    status=payload.get("status", "exploring"),
                    evidence=payload.get("evidence", ""),
                )
                broadcaster.broadcast("memory_update", {"type": "hypothesis_added", "id": hid})
                self._send_json({"success": True, "id": hid})
            elif action == "update":
                self.memory.update_hypothesis(
                    hypothesis_id=payload.get("id"),
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
                )
                broadcaster.broadcast("memory_update", {"type": "task_added", "id": tid})
                self._send_json({"success": True, "id": tid})
            elif action == "update":
                self.memory.update_task(
                    task_id=payload.get("id"),
                    status=payload.get("status"),
                    notes=payload.get("notes"),
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
            content = payload.get("content", "")
            sandbox = GhostPatchSandbox(self.cartographer)
            verdict = sandbox.dry_run_patch(target_file, content)
            self._send_json(verdict)
            return

        elif path == "/api/verify":
            target_file = payload.get("file", "")
            content = payload.get("content")
            guard = HallucinationGuard(self.cartographer)
            res = guard.verify_file(target_file, content=content)
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
            res = PortSentinel.kill_port(port)
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
        recent_activities.append(activity)
        if len(recent_activities) > 50:
            recent_activities.pop(0)
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
