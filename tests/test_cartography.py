import os
import tempfile
import pytest
from agent_lens.core.cartography import CodebaseCartographer


def test_cartography_indexing_and_blast_radius():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create module A: db.py
        db_path = os.path.join(tmpdir, "db.py")
        with open(db_path, "w", encoding="utf-8") as f:
            f.write("""
def connect_db():
    \"\"\"Establishes database connection.\"\"\"
    return "DB_CONN"
""")

        # Create module B: service.py
        service_path = os.path.join(tmpdir, "service.py")
        with open(service_path, "w", encoding="utf-8") as f:
            f.write("""
from db import connect_db

def fetch_users():
    conn = connect_db()
    return ["alice", "bob"]
""")

        # Create module C: test_service.py
        test_path = os.path.join(tmpdir, "test_service.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("""
from service import fetch_users

def test_fetch():
    assert len(fetch_users()) == 2
""")

        cart = CodebaseCartographer(tmpdir)
        metrics = cart.scan()

        assert metrics["files_scanned"] == 3
        assert "connect_db" in cart.symbol_index
        assert "fetch_users" in cart.symbol_index

        # Test Symbol Card
        card = cart.get_symbol_card("connect_db")
        assert card is not None
        assert card["symbol"] == "connect_db"
        assert "Establishes database connection" in card["docstring"]

        # Test Blast Radius
        blast = cart.calculate_blast_radius("db.py", symbol_name="connect_db")
        assert "service.py" in blast["impacted_files"]
        assert blast["risk_level"] in ["MEDIUM", "HIGH", "CRITICAL"]

        # Markdown representation
        md = cart.format_card_markdown(card)
        assert "[SYMBOL CARD]" in md
