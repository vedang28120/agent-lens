import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer
from agent_lens.core.dynamic_risk import DynamicRiskDetector


def test_dynamic_risk_detector_catches_reflection_and_duck_typing():
    with tempfile.TemporaryDirectory() as tmpdir:
        # File 1: target module
        target_f = os.path.join(tmpdir, "processor.py")
        with open(target_f, "w", encoding="utf-8") as f:
            f.write("def execute_pipeline():\n    return True\n")

        # File 2: uses getattr reflection
        f2 = os.path.join(tmpdir, "dispatcher.py")
        with open(f2, "w", encoding="utf-8") as f:
            f.write(
                "import importlib\n"
                "mod = importlib.import_module('processor')\n"
                "fn = getattr(mod, 'execute_pipeline')\n"
                "fn()\n"
            )

        # File 3: duck typed attribute access without import
        f3 = os.path.join(tmpdir, "caller.py")
        with open(f3, "w", encoding="utf-8") as f:
            f.write(
                "def run_any(obj):\n"
                "    return obj.execute_pipeline()\n"
            )

        cart = CodebaseCartographer(tmpdir)
        cart.scan()

        detector = DynamicRiskDetector(cart)
        audit = detector.audit_symbol_dynamic_risk("execute_pipeline", target_file="processor.py")

        assert audit["dynamic_risk_level"] == "HIGH"
        assert audit["total_unverified_references"] >= 2

        types = [find["type"] for find in audit["findings"]]
        assert "DYNAMIC_REFLECTION" in types
        assert "DUCK_TYPED_ATTRIBUTE_ACCESS" in types
