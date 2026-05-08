"""Tests for language extractors: Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Go, Julia, JS/TS."""
from __future__ import annotations
from pathlib import Path
import pytest
from graphify.extract import (
    extract_java, extract_c, extract_cpp, extract_ruby,
    extract_csharp, extract_kotlin, extract_scala, extract_php,
    extract_swift, extract_go, extract_julia, extract_js,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _labels(r):
    return [n["label"] for n in r["nodes"]]

def _relations(r):
    return {e["relation"] for e in r["edges"]}

def _calls(r):
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    return {
        (node_by_id.get(e["source"], e["source"]), node_by_id.get(e["target"], e["target"]))
        for e in r["edges"] if e["relation"] == "calls"
    }


def _references(r):
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    return [
        (
            node_by_id.get(e["source"], e["source"]),
            node_by_id.get(e["target"], e["target"]),
            e,
        )
        for e in r["edges"] if e["relation"] == "references"
    ]


def _edges_with_relation(r, *relations):
    return [e for e in r["edges"] if e["relation"] in relations]


# ── Java ──────────────────────────────────────────────────────────────────────

def test_java_no_error():
    r = extract_java(FIXTURES / "sample.java")
    assert "error" not in r

def test_java_finds_class():
    r = extract_java(FIXTURES / "sample.java")
    assert any("DataProcessor" in l for l in _labels(r))

def test_java_finds_interface():
    r = extract_java(FIXTURES / "sample.java")
    assert any("Processor" in l for l in _labels(r))

def test_java_finds_methods():
    r = extract_java(FIXTURES / "sample.java")
    labels = _labels(r)
    assert any("addItem" in l for l in labels)
    assert any("process" in l for l in labels)

def test_java_finds_imports():
    r = extract_java(FIXTURES / "sample.java")
    assert "imports" in _relations(r)


def test_java_import_edges_have_import_context():
    r = extract_java(FIXTURES / "sample.java")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)

def test_java_no_dangling_edges():
    r = extract_java(FIXTURES / "sample.java")
    node_ids = {n["id"] for n in r["nodes"]}
    for e in r["edges"]:
        assert e["source"] in node_ids


# ── C ────────────────────────────────────────────────────────────────────────

def test_c_no_error():
    r = extract_c(FIXTURES / "sample.c")
    assert "error" not in r

def test_c_finds_functions():
    r = extract_c(FIXTURES / "sample.c")
    labels = _labels(r)
    assert any("process" in l for l in labels)
    assert any("main" in l for l in labels)

def test_c_finds_includes():
    r = extract_c(FIXTURES / "sample.c")
    assert "imports" in _relations(r)

def test_c_emits_calls():
    r = extract_c(FIXTURES / "sample.c")
    assert any(e["relation"] == "calls" for e in r["edges"])

def test_c_calls_are_extracted():
    r = extract_c(FIXTURES / "sample.c")
    for e in r["edges"]:
        if e["relation"] == "calls":
            assert e["confidence"] == "EXTRACTED"


def test_c_import_edges_have_import_context():
    r = extract_c(FIXTURES / "sample.c")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


def test_c_call_edges_have_call_context():
    r = extract_c(FIXTURES / "sample.c")
    call_edges = _edges_with_relation(r, "calls")
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)


# ── C++ ───────────────────────────────────────────────────────────────────────

def test_cpp_no_error():
    r = extract_cpp(FIXTURES / "sample.cpp")
    assert "error" not in r

def test_cpp_finds_class():
    r = extract_cpp(FIXTURES / "sample.cpp")
    assert any("HttpClient" in l for l in _labels(r))

def test_cpp_finds_methods():
    r = extract_cpp(FIXTURES / "sample.cpp")
    labels = _labels(r)
    # C++ extractor captures the constructor and public-visible methods
    assert any("HttpClient" in l for l in labels)

def test_cpp_finds_includes():
    r = extract_cpp(FIXTURES / "sample.cpp")
    assert "imports" in _relations(r)


def test_cpp_import_edges_have_import_context():
    r = extract_cpp(FIXTURES / "sample.cpp")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


# ── Ruby ─────────────────────────────────────────────────────────────────────

def test_ruby_no_error():
    r = extract_ruby(FIXTURES / "sample.rb")
    assert "error" not in r

def test_ruby_finds_class():
    r = extract_ruby(FIXTURES / "sample.rb")
    assert any("ApiClient" in l for l in _labels(r))

def test_ruby_finds_methods():
    r = extract_ruby(FIXTURES / "sample.rb")
    labels = _labels(r)
    assert any("get" in l for l in labels)
    assert any("post" in l for l in labels)

def test_ruby_finds_function():
    r = extract_ruby(FIXTURES / "sample.rb")
    assert any("parse_response" in l for l in _labels(r))


# ── C# ───────────────────────────────────────────────────────────────────────

def test_csharp_no_error():
    r = extract_csharp(FIXTURES / "sample.cs")
    assert "error" not in r

def test_csharp_finds_class():
    r = extract_csharp(FIXTURES / "sample.cs")
    assert any("DataProcessor" in l for l in _labels(r))

def test_csharp_finds_interface():
    r = extract_csharp(FIXTURES / "sample.cs")
    assert any("IProcessor" in l for l in _labels(r))

def test_csharp_finds_methods():
    r = extract_csharp(FIXTURES / "sample.cs")
    labels = _labels(r)
    assert any("Process" in l for l in labels)

def test_csharp_finds_usings():
    r = extract_csharp(FIXTURES / "sample.cs")
    assert "imports" in _relations(r)

def test_csharp_inherits_edge():
    r = extract_csharp(FIXTURES / "sample.cs")
    inherits = [e for e in r["edges"] if e["relation"] == "inherits"]
    assert len(inherits) >= 1

def test_csharp_inherits_iprocessor():
    r = extract_csharp(FIXTURES / "sample.cs")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    found = any(
        "DataProcessor" in node_by_id.get(e["source"], "") and
        "IProcessor" in node_by_id.get(e["target"], "")
        for e in r["edges"] if e["relation"] == "inherits"
    )
    assert found, "DataProcessor should have inherits edge to IProcessor"


def test_csharp_field_type_references_have_field_context():
    r = extract_csharp(FIXTURES / "sample.cs")
    refs = _references(r)
    assert any(
        "DataProcessor" in src and "HttpClient" in tgt and edge.get("context") == "field"
        for src, tgt, edge in refs
    ), "DataProcessor field declarations should reference HttpClient with field context"


def test_csharp_call_edges_have_call_context():
    r = extract_csharp(FIXTURES / "sample.cs")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    assert any(
        "Process" in node_by_id.get(e["source"], "")
        and "Validate" in node_by_id.get(e["target"], "")
        and e.get("context") == "call"
        for e in r["edges"] if e["relation"] == "calls"
    ), "C# call edges should retain call context"


def test_csharp_import_edges_have_import_context():
    r = extract_csharp(FIXTURES / "sample.cs")
    import_edges = [e for e in r["edges"] if e["relation"] == "imports"]
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


# ── Kotlin ───────────────────────────────────────────────────────────────────

def test_kotlin_no_error():
    r = extract_kotlin(FIXTURES / "sample.kt")
    assert "error" not in r

def test_kotlin_finds_class():
    r = extract_kotlin(FIXTURES / "sample.kt")
    assert any("HttpClient" in l for l in _labels(r))

def test_kotlin_finds_data_class():
    r = extract_kotlin(FIXTURES / "sample.kt")
    assert any("Config" in l for l in _labels(r))

def test_kotlin_finds_methods():
    r = extract_kotlin(FIXTURES / "sample.kt")
    labels = _labels(r)
    assert any("get" in l for l in labels)
    assert any("post" in l for l in labels)

def test_kotlin_finds_function():
    r = extract_kotlin(FIXTURES / "sample.kt")
    assert any("createClient" in l for l in _labels(r))

def test_kotlin_emits_in_file_calls():
    """Regression test for the call-walker `simple_identifier` /
    `identifier` rename — see graphify-kmp's PythonParityTest."""
    r = extract_kotlin(FIXTURES / "sample.kt")
    calls = _calls(r)
    # In sample.kt: get() and post() both call buildRequest(), and
    # createClient() invokes Config and HttpClient (constructor calls).
    assert (".get()", ".buildRequest()") in calls
    assert (".post()", ".buildRequest()") in calls
    assert ("createClient()", "Config") in calls
    assert ("createClient()", "HttpClient") in calls


# ── Scala ─────────────────────────────────────────────────────────────────────

def test_scala_no_error():
    r = extract_scala(FIXTURES / "sample.scala")
    assert "error" not in r

def test_scala_finds_class():
    r = extract_scala(FIXTURES / "sample.scala")
    assert any("HttpClient" in l for l in _labels(r))

def test_scala_finds_object():
    r = extract_scala(FIXTURES / "sample.scala")
    assert any("HttpClientFactory" in l for l in _labels(r))

def test_scala_finds_methods():
    r = extract_scala(FIXTURES / "sample.scala")
    labels = _labels(r)
    assert any("get" in l for l in labels)
    assert any("post" in l for l in labels)


def test_scala_import_edges_have_import_context():
    r = extract_scala(FIXTURES / "sample.scala")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


def test_scala_call_edges_have_call_context():
    r = extract_scala(FIXTURES / "sample.scala")
    call_edges = _edges_with_relation(r, "calls")
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)


# ── PHP ───────────────────────────────────────────────────────────────────────

def test_php_no_error():
    r = extract_php(FIXTURES / "sample.php")
    assert "error" not in r

def test_php_finds_class():
    r = extract_php(FIXTURES / "sample.php")
    assert any("ApiClient" in l for l in _labels(r))

def test_php_finds_methods():
    r = extract_php(FIXTURES / "sample.php")
    labels = _labels(r)
    assert any("get" in l for l in labels)
    assert any("post" in l for l in labels)

def test_php_finds_function():
    r = extract_php(FIXTURES / "sample.php")
    assert any("parseResponse" in l for l in _labels(r))

def test_php_finds_imports():
    r = extract_php(FIXTURES / "sample.php")
    assert "imports" in _relations(r)


def test_php_import_edges_have_import_context():
    r = extract_php(FIXTURES / "sample.php")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


def test_php_call_edges_have_call_context():
    r = extract_php(FIXTURES / "sample.php")
    call_edges = _edges_with_relation(r, "calls")
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)

def test_php_finds_static_property_access():
    r = extract_php(FIXTURES / "sample_php_static_prop.php")
    assert "uses_static_prop" in _relations(r)

def test_php_static_prop_target_is_holding_class():
    r = extract_php(FIXTURES / "sample_php_static_prop.php")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    uses_prop = [
        (node_by_id.get(e["source"], e["source"]), node_by_id.get(e["target"], e["target"]))
        for e in r["edges"] if e["relation"] == "uses_static_prop"
    ]
    assert any("DefaultPalette" in tgt for _, tgt in uses_prop)

def test_php_finds_config_helper_call():
    r = extract_php(FIXTURES / "sample_php_config.php")
    assert "uses_config" in _relations(r)

def test_php_config_helper_target_matches_first_segment():
    r = extract_php(FIXTURES / "sample_php_config.php")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    uses_cfg = [
        (node_by_id.get(e["source"], e["source"]), node_by_id.get(e["target"], e["target"]))
        for e in r["edges"] if e["relation"] == "uses_config"
    ]
    assert any("Throttle" in tgt for _, tgt in uses_cfg)

def test_php_finds_container_bind():
    r = extract_php(FIXTURES / "sample_php_container.php")
    assert "bound_to" in _relations(r)

def test_php_container_bind_links_contract_to_implementation():
    r = extract_php(FIXTURES / "sample_php_container.php")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    bound = [
        (node_by_id.get(e["source"], e["source"]), node_by_id.get(e["target"], e["target"]))
        for e in r["edges"] if e["relation"] == "bound_to"
    ]
    assert any("PaymentGateway" in src and "StripeGateway" in tgt for src, tgt in bound)

def test_php_finds_event_listeners():
    r = extract_php(FIXTURES / "sample_php_listen.php")
    assert "listened_by" in _relations(r)

def test_php_event_listener_links_event_to_listener():
    r = extract_php(FIXTURES / "sample_php_listen.php")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    listened = [
        (node_by_id.get(e["source"], e["source"]), node_by_id.get(e["target"], e["target"]))
        for e in r["edges"] if e["relation"] == "listened_by"
    ]
    assert any("UserRegistered" in src and "SendWelcomeEmail" in tgt for src, tgt in listened)


# ── Swift ────────────────────────────────────────────────────────────────────

def test_swift_no_error():
    r = extract_swift(FIXTURES / "sample.swift")
    assert "error" not in r

def test_swift_finds_class():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("DataProcessor" in l for l in _labels(r))

def test_swift_finds_protocol():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("Processor" in l for l in _labels(r))

def test_swift_finds_struct():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("Config" in l for l in _labels(r))

def test_swift_finds_methods():
    r = extract_swift(FIXTURES / "sample.swift")
    labels = _labels(r)
    assert any("addItem" in l for l in labels)
    assert any("process" in l for l in labels)

def test_swift_finds_function():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("createProcessor" in l for l in _labels(r))

def test_swift_finds_imports():
    r = extract_swift(FIXTURES / "sample.swift")
    assert "imports" in _relations(r)


def test_swift_import_edges_have_import_context():
    r = extract_swift(FIXTURES / "sample.swift")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)

def test_swift_no_dangling_edges():
    r = extract_swift(FIXTURES / "sample.swift")
    node_ids = {n["id"] for n in r["nodes"]}
    for e in r["edges"]:
        assert e["source"] in node_ids

def test_swift_finds_actor():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("CacheManager" in l for l in _labels(r))

def test_swift_finds_enum():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("NetworkError" in l for l in _labels(r))

def test_swift_finds_enum_methods():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("describe" in l for l in _labels(r))

def test_swift_finds_enum_cases():
    r = extract_swift(FIXTURES / "sample.swift")
    labels = _labels(r)
    assert any("timeout" in l for l in labels)
    assert any("connectionFailed" in l for l in labels)

def test_swift_enum_cases_have_case_of_edge():
    r = extract_swift(FIXTURES / "sample.swift")
    case_edges = [e for e in r["edges"] if e["relation"] == "case_of"]
    assert len(case_edges) >= 2

def test_swift_finds_deinit():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("deinit" in l for l in _labels(r))

def test_swift_finds_subscript():
    r = extract_swift(FIXTURES / "sample.swift")
    assert any("subscript" in l for l in _labels(r))

def test_swift_extension_methods_attach_to_type():
    r = extract_swift(FIXTURES / "sample.swift")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    method_edges = [e for e in r["edges"] if e["relation"] == "method"]
    found = False
    for e in method_edges:
        src_label = node_by_id.get(e["source"], "")
        tgt_label = node_by_id.get(e["target"], "")
        if "Config" in src_label and "isValid" in tgt_label:
            found = True
            break
    assert found, "extension method isValid should attach to Config"

def test_swift_extension_does_not_duplicate_type_node():
    r = extract_swift(FIXTURES / "sample.swift")
    config_nodes = [n for n in r["nodes"] if n["label"] == "Config"]
    assert len(config_nodes) == 1, f"Config should appear once, got {len(config_nodes)}"

def test_swift_conformance_edge():
    r = extract_swift(FIXTURES / "sample.swift")
    inherits_edges = [e for e in r["edges"] if e["relation"] == "inherits"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    found = False
    for e in inherits_edges:
        src_label = node_by_id.get(e["source"], "")
        tgt_label = node_by_id.get(e["target"], "")
        if "DataProcessor" in src_label and "Processor" in tgt_label:
            found = True
            break
    assert found, "DataProcessor should have inherits edge to Processor"

def test_swift_extension_conformance_edge():
    r = extract_swift(FIXTURES / "sample.swift")
    inherits_edges = [e for e in r["edges"] if e["relation"] == "inherits"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    found = False
    for e in inherits_edges:
        src_label = node_by_id.get(e["source"], "")
        tgt_label = node_by_id.get(e["target"], "")
        if "DataProcessor" in src_label and "Loggable" in tgt_label:
            found = True
            break
    assert found, "extension should add conformance edge DataProcessor -> Loggable"

def test_swift_emits_calls():
    r = extract_swift(FIXTURES / "sample.swift")
    calls = _calls(r)
    assert any("process" in src and "validate" in tgt for src, tgt in calls)

def test_swift_call_edges_have_call_context():
    r = extract_swift(FIXTURES / "sample.swift")
    call_edges = _edges_with_relation(r, "calls")
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)


# ── Elixir ────────────────────────────────────────────────────────────────────

from graphify.extract import extract_elixir

def test_elixir_finds_module():
    r = extract_elixir(FIXTURES / "sample.ex")
    assert "error" not in r
    labels = [n["label"] for n in r["nodes"]]
    assert any("MyApp.Accounts.User" in l for l in labels)

def test_elixir_finds_functions():
    r = extract_elixir(FIXTURES / "sample.ex")
    labels = [n["label"] for n in r["nodes"]]
    assert any("create" in l for l in labels)
    assert any("find" in l for l in labels)
    assert any("validate" in l for l in labels)

def test_elixir_finds_imports():
    r = extract_elixir(FIXTURES / "sample.ex")
    import_edges = [e for e in r["edges"] if e["relation"] == "imports"]
    assert len(import_edges) >= 2


def test_elixir_import_edges_have_import_context():
    r = extract_elixir(FIXTURES / "sample.ex")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)

def test_elixir_finds_calls():
    r = extract_elixir(FIXTURES / "sample.ex")
    calls = {(e["source"], e["target"]) for e in r["edges"] if e["relation"] == "calls"}
    labels = {n["id"]: n["label"] for n in r["nodes"]}
    assert any("create" in labels.get(src, "") and "validate" in labels.get(tgt, "") for src, tgt in calls)


def test_elixir_call_edges_have_call_context():
    r = extract_elixir(FIXTURES / "sample.ex")
    call_edges = _edges_with_relation(r, "calls")
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)

def test_elixir_method_edges():
    r = extract_elixir(FIXTURES / "sample.ex")
    methods = [e for e in r["edges"] if e["relation"] == "method"]
    assert len(methods) >= 3


# ── Objective-C ──────────────────────────────────────────────────────────────
from graphify.extract import extract_objc


def test_objc_finds_interface():
    r = extract_objc(FIXTURES / "sample.m")
    labels = [n["label"] for n in r["nodes"]]
    assert "Animal" in labels


def test_objc_finds_subclass():
    r = extract_objc(FIXTURES / "sample.m")
    labels = [n["label"] for n in r["nodes"]]
    assert "Dog" in labels


def test_objc_finds_methods():
    r = extract_objc(FIXTURES / "sample.m")
    labels = [n["label"] for n in r["nodes"]]
    assert any("speak" in l or "fetch" in l or "initWithName" in l for l in labels)


def test_objc_finds_imports():
    r = extract_objc(FIXTURES / "sample.m")
    import_edges = [e for e in r["edges"] if e["relation"] == "imports"]
    assert len(import_edges) >= 1


def test_objc_import_edges_have_import_context():
    r = extract_objc(FIXTURES / "sample.m")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


def test_objc_inherits_edge():
    r = extract_objc(FIXTURES / "sample.m")
    inherits = [e for e in r["edges"] if e["relation"] == "inherits"]
    assert len(inherits) >= 1


def test_objc_no_dangling_edges():
    r = extract_objc(FIXTURES / "sample.m")
    node_ids = {n["id"] for n in r["nodes"]}
    for e in r["edges"]:
        assert e["source"] in node_ids, f"Dangling source: {e}"


# ---------------------------------------------------------------------------
# Go
# ---------------------------------------------------------------------------

def test_go_receiver_methods_share_type_node():
    """Methods on the same receiver type must share one canonical type node."""
    r = extract_go(FIXTURES / "sample.go")
    server_nodes = [n for n in r["nodes"] if n["label"] == "Server"]
    # Both Start() and Stop() are on *Server — should produce exactly one Server node
    assert len(server_nodes) == 1

def test_go_receiver_uses_pkg_scope():
    """Type node id should be scoped to directory, not file stem."""
    r = extract_go(FIXTURES / "sample.go")
    server_nodes = [n for n in r["nodes"] if n["label"] == "Server"]
    assert server_nodes
    # Should NOT contain the file stem "sample" in the type node id
    assert "sample" not in server_nodes[0]["id"].split(":")[0]


# ---------------------------------------------------------------------------
# Julia
# ---------------------------------------------------------------------------

def test_julia_finds_module():
    r = extract_julia(FIXTURES / "sample.jl")
    labels = [n["label"] for n in r["nodes"]]
    assert "Geometry" in labels


def test_julia_finds_structs():
    r = extract_julia(FIXTURES / "sample.jl")
    labels = [n["label"] for n in r["nodes"]]
    assert "Point" in labels
    assert "Circle" in labels


def test_julia_finds_abstract_type():
    r = extract_julia(FIXTURES / "sample.jl")
    labels = [n["label"] for n in r["nodes"]]
    assert "Shape" in labels


def test_julia_finds_functions():
    r = extract_julia(FIXTURES / "sample.jl")
    labels = [n["label"] for n in r["nodes"]]
    assert any("area" in l for l in labels)
    assert any("distance" in l for l in labels)


def test_julia_finds_short_function():
    r = extract_julia(FIXTURES / "sample.jl")
    labels = [n["label"] for n in r["nodes"]]
    assert any("perimeter" in l for l in labels)


def test_julia_finds_imports():
    r = extract_julia(FIXTURES / "sample.jl")
    import_edges = [e for e in r["edges"] if e["relation"] == "imports"]
    assert len(import_edges) >= 1


def test_julia_import_edges_have_import_context():
    r = extract_julia(FIXTURES / "sample.jl")
    import_edges = _edges_with_relation(r, "imports", "imports_from")
    assert import_edges
    assert all(e.get("context") == "import" for e in import_edges)


def test_julia_finds_inherits():
    r = extract_julia(FIXTURES / "sample.jl")
    inherits = [e for e in r["edges"] if e["relation"] == "inherits"]
    assert len(inherits) >= 1


def test_julia_finds_calls():
    r = extract_julia(FIXTURES / "sample.jl")
    call_edges = [e for e in r["edges"] if e["relation"] == "calls"]
    assert len(call_edges) >= 1


def test_julia_call_edges_have_call_context():
    r = extract_julia(FIXTURES / "sample.jl")
    call_edges = _edges_with_relation(r, "calls")
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)


def test_julia_no_dangling_edges():
    r = extract_julia(FIXTURES / "sample.jl")
    node_ids = {n["id"] for n in r["nodes"]}
    for e in r["edges"]:
        assert e["source"] in node_ids, f"Dangling source: {e}"


# ── TypeScript dynamic imports ───────────────────────────────────────────────

def test_ts_dynamic_import_no_error():
    r = extract_js(FIXTURES / "dynamic_import.ts")
    assert "error" not in r

def test_ts_dynamic_import_extracts_edges():
    """Dynamic import() calls inside functions should produce imports_from edges."""
    r = extract_js(FIXTURES / "dynamic_import.ts")
    dyn_edges = [e for e in r["edges"] if e["relation"] == "imports_from"]
    targets = {e["target"] for e in dyn_edges}
    # Should find: static ./logger, dynamic ./mayaEngine.js, dynamic ./queue.js
    assert any("logger" in t for t in targets), f"Missing static import of logger: {targets}"
    assert any("mayaengine" in t.lower() for t in targets), f"Missing dynamic import of mayaEngine: {targets}"
    assert any("queue" in t.lower() for t in targets), f"Missing dynamic import of queue: {targets}"

def test_ts_dynamic_import_confidence():
    """Dynamic imports should have EXTRACTED confidence (they are deterministic string literals)."""
    r = extract_js(FIXTURES / "dynamic_import.ts")
    dyn_edges = [e for e in r["edges"]
                 if e["relation"] == "imports_from"
                 and "mayaengine" in e["target"].lower()]
    assert len(dyn_edges) >= 1
    assert dyn_edges[0]["confidence"] == "EXTRACTED"

def test_ts_dynamic_import_source_is_function():
    """Dynamic import edge source should be the enclosing function, not the file."""
    r = extract_js(FIXTURES / "dynamic_import.ts")
    node_labels = {n["id"]: n["label"] for n in r["nodes"]}
    dyn_edges = [e for e in r["edges"]
                 if e["relation"] == "imports_from"
                 and "mayaengine" in e["target"].lower()]
    assert len(dyn_edges) >= 1
    src_label = node_labels.get(dyn_edges[0]["source"], "")
    assert "processInbound" in src_label, f"Expected processInbound as source, got {src_label}"

def test_ts_no_dynamic_import_in_sync_fn():
    """Functions without dynamic imports should not get spurious imports_from edges."""
    r = extract_js(FIXTURES / "dynamic_import.ts")
    node_ids = {n["label"]: n["id"] for n in r["nodes"]}
    sync_nid = node_ids.get("syncOnly()")
    if sync_nid:
        sync_imports = [e for e in r["edges"]
                        if e["source"] == sync_nid and e["relation"] == "imports_from"]
        assert len(sync_imports) == 0

def test_ts_dynamic_template_literal_skipped():
    """Dynamic template literals (with ${}) must not produce an imports_from edge."""
    r = extract_js(FIXTURES / "dynamic_import.ts")
    targets = {e["target"] for e in r["edges"] if e["relation"] == "imports_from"}
    # loadHandler uses `./handlers/${handlerName}` — no static path, must be absent
    assert not any("handler" in t.lower() and "$" in t for t in targets), \
        f"Garbage edge from dynamic template literal found: {targets}"
    # More robust: no target should contain a brace character
    assert not any("{" in t or "}" in t for t in targets), \
        f"Target contains unresolved template expression: {targets}"

def test_ts_static_template_literal_resolved():
    """Static template literals (no ${}) should resolve the same as a plain string."""
    r = extract_js(FIXTURES / "dynamic_import.ts")
    targets = {e["target"] for e in r["edges"] if e["relation"] == "imports_from"}
    assert any("statichelper" in t.lower() for t in targets), \
        f"Static template literal import not resolved: {targets}"


# ── External library call tracking ───────────────────────────────────────────

def test_ts_external_call_default_import():
    """jwt.decode() on a default import should produce a calls_external edge."""
    r = extract_js(FIXTURES / "external_calls.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    targets = {e["target"] for e in ext_edges}
    assert any("jsonwebtoken" in t and "decode" in t for t in targets), \
        f"Expected calls_external edge to jsonwebtoken.decode, got targets: {targets}"


def test_ts_external_call_namespace_import():
    """fs.readFileSync() on a namespace import (import * as fs) should produce a calls_external edge."""
    r = extract_js(FIXTURES / "external_calls.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    targets = {e["target"] for e in ext_edges}
    assert any("fs" in t and "readfilesync" in t.lower() for t in targets), \
        f"Expected calls_external edge to fs.readFileSync, got targets: {targets}"


def test_ts_external_call_named_import():
    """createHash() from a named import should produce a calls_external edge when used as member call."""
    r = extract_js(FIXTURES / "external_calls.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    # createHash is a named import used as a direct call, not a member call — it
    # should appear as a regular cross-file callee miss (no external edge needed).
    # This test confirms named-import *direct* calls are not mis-classified.
    ext_targets = {e["target"] for e in ext_edges}
    assert not any("createhash" in t.lower() and "crypto" not in t.lower() for t in ext_targets), \
        f"createHash should not produce a spurious external edge: {ext_targets}"


def test_ts_external_call_node_created():
    """External call nodes should have file_type='external_call' and be in all_nodes."""
    r = extract_js(FIXTURES / "external_calls.ts")
    ext_nodes = [n for n in r["nodes"] if n.get("file_type") == "external_call"]
    labels = {n["label"] for n in ext_nodes}
    assert any("jsonwebtoken" in lb for lb in labels), \
        f"Expected external_call node for jsonwebtoken.decode, got: {labels}"


def test_ts_external_call_confidence():
    """calls_external edges should have EXTRACTED confidence (binding is statically known)."""
    r = extract_js(FIXTURES / "external_calls.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    assert ext_edges, "Expected at least one calls_external edge"
    assert all(e["confidence"] == "EXTRACTED" for e in ext_edges), \
        f"Expected EXTRACTED confidence on all calls_external edges"


def test_ts_external_call_caller_is_function():
    """The source of a calls_external edge should be the enclosing function node."""
    r = extract_js(FIXTURES / "external_calls.ts")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    jwt_edges = [e for e in r["edges"]
                 if e["relation"] == "calls_external"
                 and "jsonwebtoken" in e["target"] and "decode" in e["target"]]
    assert jwt_edges, "Expected calls_external edge from buildContext to jwt.decode"
    src_label = node_by_id.get(jwt_edges[0]["source"], "")
    assert "buildContext" in src_label, \
        f"Expected source to be buildContext(), got: {src_label}"


def test_ts_internal_call_unaffected():
    """Internal function calls (internalHelper → buildContext) still produce a calls edge."""
    r = extract_js(FIXTURES / "external_calls.ts")
    call_edges = [e for e in r["edges"] if e["relation"] == "calls"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    labels_called = {node_by_id.get(e["target"], "") for e in call_edges}
    assert any("buildContext" in lb for lb in labels_called), \
        f"Expected internal call edge to buildContext, got: {labels_called}"


def test_ts_no_spurious_external_edges_for_this_field():
    """Member calls on 'this' (this.baseUrl) should not produce external edges."""
    r = extract_js(FIXTURES / "sample.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    assert len(ext_edges) == 0, \
        f"sample.ts has no external imports; expected no calls_external edges, got: {ext_edges}"


# ── Argument reference tracking ───────────────────────────────────────────────

def test_ts_arg_ref_direct_identifier():
    """foo(buildContext) should produce a references edge from callWithRef to buildContext."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    targets = {node_by_id.get(e["target"], "") for e in ref_edges}
    assert any("buildContext" in t for t in targets), \
        f"Expected references edge targeting buildContext, got targets: {targets}"


def test_ts_arg_ref_object_property():
    """new ApolloServer({{ context: buildContext }}) should produce a references edge."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    targets = {node_by_id.get(e["target"], "") for e in ref_edges}
    assert any("buildContext" in t for t in targets), \
        f"Expected references edge from new_expression object arg, got: {targets}"


def test_ts_arg_ref_caller_is_function():
    """References edge source should be the enclosing function, not the file node."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "buildContext" in n["label"]), None)
    assert build_ctx_nid, "buildContext node not found"
    edges_to_ctx = [e for e in ref_edges if e["target"] == build_ctx_nid]
    assert edges_to_ctx, "No references edges pointing to buildContext"
    sources = {node_by_id.get(e["source"], "") for e in edges_to_ctx}
    assert any(s for s in sources if s not in ("", "arg_refs.ts")), \
        f"Expected function-level source for references edge, got: {sources}"


def test_ts_arg_ref_confidence():
    """references edges from arg refs should have EXTRACTED confidence."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    assert ref_edges, "Expected at least one arg_ref references edge"
    assert all(e["confidence"] == "EXTRACTED" for e in ref_edges)


def test_ts_arg_ref_no_spurious_self_reference():
    """buildConfig itself should not have a self-references edge."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"]
    self_loops = [e for e in ref_edges if e["source"] == e["target"]]
    assert not self_loops, f"Self-referencing edges found: {self_loops}"


def test_ts_arg_ref_callee_not_double_counted():
    """buildServer() calls buildConfig() — buildConfig should appear as calls, not references."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_cfg_nid = next((n["id"] for n in r["nodes"] if "buildConfig" in n["label"]), None)
    assert build_cfg_nid, "buildConfig node not found"
    calls_to_cfg = [e for e in r["edges"]
                    if e["target"] == build_cfg_nid and e["relation"] == "calls"]
    refs_to_cfg = [e for e in r["edges"]
                   if e["target"] == build_cfg_nid and e["relation"] == "references"]
    assert calls_to_cfg, "buildConfig should be reached via a calls edge"
    assert not refs_to_cfg, \
        f"buildConfig should not be double-counted as a references edge: {refs_to_cfg}"


def test_ts_arg_ref_positional_arg_key():
    """Direct positional arg should carry a numeric arg_key (0-based index)."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "buildContext" in n["label"]), None)
    assert build_ctx_nid, "buildContext node not found"
    # callWithRef() passes buildContext as positional arg 0
    positional_edges = [
        e for e in r["edges"]
        if e["relation"] == "references"
        and e["target"] == build_ctx_nid
        and isinstance(e.get("arg_key"), int)
    ]
    assert positional_edges, \
        f"Expected a references edge with numeric arg_key for positional arg, got: " \
        f"{[e.get('arg_key') for e in r['edges'] if e['relation'] == 'references' and e['target'] == build_ctx_nid]}"
    assert positional_edges[0]["arg_key"] == 0


def test_ts_arg_ref_object_property_arg_key():
    """Object property arg should carry the property name as arg_key string."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "buildContext" in n["label"]), None)
    assert build_ctx_nid, "buildContext node not found"
    # buildConfig() and new ApolloServer() both pass buildContext as { context: buildContext }
    named_edges = [
        e for e in r["edges"]
        if e["relation"] == "references"
        and e["target"] == build_ctx_nid
        and e.get("arg_key") == "context"
    ]
    assert named_edges, \
        f"Expected a references edge with arg_key='context', got arg_keys: " \
        f"{[e.get('arg_key') for e in r['edges'] if e['relation'] == 'references' and e['target'] == build_ctx_nid]}"


def test_ts_arg_ref_object_return_value():
    """Arrow fn returning an object literal: (gw) => ({ context: buildContext })
    should produce buildConfigArrow → references → buildContext with arg_key='context'.
    This covers the indirect Apollo pattern where context is wired inside a config
    factory rather than directly in new ApolloServer({...})."""
    r = extract_js(FIXTURES / "arg_refs.ts")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "buildContext" in n["label"]), None)
    assert build_ctx_nid, "buildContext node not found"
    # Source should be buildConfigArrow (the arrow function returning the object)
    object_return_edges = [
        e for e in r["edges"]
        if e["relation"] == "references"
        and e["target"] == build_ctx_nid
        and e.get("arg_key") == "context"
        and "buildConfigArrow" in node_by_id.get(e["source"], "")
    ]
    assert object_return_edges, (
        f"Expected buildConfigArrow → references(context) → buildContext. "
        f"All references edges to buildContext: "
        f"{[(node_by_id.get(e['source']), e.get('arg_key')) for e in r['edges'] if e['relation'] == 'references' and e['target'] == build_ctx_nid]}"
    )


# ── CommonJS require() binding support ───────────────────────────────────────

def test_ts_require_default_binding():
    """const jwt = require('jsonwebtoken') should produce a calls_external edge for jwt.decode()."""
    r = extract_js(FIXTURES / "commonjs_require.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    targets = {e["target"] for e in ext_edges}
    assert any("jsonwebtoken" in t and "decode" in t for t in targets), \
        f"Expected calls_external to jsonwebtoken.decode via require binding, got: {targets}"


def test_ts_require_default_binding_hoek():
    """const hoek = require('hoek') should produce a calls_external edge for hoek.reach()."""
    r = extract_js(FIXTURES / "commonjs_require.ts")
    ext_edges = [e for e in r["edges"] if e["relation"] == "calls_external"]
    targets = {e["target"] for e in ext_edges}
    assert any("hoek" in t and "reach" in t for t in targets), \
        f"Expected calls_external to hoek.reach via require binding, got: {targets}"


def test_ts_require_destructured_binding():
    """const {{ reach }} = require('hoek') should also produce a calls_external edge."""
    r = extract_js(FIXTURES / "commonjs_require.ts")
    ext_nodes = [n for n in r["nodes"] if n.get("file_type") == "external_call"]
    labels = {n["label"] for n in ext_nodes}
    # clone() is called directly (not as member call) — it's a named import ref,
    # not a member call, so no calls_external edge; but the binding should exist.
    # reach() via hoek.reach() should still appear.
    assert any("hoek" in lb for lb in labels), \
        f"Expected external_call node for hoek.*, got: {labels}"


def test_ts_require_caller_is_buildcontext():
    """calls_external edge source for jwt.decode() should be buildContext()."""
    r = extract_js(FIXTURES / "commonjs_require.ts")
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    jwt_edges = [e for e in r["edges"]
                 if e["relation"] == "calls_external"
                 and "jsonwebtoken" in e.get("target", "")
                 and "decode" in e.get("target", "")]
    assert jwt_edges, "No calls_external edge to jsonwebtoken.decode"
    src_label = node_by_id.get(jwt_edges[0]["source"], "")
    assert "buildContext" in src_label, \
        f"Expected buildContext() as source of jwt.decode call, got: {src_label}"


def test_ts_require_no_relative_bindings():
    """require('./local') should not produce an import binding."""
    from graphify.extract import _collect_js_import_bindings
    import tree_sitter_typescript as tsts
    from tree_sitter import Language, Parser
    source = b"const local = require('./local'); local.fn();"
    lang = Language(tsts.language_typescript())
    parser = Parser(lang)
    tree = parser.parse(source)
    bindings = _collect_js_import_bindings(tree.root_node, source)
    assert "local" not in bindings, \
        f"Relative require should not produce a binding, got: {bindings}"

