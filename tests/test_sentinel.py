import pytest
from agent_lens.core.sentinel import PortSentinel


def test_port_sentinel_scan():
    ports = PortSentinel.list_listening_ports()
    assert isinstance(ports, list)
    # If there are listening ports, verify schema
    if ports and "error" not in ports[0]:
        first = ports[0]
        assert "port" in first
        assert "pid" in first
        assert "process_name" in first
