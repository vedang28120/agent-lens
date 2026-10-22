import os
import sqlite3
import json
import time
from typing import List, Dict, Optional, Any


class AgentMemory:
    """Persistent SQLite-backed working memory and flight recorder for AI agents."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to .agentlens/memory.db in the working directory
            lens_dir = os.path.abspath(".agentlens")
            os.makedirs(lens_dir, exist_ok=True)
            db_path = os.path.join(lens_dir, "memory.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Hypotheses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hypotheses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    statement TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'exploring',  -- exploring, confirmed, refuted
                    evidence TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

            # Architectural Decisions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    tradeoffs TEXT DEFAULT '',
                    created_at REAL NOT NULL
                )
            """)

            # Memos / Key-Value Facts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at REAL NOT NULL
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, done, blocked
                    priority INTEGER DEFAULT 1,
                    notes TEXT DEFAULT '',
                    updated_at REAL NOT NULL
                )
            """)

            # Collaborative Shared Scratchpad table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scratchpad (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    content TEXT NOT NULL,
                    updated_by TEXT DEFAULT 'agent',
                    updated_at REAL NOT NULL
                )
            """)

            # Default scratchpad row
            cursor.execute("""
                INSERT OR IGNORE INTO scratchpad (id, content, updated_by, updated_at)
                VALUES (1, '# AgentLens Shared Scratchpad\n\nUse this board for persistent notes between human and agent.', 'system', ?)
            """, (time.time(),))

            conn.commit()

    # --- Hypotheses API ---

    def add_hypothesis(self, statement: str, status: str = "exploring", evidence: str = "") -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO hypotheses (statement, status, evidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (statement, status, evidence, now, now),
            )
            conn.commit()
            return cursor.lastrowid

    def update_hypothesis(self, hypothesis_id: int, status: Optional[str] = None, evidence: Optional[str] = None):
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if status:
                updates.append("status = ?")
                params.append(status)
            if evidence is not None:
                updates.append("evidence = ?")
                params.append(evidence)
            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(hypothesis_id)
                query = f"UPDATE hypotheses SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, tuple(params))
                conn.commit()

    def get_hypotheses(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hypotheses ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Decisions API ---

    def add_decision(self, title: str, rationale: str, tradeoffs: str = "") -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO decisions (title, rationale, tradeoffs, created_at) VALUES (?, ?, ?, ?)",
                (title, rationale, tradeoffs, now),
            )
            conn.commit()
            return cursor.lastrowid

    def get_decisions(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM decisions ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Memos API ---

    def set_memo(self, key: str, value: Any, category: str = "general"):
        now = time.time()
        val_str = json.dumps(value) if not isinstance(value, str) else value
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memos (key, value, category, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, category = excluded.category, updated_at = excluded.updated_at
            """, (key, val_str, category, now))
            conn.commit()

    def get_memo(self, key: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memos WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def get_all_memos(self) -> Dict[str, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM memos ORDER BY key ASC")
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # --- Tasks API ---

    def add_task(self, title: str, status: str = "pending", priority: int = 1, notes: str = "") -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (title, status, priority, notes, updated_at) VALUES (?, ?, ?, ?, ?)",
                (title, status, priority, notes, now),
            )
            conn.commit()
            return cursor.lastrowid

    def update_task(self, task_id: int, status: Optional[str] = None, notes: Optional[str] = None):
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if status:
                updates.append("status = ?")
                params.append(status)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if updates:
                updates.append("updated_at = ?")
                params.append(now)
                params.append(task_id)
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, tuple(params))
                conn.commit()

    def get_tasks(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks ORDER BY priority DESC, id ASC")
            return [dict(row) for row in cursor.fetchall()]

    # --- Scratchpad API ---

    def get_scratchpad(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, updated_by, updated_at FROM scratchpad WHERE id = 1")
            row = cursor.fetchone()
            return dict(row) if row else {"content": "", "updated_by": "unknown", "updated_at": 0}

    def update_scratchpad(self, content: str, updated_by: str = "agent"):
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scratchpad SET content = ?, updated_by = ?, updated_at = ? WHERE id = 1",
                (content, updated_by, now),
            )
            conn.commit()

    # --- Token-Optimized Agent Briefing ---

    def get_compact_summary(self) -> str:
        """Generates an ultra-dense, token-minimalist summary of current session memory."""
        tasks = self.get_tasks()
        hypotheses = self.get_hypotheses()
        decisions = self.get_decisions()
        memos = self.get_all_memos()

        lines = ["### [AGENT WORKING MEMORY RECOVERY]"]

        # Tasks
        active_tasks = [t for t in tasks if t["status"] in ["in_progress", "pending"]]
        done_tasks = [t for t in tasks if t["status"] == "done"]
        lines.append(f"**Tasks**: {len(done_tasks)} completed, {len(active_tasks)} pending")
        for t in active_tasks[:4]:
            lines.append(f"  - [{t['status'].upper()}] #{t['id']}: {t['title']}")

        # Hypotheses
        if hypotheses:
            lines.append(f"**Hypotheses ({len(hypotheses)})**:")
            for h in hypotheses[:3]:
                status_icon = "✓" if h["status"] == "confirmed" else ("✗" if h["status"] == "refuted" else "?")
                lines.append(f"  - [{status_icon} {h['status']}] {h['statement']}")

        # Decisions
        if decisions:
            lines.append(f"**Key Decisions ({len(decisions)})**:")
            for d in decisions[:2]:
                lines.append(f"  - `{d['title']}`: {d['rationale']}")

        # Memos
        if memos:
            memo_str = ", ".join([f"{k}={v}" for k, v in list(memos.items())[:6]])
            lines.append(f"**Memos**: {memo_str}")

        return "\n".join(lines)
