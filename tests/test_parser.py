import pytest
from agent_lens.core.parser import CodeParser


def test_python_ast_parsing():
    code = """
import os
from typing import List

class UserAuthService:
    \"\"\"Handles user authentication and tokens.\"\"\"

    def __init__(self, secret: str):
        self.secret = secret

    def authenticate(self, username: str, password_hash: str) -> bool:
        self.log_event(username)
        return True

    def log_event(self, msg: str):
        print(f"Log: {msg}")
"""
    res = CodeParser.parse_file("auth_service.py", content=code)

    assert res.language == "python"
    assert res.parse_error is None
    assert len(res.symbols) == 4  # Class + 3 methods

    # Check class
    cls_sym = next(s for s in res.symbols if s.kind == "class")
    assert cls_sym.name == "UserAuthService"
    assert "Handles user authentication" in cls_sym.docstring

    # Check method
    auth_sym = next(s for s in res.symbols if s.name == "authenticate")
    assert auth_sym.kind == "method"
    assert auth_sym.parent == "UserAuthService"
    assert "self.log_event" in auth_sym.calls or "log_event" in auth_sym.calls


def test_javascript_parsing():
    js_code = """
import { createServer } from 'http';

function startServer(port) {
    console.log("Starting server on port", port);
    return createServer();
}

class ApiRouter {
    handleRequest(req, res) {
        res.end("OK");
    }
}
"""
    res = CodeParser.parse_file("server.js", content=js_code)
    assert res.language == "javascript"
    assert res.parse_error is None
    sym_names = [s.name for s in res.symbols]
    assert "startServer" in sym_names
    assert "ApiRouter" in sym_names
