import os
import sqlite3
import json
import time
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Generator


class AgentMemory:
    """
    Persistent, thread-safe, SQLite WAL-backed working memory and flight recorder
    for AI agents and multi-agent swarms.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to .agentlens/memory.db in the working directory
            lens_dir = os.path.abspath(".agentlens")
            os.makedirs(lens_dir, exist_ok=True)
            db_path = os.path.join(lens_dir, "memory.db")

        self.db_path = db_path
        self._init_wal()
        self._init_db()

    def _init_wal(self):
        """Configures Write-Ahead Logging (WAL) and busy timeouts for high-throughput concurrency."""
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Thread-safe connection generator that guarantees connection closure
        and auto-retries on transient database locks.
        """
        retries = 4
        backoff = 0.05
        conn = None

        while retries > 0:
            try:
                conn = sqlite3.connect(self.db_path, timeout=5.0)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA busy_timeout = 5000;")
                break
            except sqlite3.OperationalError:
                retries -= 1
                if retries == 0:
                    raise
                time.sleep(backoff)
                backoff *= 2

        try:
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

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
                    agent_id TEXT DEFAULT 'default',
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
                    agent_id TEXT DEFAULT 'default',
                    created_at REAL NOT NULL
                )
            """)

            # Structured Tasks table with multi-agent hierarchy support
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',  -- pending, in_progress, done, blocked
                    priority INTEGER DEFAULT 1,             -- 1: Normal, 2: High, 3: Critical
                    parent_task_id INTEGER DEFAULT NULL,
                    agent_id TEXT DEFAULT 'default',
                    notes TEXT DEFAULT '',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

            # Key-Value Memos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    agent_id TEXT DEFAULT 'default',
                    updated_at REAL NOT NULL
                )
            """)

            # Scratchpad table (Single active working markdown block)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scratchpad (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    content TEXT NOT NULL,
                    updated_by TEXT DEFAULT 'agent',
                    updated_at REAL NOT NULL
                )
            """)

            # Ensure single scratchpad row
            cursor.execute("""
                INSERT OR IGNORE INTO scratchpad (id, content, updated_by, updated_at)
                VALUES (1, '# Agent Scratchpad\n- Goal: Understand codebase\n- Status: Initialized', 'system', ?)
            """, (time.time(),))

            # Resilient column migrations for existing databases
            for col_sql in [
                "ALTER TABLE hypotheses ADD COLUMN agent_id TEXT DEFAULT 'default'",
                "ALTER TABLE decisions ADD COLUMN agent_id TEXT DEFAULT 'default'",
                "ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER DEFAULT NULL",
                "ALTER TABLE tasks ADD COLUMN agent_id TEXT DEFAULT 'default'",
                "ALTER TABLE memos ADD COLUMN agent_id TEXT DEFAULT 'default'",
            ]:
                try:
                    cursor.execute(col_sql)
                except sqlite3.OperationalError:
                    pass

            conn.commit()

    # --- Hypotheses API ---

    def add_hypothesis(self, statement: str, status: str = "exploring", evidence: str = "", agent_id: str = "default") -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO hypotheses (statement, status, evidence, agent_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (statement, status, evidence, agent_id, now, now),
            )
            conn.commit()
            return cursor.lastrowid

    def update_hypothesis(self, hypo_id: int, status: Optional[str] = None, evidence: Optional[str] = None):
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["updated_at = ?"]
            params: List[Any] = [now]
            if status:
                updates.append("status = ?")
                params.append(status)
            if evidence is not None:
                updates.append("evidence = ?")
                params.append(evidence)
            params.append(hypo_id)

            sql = f"UPDATE hypotheses SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()

    def get_hypotheses(self, status: Optional[str] = None, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cursor.execute(f"SELECT * FROM hypotheses {where} ORDER BY created_at ASC", params)
            return [dict(r) for r in cursor.fetchall()]

    # --- Architectural Decisions API ---

    def add_decision(self, title: str, rationale: str, tradeoffs: str = "", agent_id: str = "default") -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO decisions (title, rationale, tradeoffs, agent_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, rationale, tradeoffs, agent_id, now),
            )
            conn.commit()
            return cursor.lastrowid

    def get_decisions(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if agent_id:
                cursor.execute("SELECT * FROM decisions WHERE agent_id = ? ORDER BY created_at ASC", (agent_id,))
            else:
                cursor.execute("SELECT * FROM decisions ORDER BY created_at ASC")
            return [dict(r) for r in cursor.fetchall()]

    # --- Structured Tasks API ---

    def add_task(
        self,
        title: str,
        status: str = "pending",
        priority: int = 1,
        notes: str = "",
        agent_id: str = "default",
        parent_id: Optional[int] = None
    ) -> int:
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO tasks (title, status, priority, parent_task_id, agent_id, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, status, priority, parent_id, agent_id, notes, now, now),
            )
            conn.commit()
            return cursor.lastrowid

    def update_task(
        self,
        task_id: int,
        status: Optional[str] = None,
        notes: Optional[str] = None,
        priority: Optional[int] = None
    ):
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            updates = ["updated_at = ?"]
            params: List[Any] = [now]
            if status:
                updates.append("status = ?")
                params.append(status)
            if notes is not None:
                updates.append("notes = ?")
                params.append(notes)
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            params.append(task_id)

            sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, params)
            conn.commit()

    def get_tasks(
        self,
        status: Optional[str] = None,
        agent_id: Optional[str] = None,
        parent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []
            if status:
                conditions.append("status = ?")
                params.append(status)
            if agent_id:
                conditions.append("agent_id = ?")
                params.append(agent_id)
            if parent_id is not None:
                conditions.append("parent_task_id = ?")
                params.append(parent_id)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            cursor.execute(f"SELECT * FROM tasks {where} ORDER BY priority DESC, id ASC", params)
            return [dict(r) for r in cursor.fetchall()]

    # --- Memos API ---

    def set_memo(self, key: str, value: str, agent_id: str = "default"):
        now = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memos (key, value, agent_id, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, agent_id = excluded.agent_id, updated_at = excluded.updated_at
                """,
                (key, value, agent_id, now),
            )
            conn.commit()

    def get_memo(self, key: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memos WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def get_all_memos(self, agent_id: Optional[str] = None) -> Dict[str, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if agent_id:
                cursor.execute("SELECT key, value FROM memos WHERE agent_id = ? ORDER BY key ASC", (agent_id,))
            else:
                cursor.execute("SELECT key, value FROM memos ORDER BY key ASC")
            return {r["key"]: r["value"] for r in cursor.fetchall()}

    # --- Scratchpad API ---

    def get_scratchpad(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, updated_by, updated_at FROM scratchpad WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {"content": "", "updated_by": "system", "updated_at": time.time()}

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

    def get_compact_summary(self, agent_id: Optional[str] = None) -> str:
        """Generates an ultra-dense, token-minimalist summary of current session memory."""
        tasks = self.get_tasks(agent_id=agent_id)
        hypotheses = self.get_hypotheses(agent_id=agent_id)
        decisions = self.get_decisions(agent_id=agent_id)
        memos = self.get_all_memos(agent_id=agent_id)

        lines = ["### [AGENT WORKING MEMORY RECOVERY]"]

        # Tasks
        active_tasks = [t for t in tasks if t["status"] in ["in_progress", "pending"]]
        done_tasks = [t for t in tasks if t["status"] == "done"]
        lines.append(f"**Tasks**: {len(done_tasks)} completed, {len(active_tasks)} pending")
        for t in active_tasks[:5]:
            prio_badge = " [CRITICAL]" if t["priority"] == 3 else (" [HIGH]" if t["priority"] == 2 else "")
            lines.append(f"  - [{t['status'].upper()}]{prio_badge} #{t['id']}: {t['title']}")

        # Hypotheses
        if hypotheses:
            lines.append(f"**Hypotheses ({len(hypotheses)})**:")
            for h in hypotheses[:3]:
                status_icon = "✓" if h["status"] == "confirmed" else ("✗" if h["status"] == "refuted" else "?")
                lines.append(f"  - [{status_icon} {h['status']}] {h['statement']}")

        # Decisions
        if decisions:
            lines.append(f"**Key Decisions ({len(decisions)})**:")
            for d in decisions[:3]:
                lines.append(f"  - `{d['title']}`: {d['rationale']}")

        # Memos
        if memos:
            memo_str = ", ".join([f"{k}={v}" for k, v in list(memos.items())[:6]])
            lines.append(f"**Memos**: {memo_str}")

        return "\n".join(lines)
