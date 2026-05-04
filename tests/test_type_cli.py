"""Tests for graphify type CLI commands."""
from __future__ import annotations

import json
import networkx as nx
from networkx.readwrite import json_graph

import graphify.__main__ as mainmod


def _write_graph_with_types(tmp_path):
    """Create a test graph with type metadata on function nodes."""
    G = nx.Graph()

    # Function with uint16_t return type
    G.add_node(
        "n1",
        label="get_value()",
        source_file="test.c",
        source_location="L5",
        return_type="uint16_t",
        parameters=[{"name": "x", "type": "uint32_t"}],
        community=0,
    )

    # Function with char* parameter
    G.add_node(
        "n2",
        label="process_string()",
        source_file="test.c",
        source_location="L10",
        return_type="void",
        parameters=[{"name": "input", "type": "char*"}],
        community=0,
    )

    # Function with int* parameter
    G.add_node(
        "n3",
        label="modify_value()",
        source_file="test.c",
        source_location="L15",
        return_type="void",
        parameters=[{"name": "ptr", "type": "int*"}],
        community=0,
    )

    # Function with multiple parameters including uint8_t
    G.add_node(
        "n4",
        label="clamp()",
        source_file="test.c",
        source_location="L20",
        return_type="uint8_t",
        parameters=[
            {"name": "val", "type": "uint8_t"},
            {"name": "min", "type": "uint8_t"},
            {"name": "max", "type": "uint8_t"},
        ],
        community=0,
    )

    # Class with String field
    G.add_node(
        "c1",
        label="Config",
        source_file="config.h",
        source_location="L1",
        file_type="class",
        fields=[{"name": "path", "type": "String"}],
        community=1,
    )

    # Class with int field
    G.add_node(
        "c2",
        label="Point",
        source_file="point.h",
        source_location="L1",
        file_type="class",
        fields=[{"name": "x", "type": "int"}, {"name": "y", "type": "int"}],
        community=1,
    )

    graph_path = tmp_path / "graph.json"
    graph_path.write_text(json.dumps(json_graph.node_link_data(G, edges="links")))
    return graph_path


def test_type_functions_return(monkeypatch, tmp_path, capsys):
    """Test: graphify type functions return uint16_t"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "functions", "return", "uint16_t", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    assert "get_value()" in out
    assert "Return: uint16_t" in out
    assert "test.c" in out


def test_type_functions_param(monkeypatch, tmp_path, capsys):
    """Test: graphify type functions param char*"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "functions", "param", "char*", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    assert "process_string()" in out
    assert "input: char*" in out


def test_type_classes_field(monkeypatch, tmp_path, capsys):
    """Test: graphify type classes field int"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "classes", "field", "int", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    assert "Point" in out
    assert "Field: x: int" in out


def test_type_list_all(monkeypatch, tmp_path, capsys):
    """Test: graphify type list-all"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "list-all", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    assert "Return types:" in out
    assert "Parameter types:" in out
    assert "uint16_t" in out
    assert "char*" in out


def test_type_functions_return_no_match(monkeypatch, tmp_path, capsys):
    """Test: no functions found with given return type"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "functions", "return", "float", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    assert "(none found)" in out


def test_type_functions_param_regex(monkeypatch, tmp_path, capsys):
    """Test: regex pattern matching for pointer types"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    # /\\w+\\*/ should match all pointer types
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "functions", "param", "/\\w+\\*/", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    # Should match both char* and int*
    assert "process_string()" in out
    assert "modify_value()" in out


def test_type_classes_missing_type_pattern(monkeypatch, tmp_path, capsys):
    """Test: error when type_pattern is missing for classes query"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    # Missing type_pattern after "field"
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "classes", "field", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    # Should show usage error
    assert "Usage" in out or "field" in out


def test_type_functions_missing_type_pattern(monkeypatch, tmp_path, capsys):
    """Test: error when type_pattern is missing for functions query"""
    graph_path = _write_graph_with_types(tmp_path)
    monkeypatch.setattr(mainmod, "_check_skill_version", lambda _: None)
    # Missing type_pattern after "return"
    monkeypatch.setattr(
        mainmod.sys,
        "argv",
        ["graphify", "type", "functions", "return", "--graph", str(graph_path)],
    )
    mainmod.main()
    out = capsys.readouterr().out
    # Should show usage error
    assert "Usage" in out or "return" in out
