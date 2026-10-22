import os
import tempfile
import pytest
from agent_lens.core.memory import AgentMemory


def test_agent_memory_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = os.path.join(tmpdir, "test_memory.db")
        mem = AgentMemory(db_path=db_file)

        # 1. Hypotheses
        hid = mem.add_hypothesis(
            statement="CORS headers missing on /api/v1/session",
            status="exploring",
            evidence="Browser showed CORS blocked origin error"
        )
        assert hid == 1

        mem.update_hypothesis(hid, status="confirmed", evidence="Verified in network tab")
        hypos = mem.get_hypotheses()
        assert len(hypos) == 1
        assert hypos[0]["status"] == "confirmed"

        # 2. Decisions
        did = mem.add_decision(
            title="Use SQLite for local storage",
            rationale="Zero network latency and zero daemon prerequisites",
            tradeoffs="Single-writer concurrency limitation"
        )
        assert did == 1
        decs = mem.get_decisions()
        assert len(decs) == 1
        assert decs[0]["title"] == "Use SQLite for local storage"

        # 3. Tasks
        tid = mem.add_task("Implement Tree-Sitter parser", status="in_progress", priority=2)
        assert tid == 1
        mem.update_task(tid, status="done")
        tasks = mem.get_tasks()
        assert tasks[0]["status"] == "done"

        # 4. Memos
        mem.set_memo("server_port", "4141")
        assert mem.get_memo("server_port") == "4141"

        # 5. Scratchpad
        mem.update_scratchpad("Important note: Check port binding before start", updated_by="human")
        pad = mem.get_scratchpad()
        assert "Check port binding" in pad["content"]

        # 6. Compact Summary Briefing
        summary = mem.get_compact_summary()
        assert "[AGENT WORKING MEMORY RECOVERY]" in summary
        assert "CORS headers missing" in summary
