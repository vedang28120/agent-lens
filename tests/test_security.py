import os
import pytest
import tempfile
from agent_lens.core.security import resolve_safe_path, is_safe_path
from agent_lens.core.sentinel import PortSentinel


def test_resolve_safe_path_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        subfile = os.path.join(tmpdir, "subdir", "test.py")
        os.makedirs(os.path.dirname(subfile), exist_ok=True)
        with open(subfile, "w") as f:
            f.write("# test")

        resolved = resolve_safe_path(tmpdir, "subdir/test.py")
        assert os.path.exists(resolved)
        assert is_safe_path(tmpdir, "subdir/test.py") is True


def test_resolve_safe_path_traversal_rejection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Attempt directory traversal out of root
        with pytest.raises(PermissionError):
            resolve_safe_path(tmpdir, "../../etc/passwd")

        with pytest.raises(PermissionError):
            resolve_safe_path(tmpdir, "..\\..\\windows\\system32\\cmd.exe")

        assert is_safe_path(tmpdir, "../../etc/passwd") is False


def test_resolve_safe_path_null_bytes():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            resolve_safe_path(tmpdir, "file.py\x00.evil")


def test_sentinel_protected_pid_safety():
    # Attempting to kill port with system or invalid port
    res_bad_port = PortSentinel.kill_port(0)
    assert res_bad_port["success"] is False

    res_priv_port = PortSentinel.kill_port(80)
    assert res_priv_port["success"] is False
    assert "privileged" in res_bad_port.get("message", "").lower() or "privileged" in res_priv_port.get("message", "").lower() or "invalid" in res_bad_port.get("message", "").lower()
