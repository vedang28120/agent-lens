import pytest
from agent_lens.core.parser import CodeParser


def test_go_ast_parsing():
    go_code = """
package main

import (
    "fmt"
    "net/http"
)

type Config struct {
    Host string
    Port int
}

func (c *Config) Address() string {
    return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

func StartServer(cfg Config) {
    http.ListenAndServe(cfg.Address(), nil)
}
"""
    res = CodeParser.parse_file("server.go", content=go_code)
    assert res.language == "go"
    assert res.parse_error is None

    # Check symbols
    sym_map = {s.name: s for s in res.symbols}
    assert "Config" in sym_map
    assert sym_map["Config"].kind == "struct"

    assert "Address" in sym_map
    assert sym_map["Address"].kind == "method"
    assert sym_map["Address"].parent == "Config"

    assert "StartServer" in sym_map
    assert sym_map["StartServer"].kind == "function"

    # Check calls
    assert any("Sprintf" in c for c in res.all_calls)
    assert any("ListenAndServe" in c for c in res.all_calls)


def test_rust_ast_parsing():
    rust_code = """
use std::collections::HashMap;

pub struct Cache {
    data: HashMap<String, String>,
}

impl Cache {
    pub fn new() -> Self {
        println!("Initializing cache");
        Cache { data: HashMap::new() }
    }

    pub fn get(&self, key: &str) -> Option<&String> {
        self.data.get(key)
    }
}

pub fn helper_fn(x: i32) -> i32 {
    x * 2
}
"""
    res = CodeParser.parse_file("cache.rs", content=rust_code)
    assert res.language == "rust"
    assert res.parse_error is None

    # Check symbols
    sym_map = {s.name: s for s in res.symbols}
    assert "Cache" in sym_map
    assert sym_map["Cache"].kind == "struct"

    assert "new" in sym_map
    assert sym_map["new"].kind == "method"
    assert sym_map["new"].parent == "Cache"

    assert "get" in sym_map
    assert sym_map["get"].kind == "method"
    assert sym_map["get"].parent == "Cache"

    assert "helper_fn" in sym_map
    assert sym_map["helper_fn"].kind == "function"

    # Check calls & macros
    assert "println!" in res.all_calls or any("println" in c for c in res.all_calls)
    assert any("new" in c for c in res.all_calls)


def test_java_ast_parsing():
    java_code = """
package com.example.service;

import java.util.List;
import java.util.ArrayList;

public class UserService {
    private List<String> users = new ArrayList<>();

    public UserService() {
    }

    public void addUser(String user) {
        users.add(user);
    }

    public List<String> getUsers() {
        return users;
    }
}
"""
    res = CodeParser.parse_file("UserService.java", content=java_code)
    assert res.language == "java"
    assert res.parse_error is None

    # Check symbols
    sym_map = {s.name: s for s in res.symbols}
    assert "UserService" in sym_map
    assert sym_map["UserService"].kind in ["class", "method"]

    assert "addUser" in sym_map
    assert sym_map["addUser"].kind == "method"
    assert sym_map["addUser"].parent == "UserService"

    assert "getUsers" in sym_map
    assert sym_map["getUsers"].kind == "method"
    assert sym_map["getUsers"].parent == "UserService"

    # Check calls
    assert any("add" in c for c in res.all_calls)
