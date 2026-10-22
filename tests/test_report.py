import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.report import ArchitectureReporter
from agent_lens.core.memory import AgentMemory


def test_architecture_reporter():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample project structure
        a_path = os.path.join(tmpdir, "a.py")
        with open(a_path, "w", encoding="utf-8") as f:
            f.write("def func_a():\n    return 'A'\n")

        b_path = os.path.join(tmpdir, "b.py")
        with open(b_path, "w", encoding="utf-8") as f:
            f.write("from a import func_a\ndef func_b():\n    return func_a()\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()

        mem = AgentMemory(db_path=os.path.join(tmpdir, "memory.db"))
        mem.add_hypothesis("Testing report generation", status="confirmed")

        reporter = ArchitectureReporter(cart, memory=mem)
        report_md = reporter.generate_report()

        assert "AgentLens Codebase Architecture & Health Audit" in report_md
        assert "flowchart TD" in report_md
        assert "func_a" in report_md or "func_b" in report_md
        assert "Testing report generation" in report_md

        # Test writing report to disk
        out_file = reporter.write_report_to_file(os.path.join(tmpdir, "REPORT.md"))
        assert os.path.exists(out_file)
