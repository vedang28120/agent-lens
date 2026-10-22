import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.radar import ArchitectureRadar


def test_architecture_radar_and_cycle_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create circular dependency: a.py -> b.py -> a.py
        a_path = os.path.join(tmpdir, "a.py")
        b_path = os.path.join(tmpdir, "b.py")

        with open(a_path, "w", encoding="utf-8") as f:
            f.write("from b import func_b\ndef func_a():\n    return func_b()\n")

        with open(b_path, "w", encoding="utf-8") as f:
            f.write("from a import func_a\ndef func_b():\n    return func_a()\n")

        cart = CodebaseCartographer(tmpdir)
        cart.scan()
        radar = ArchitectureRadar(cart)
        report = radar.analyze()

        assert report["circular_count"] >= 1
        assert report["health_score"] < 100
        assert report["status"] in ["WARNING", "CRITICAL", "HEALTHY"]
