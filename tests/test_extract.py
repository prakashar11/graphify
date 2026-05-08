from pathlib import Path
from graphify.extract import extract_python, extract, collect_files, _make_id

FIXTURES = Path(__file__).parent / "fixtures"


def test_make_id_strips_dots_and_underscores():
    assert _make_id("_auth") == "auth"
    assert _make_id(".httpx._client") == "httpx_client"


def test_make_id_consistent():
    """Same input always produces same output."""
    assert _make_id("foo", "Bar") == _make_id("foo", "Bar")


def test_make_id_no_leading_trailing_underscores():
    result = _make_id("__init__")
    assert not result.startswith("_")
    assert not result.endswith("_")


def test_extract_python_finds_class():
    result = extract_python(FIXTURES / "sample.py")
    labels = [n["label"] for n in result["nodes"]]
    assert "Transformer" in labels


def test_extract_python_finds_methods():
    result = extract_python(FIXTURES / "sample.py")
    labels = [n["label"] for n in result["nodes"]]
    assert any("__init__" in l or "forward" in l for l in labels)


def test_extract_python_no_dangling_edges():
    """All edge sources must reference a known node (targets may be external imports)."""
    result = extract_python(FIXTURES / "sample.py")
    node_ids = {n["id"] for n in result["nodes"]}
    for edge in result["edges"]:
        assert edge["source"] in node_ids, f"Dangling source: {edge['source']}"


def test_structural_edges_are_extracted():
    """contains / method / inherits / imports edges must always be EXTRACTED."""
    result = extract_python(FIXTURES / "sample.py")
    structural = {"contains", "method", "inherits", "imports", "imports_from"}
    for edge in result["edges"]:
        if edge["relation"] in structural:
            assert edge["confidence"] == "EXTRACTED", f"Expected EXTRACTED: {edge}"


def test_extract_merges_multiple_files():
    files = list(FIXTURES.glob("*.py"))
    result = extract(files)
    assert len(result["nodes"]) > 0
    assert result["input_tokens"] == 0


def test_collect_files_from_dir():
    files = collect_files(FIXTURES)
    supported = {".py", ".js", ".ts", ".tsx", ".go", ".rs",
                 ".java", ".c", ".cpp", ".cc", ".cxx", ".rb",
                 ".cs", ".kt", ".kts", ".scala", ".php", ".h", ".hpp",
                 ".swift", ".lua", ".toc", ".zig", ".ps1", ".ex", ".exs",
                 ".m", ".mm"}
    assert all(f.suffix in supported for f in files)
    assert len(files) > 0


def test_collect_files_skips_hidden():
    files = collect_files(FIXTURES)
    for f in files:
        assert not any(part.startswith(".") for part in f.parts)


def test_collect_files_follows_symlinked_directory(tmp_path):
    real_dir = tmp_path / "real_src"
    real_dir.mkdir()
    (real_dir / "lib.py").write_text("x = 1")
    (tmp_path / "linked_src").symlink_to(real_dir)

    files_no = collect_files(tmp_path, follow_symlinks=False)
    files_yes = collect_files(tmp_path, follow_symlinks=True)

    assert [f.name for f in files_no].count("lib.py") == 1
    assert [f.name for f in files_yes].count("lib.py") == 2


def test_collect_files_handles_circular_symlinks(tmp_path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "mod.py").write_text("x = 1")
    (sub / "cycle").symlink_to(tmp_path)

    files = collect_files(tmp_path, follow_symlinks=True)
    assert any(f.name == "mod.py" for f in files)


def test_no_dangling_edges_on_extract():
    """After merging multiple files, no internal edges should be dangling."""
    files = list(FIXTURES.glob("*.py"))
    result = extract(files)
    node_ids = {n["id"] for n in result["nodes"]}
    internal_relations = {"contains", "method", "inherits", "calls"}
    for edge in result["edges"]:
        if edge["relation"] in internal_relations:
            assert edge["source"] in node_ids, f"Dangling source: {edge}"
            assert edge["target"] in node_ids, f"Dangling target: {edge}"


def test_calls_edges_emitted():
    """Call-graph pass must produce INFERRED calls edges."""
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = [e for e in result["edges"] if e["relation"] == "calls"]
    assert len(calls) > 0, "Expected at least one calls edge"


def test_calls_edges_are_extracted():
    """AST-resolved call edges are deterministic and should be EXTRACTED/1.0."""
    result = extract_python(FIXTURES / "sample_calls.py")
    for edge in result["edges"]:
        if edge["relation"] == "calls":
            assert edge["confidence"] == "EXTRACTED"
            assert edge["weight"] == 1.0


def test_python_call_edges_have_call_context():
    result = extract_python(FIXTURES / "sample_calls.py")
    call_edges = [e for e in result["edges"] if e["relation"] == "calls"]
    assert call_edges
    assert all(e.get("context") == "call" for e in call_edges)


def test_calls_no_self_loops():
    result = extract_python(FIXTURES / "sample_calls.py")
    for edge in result["edges"]:
        if edge["relation"] == "calls":
            assert edge["source"] != edge["target"], f"Self-loop: {edge}"


def test_run_analysis_calls_compute_score():
    """run_analysis() calls compute_score() - must appear as a calls edge."""
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    src = node_by_label.get("run_analysis()")
    tgt = node_by_label.get("compute_score()")
    assert src and tgt, "run_analysis or compute_score node not found"
    assert (src, tgt) in calls, f"run_analysis -> compute_score not found in {calls}"


def test_run_analysis_calls_normalize():
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    src = node_by_label.get("run_analysis()")
    tgt = node_by_label.get("normalize()")
    assert src and tgt
    assert (src, tgt) in calls


def test_method_calls_module_function():
    """Analyzer.process() calls run_analysis() - cross class→function calls edge."""
    result = extract_python(FIXTURES / "sample_calls.py")
    calls = {(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"}
    node_by_label = {n["label"]: n["id"] for n in result["nodes"]}
    src = node_by_label.get(".process()")
    tgt = node_by_label.get("run_analysis()")
    assert src and tgt
    assert (src, tgt) in calls


def test_calls_deduplication():
    """Same caller→callee pair must appear only once even if called multiple times."""
    result = extract_python(FIXTURES / "sample_calls.py")
    call_pairs = [(e["source"], e["target"]) for e in result["edges"] if e["relation"] == "calls"]
    assert len(call_pairs) == len(set(call_pairs)), "Duplicate calls edges found"


def test_cross_file_calls_skip_ambiguous_duplicate_labels(tmp_path):
    """Unqualified cross-file calls must not guess between duplicate helper names."""
    caller = tmp_path / "caller.py"
    helper_a = tmp_path / "a.py"
    helper_b = tmp_path / "b.py"
    caller.write_text("def run():\n    log()\n")
    helper_a.write_text("def log():\n    return 'a'\n")
    helper_b.write_text("def log():\n    return 'b'\n")

    result = extract([caller, helper_a, helper_b], cache_root=tmp_path)
    nodes = {n["id"]: n for n in result["nodes"]}
    calls = [
        e for e in result["edges"]
        if e["relation"] == "calls" and e["confidence"] == "INFERRED"
    ]

    assert not any(
        nodes[e["source"]]["label"] == "run()" and nodes[e["target"]]["label"] == "log()"
        for e in calls
    )


# ── Python argument reference tracking ───────────────────────────────────────

def test_python_arg_ref_positional():
    """pass_around(build_context) should produce a references edge with numeric arg_key."""
    r = extract_python(FIXTURES / "arg_refs.py")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    targets = {node_by_id.get(e["target"], "") for e in ref_edges}
    assert any("build_context" in t for t in targets), \
        f"Expected references edge to build_context, got: {targets}"
    positional = [e for e in ref_edges
                  if "build_context" in node_by_id.get(e["target"], "")
                  and isinstance(e.get("arg_key"), int)]
    assert positional, "Expected numeric arg_key for positional reference"
    assert positional[0]["arg_key"] == 0


def test_python_arg_ref_keyword():
    """GraphQLSchema(context=build_context) should produce a references edge with arg_key='context'."""
    r = extract_python(FIXTURES / "arg_refs.py")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    named = [e for e in ref_edges
             if "build_context" in node_by_id.get(e["target"], "")
             and e.get("arg_key") == "context"]
    assert named, \
        f"Expected references edge with arg_key='context', got arg_keys: " \
        f"{[e.get('arg_key') for e in ref_edges if 'build_context' in node_by_id.get(e['target'], '')]}"


def test_python_arg_ref_caller_is_function():
    """Source of the references edge should be the enclosing function, not the file node."""
    r = extract_python(FIXTURES / "arg_refs.py")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "build_context" in n["label"]), None)
    assert build_ctx_nid, "build_context node not found"
    edges_to_ctx = [e for e in ref_edges if e["target"] == build_ctx_nid]
    assert edges_to_ctx, "No references edges to build_context"
    sources = {node_by_id.get(e["source"], "") for e in edges_to_ctx}
    assert any(s not in ("", "arg_refs.py") for s in sources), \
        f"Expected function-level source, got: {sources}"


def test_python_arg_ref_no_self_loops():
    """No references edge should have source == target."""
    r = extract_python(FIXTURES / "arg_refs.py")
    self_loops = [e for e in r["edges"]
                  if e["relation"] == "references" and e["source"] == e["target"]]
    assert not self_loops, f"Self-referencing edges found: {self_loops}"


def test_python_arg_ref_confidence():
    """In-file arg references should have EXTRACTED confidence."""
    r = extract_python(FIXTURES / "arg_refs.py")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    assert ref_edges, "Expected at least one arg_ref references edge"
    assert all(e["confidence"] == "EXTRACTED" for e in ref_edges)


def test_python_dict_literal_as_positional_arg():
    """foo({'context': build_context}) — dict literal as positional call arg should
    produce a references edge with arg_key='context' (Gap 1)."""
    r = extract_python(FIXTURES / "arg_refs.py")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "build_context" in n["label"]), None)
    assert build_ctx_nid, "build_context node not found"
    dict_arg_edges = [e for e in ref_edges
                      if e["target"] == build_ctx_nid
                      and e.get("arg_key") == "context"
                      and "build_server_dict_arg" in node_by_id.get(e["source"], "")]
    assert dict_arg_edges, (
        f"Expected build_server_dict_arg → references(context) → build_context via dict arg. "
        f"All arg_ref edges to build_context: "
        f"{[(node_by_id.get(e['source']), e.get('arg_key')) for e in ref_edges if e['target'] == build_ctx_nid]}"
    )


def test_python_dict_return_value():
    """def build_config(): return {'context': build_context} — dict in return value
    should produce build_config → references(context) → build_context (Gap 2)."""
    r = extract_python(FIXTURES / "arg_refs.py")
    ref_edges = [e for e in r["edges"] if e["relation"] == "references"
                 and e.get("context") == "arg_ref"]
    node_by_id = {n["id"]: n["label"] for n in r["nodes"]}
    build_ctx_nid = next((n["id"] for n in r["nodes"] if "build_context" in n["label"]), None)
    assert build_ctx_nid, "build_context node not found"
    return_dict_edges = [e for e in ref_edges
                         if e["target"] == build_ctx_nid
                         and e.get("arg_key") == "context"
                         and "build_config" in node_by_id.get(e["source"], "")]
    assert return_dict_edges, (
        f"Expected build_config → references(context) → build_context via return dict. "
        f"All arg_ref edges to build_context: "
        f"{[(node_by_id.get(e['source']), e.get('arg_key')) for e in ref_edges if e['target'] == build_ctx_nid]}"
    )
