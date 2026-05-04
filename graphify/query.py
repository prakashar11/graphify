"""Type-based structural queries for Graphify.

Enables queries like:
- "list all functions with uint16_t return type"
- "find all functions with char* parameters"
- "show classes with String fields"

This is PURE structural extraction — not vulnerability analysis. Type metadata
is extracted from AST nodes and stored as node attributes, enabling filtering
without semantic inference.
"""
from __future__ import annotations
import re
import networkx as nx


def _type_matches(node_attr: dict, pattern: str) -> bool:
    """Check if a node's type attribute matches a pattern.

    Supports:
    - Exact match: "uint16_t"
    - Substring: "int" matches "int", "uint16_t", "char*"
    - Regex: r"\\w+\\*" matches all pointer types
    - Type family: "pointer" matches any * type
    """
    # Check return_type
    return_type = node_attr.get("return_type")
    if return_type:
        if _check_type_match(return_type, pattern):
            return True

    # Check parameters
    params = node_attr.get("parameters", [])
    for param in params:
        param_type = param.get("type")
        if param_type and _check_type_match(param_type, pattern):
            return True

    # Check fields (for class nodes)
    fields = node_attr.get("fields", [])
    for field in fields:
        field_type = field.get("type")
        if field_type and _check_type_match(field_type, pattern):
            return True

    return False


def _check_type_match(type_str: str, pattern: str) -> bool:
    """Check if a type string matches a pattern."""
    if not type_str or not pattern:
        return False

    # Type family match
    if pattern == "pointer":
        return "*" in type_str
    if pattern == "array":
        return "[]" in type_str or "array" in type_str.lower()
    if pattern == "reference":
        return "&" in type_str
    if pattern == "integer":
        # Match integer types including fixed-width variants (int, uint16_t, int32_t, etc.)
        # Use word boundary at start and flexible matching at end for suffixes like _t
        return bool(re.search(r"\b(int|uint|long|short|char)(\d+_t|_t|\d*)?\b", type_str, re.IGNORECASE))
    if pattern == "float":
        return bool(re.search(r"\b(float|double)\b", type_str, re.IGNORECASE))
    if pattern == "string":
        # Fixed: char* match uses substring check since \b before * doesn't work
        return "char*" in type_str or bool(re.search(r"\b(string|std::string)\b", type_str, re.IGNORECASE))

    # Regex pattern
    if pattern.startswith("/") and pattern.endswith("/"):
        regex = pattern[1:-1]  # Strip slashes
        try:
            return bool(re.search(regex, type_str))
        except re.error:
            return False

    # Substring match (case-insensitive)
    return pattern.lower() in type_str.lower()


def filter_by_type(G: nx.Graph, type_pattern: str) -> list[dict]:
    """Filter nodes that have a type attribute matching the pattern.

    Args:
        G: NetworkX graph
        type_pattern: Type pattern to match (e.g., "uint16_t", "char*", "int*")

    Returns:
        List of node dicts with matching type attributes
    """
    results = []
    for node_id, attrs in G.nodes(data=True):
        # Skip nodes with no type metadata (e.g. plain file nodes, semantic nodes)
        if not (attrs.get("return_type") or attrs.get("parameters") or attrs.get("fields")):
            continue

        if _type_matches(attrs, type_pattern):
            results.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "return_type": attrs.get("return_type"),
                "parameters": attrs.get("parameters", []),
                "fields": attrs.get("fields", []),
                "source_file": attrs.get("source_file", ""),
                "source_location": attrs.get("source_location", ""),
            })

    return results


def find_functions_with_return_type(G: nx.Graph, return_type: str) -> list[dict]:
    """Find all functions with a specific return type.

    Args:
        G: NetworkX graph
        return_type: Return type to match (e.g., "uint16_t", "char*")

    Returns:
        List of function node dicts
    """
    results = []
    for node_id, attrs in G.nodes(data=True):
        # Only function/method nodes (have "()" in label)
        if "()" not in attrs.get("label", ""):
            continue

        node_return_type = attrs.get("return_type")
        if node_return_type and _check_type_match(node_return_type, return_type):
            results.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "return_type": node_return_type,
                "parameters": attrs.get("parameters", []),
                "source_file": attrs.get("source_file", ""),
                "source_location": attrs.get("source_location", ""),
            })

    return results


def find_functions_with_parameter_type(G: nx.Graph, param_type: str) -> list[dict]:
    """Find all functions with at least one parameter of a specific type.

    Args:
        G: NetworkX graph
        param_type: Parameter type to match (e.g., "char*", "uint8_t")

    Returns:
        List of function node dicts
    """
    results = []
    for node_id, attrs in G.nodes(data=True):
        # Only function/method nodes
        if "()" not in attrs.get("label", ""):
            continue

        params = attrs.get("parameters", [])
        matching_params = [p for p in params if _check_type_match(p.get("type", ""), param_type)]

        if matching_params:
            results.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "return_type": attrs.get("return_type"),
                "parameters": attrs.get("parameters", []),
                "matching_parameters": matching_params,
                "source_file": attrs.get("source_file", ""),
                "source_location": attrs.get("source_location", ""),
            })

    return results


def find_classes_with_field_type(G: nx.Graph, field_type: str) -> list[dict]:
    """Find all classes with at least one field of a specific type.

    Args:
        G: NetworkX graph
        field_type: Field type to match (e.g., "String", "int", "char*")

    Returns:
        List of class node dicts
    """
    results = []
    for node_id, attrs in G.nodes(data=True):
        # Only class nodes (no "()" in label, has fields)
        if "()" in attrs.get("label", ""):
            continue

        fields = attrs.get("fields", [])
        matching_fields = [f for f in fields if _check_type_match(f.get("type", ""), field_type)]

        if matching_fields:
            results.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "fields": attrs.get("fields", []),
                "matching_fields": matching_fields,
                "source_file": attrs.get("source_file", ""),
                "source_location": attrs.get("source_location", ""),
            })

    return results


def list_all_types(G: nx.Graph) -> dict:
    """List all unique types found in the graph.

    Returns:
        Dict with keys:
            - return_types: list of unique return types
            - param_types: list of unique parameter types
            - field_types: list of unique field types
    """
    return_types: set = set()
    param_types: set = set()
    field_types: set = set()

    for node_id, attrs in G.nodes(data=True):
        # Return types
        ret = attrs.get("return_type")
        if ret:
            return_types.add(ret)

        # Parameter types
        for param in attrs.get("parameters", []):
            ptype = param.get("type")
            if ptype:
                param_types.add(ptype)

        # Field types
        for field in attrs.get("fields", []):
            ftype = field.get("type")
            if ftype:
                field_types.add(ftype)

    return {
        "return_types": sorted(return_types),
        "param_types": sorted(param_types),
        "field_types": sorted(field_types),
    }


def query(G: nx.Graph, query_str: str) -> list[dict]:
    """Parse and execute a type-based query string.

    Supported query formats:
    - "functions with uint16_t return type"
    - "functions with char* parameter"
    - "classes with String field"
    - "all types"

    Args:
        G: NetworkX graph
        query_str: Natural language query

    Returns:
        List of matching node dicts
    """
    query_lower = query_str.lower().strip()

    # "all types"
    if query_lower in ("all types", "list all types", "show all types"):
        type_summary = list_all_types(G)
        return [{
            "type": "summary",
            "return_types": type_summary["return_types"],
            "param_types": type_summary["param_types"],
            "field_types": type_summary["field_types"],
        }]

    # "functions with <type> return type"
    match = re.match(r"functions?\s+with\s+(.+?)\s+(?:return\s+)?type", query_lower)
    if match:
        type_pattern = match.group(1).strip()
        return find_functions_with_return_type(G, type_pattern)

    # "functions with <type> parameter"
    match = re.match(r"functions?\s+with\s+(.+?)\s+(?:a\s+)?(?:param|argument)", query_lower)
    if match:
        type_pattern = match.group(1).strip()
        return find_functions_with_parameter_type(G, type_pattern)

    # "classes with <type> field"
    match = re.match(r"classes?\s+with\s+(.+?)\s+(?:a\s+)?(?:field|property)", query_lower)
    if match:
        type_pattern = match.group(1).strip()
        return find_classes_with_field_type(G, type_pattern)

    # Generic type filter — extract everything after "with"
    if "with" in query_lower:
        type_pattern = query_lower.split("with", 1)[1].strip()
        return filter_by_type(G, type_pattern)

    return []
