"""Test enforcing import isolation for deterministic safety core modules."""

import ast
import importlib
from pathlib import Path

FORBIDDEN_PACKAGES = frozenset(
    {
        "google",
        "langchain",
        "langgraph",
        "openai",
        "httpx",
        "requests",
        "aiohttp",
        "urllib",
        "socket",
    }
)

CORE_DETERMINISTIC_MODULES = [
    "app.core.text",
    "app.core.helplines",
    "app.core.rule_engine",
    "app.core.safety_gate",
    "app.core.scorer",
    "app.core.validators",
]


def get_ast_imports(file_path: Path) -> set[str]:
    """Extract top-level and direct imported module names from Python AST."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def get_module_closure(module_name: str, visited: set[str] | None = None) -> set[str]:
    """Recursively discover the full import closure of internal app modules."""
    if visited is None:
        visited = set()

    if module_name in visited:
        return visited

    visited.add(module_name)

    # Import the module dynamically to inspect
    mod = importlib.import_module(module_name)
    mod_file = getattr(mod, "__file__", None)
    if not mod_file or not mod_file.endswith(".py"):
        return visited

    direct_imports = get_ast_imports(Path(mod_file))
    for imp in direct_imports:
        # Check if internal app module
        if imp.startswith("app."):
            get_module_closure(imp, visited)
        else:
            visited.add(imp)

    return visited


def test_safety_core_import_isolation() -> None:
    """Deterministic core modules must never import forbidden network or LLM libraries."""
    full_closure: set[str] = set()
    for mod_name in CORE_DETERMINISTIC_MODULES:
        closure = get_module_closure(mod_name)
        full_closure.update(closure)

    violations: list[str] = []
    for mod in sorted(full_closure):
        root_pkg = mod.split(".")[0]
        if root_pkg in FORBIDDEN_PACKAGES:
            violations.append(mod)

    assert not violations, f"Forbidden packages found in safety core import closure: {violations}"
