import pytest
from agent_lens.core.sentinel import PortSentinel


def test_sentinel_kill_port_confirmation_requirement():
    # Calling kill_port on non-existent port
    res_none = PortSentinel.kill_port(64321, confirm=False)
    assert res_none["success"] is False
    assert "no active process found" in res_none["message"].lower()

    # Calling kill_port on privileged port (<1024)
    res_priv = PortSentinel.kill_port(80, confirm=False)
    assert res_priv["success"] is False
    assert "privileged" in res_priv["message"].lower()


def test_sentinel_requires_confirm_on_active_port():
    # List active dev ports
    ports = PortSentinel.list_listening_ports()
    dev_ports = [p for p in ports if p.get("is_dev_port") and "error" not in p]
    if dev_ports:
        target = dev_ports[0]
        p_num = target["port"]
        # Try killing without confirm
        res = PortSentinel.kill_port(p_num, confirm=False)
        assert res["success"] is False
        assert res.get("requires_confirmation") is True
        assert "explicit confirmation" in res["message"].lower()
