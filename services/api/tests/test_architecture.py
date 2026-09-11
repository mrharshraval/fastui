"""Automated Architectural Boundaries and Dependency Integrity Tests.

Verifies using Python AST:
1. Complete elimination of legacy packages (core, models, routes, schemas, services, utils).
2. Complete absence of unwanted dependency on services/worker.
3. Strict unidirectional acyclic layering:
   - shared has zero dependencies on domains, infrastructure, or api.
   - infrastructure has zero dependencies on domains or api.
   - domains has zero dependencies on api.
"""

import ast
import os
from pathlib import Path

APP_DIR = Path(__file__).parent.parent / "app"
TESTS_DIR = Path(__file__).parent
FORBIDDEN_LEGACY_MODULES = {"core", "models", "routes", "schemas", "services", "utils", "worker"}


def _get_all_python_files(directory: Path):
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def _extract_imported_modules(file_path: Path):
    with open(file_path, encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError:
            return []

    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)
    return imported


def test_zero_legacy_and_worker_imports():
    """Ensures no file in app/ or tests/ imports legacy modules or worker."""
    violations = []
    all_files = list(_get_all_python_files(APP_DIR)) + list(_get_all_python_files(TESTS_DIR))

    for py_file in all_files:
        imported = _extract_imported_modules(py_file)
        for mod in imported:
            root_mod = mod.split(".")[0]
            if root_mod in FORBIDDEN_LEGACY_MODULES:
                violations.append(f"{py_file.name}: imports forbidden '{mod}'")

    assert not violations, "Forbidden architectural imports found:\n" + "\n".join(violations)


def test_shared_layer_has_no_higher_layer_dependencies():
    """app/shared must not depend on app.domains, app.infrastructure, or app.api."""
    shared_dir = APP_DIR / "shared"
    violations = []

    for py_file in _get_all_python_files(shared_dir):
        imported = _extract_imported_modules(py_file)
        for mod in imported:
            if (
                mod.startswith("app.domains")
                or mod.startswith("app.infrastructure")
                or mod.startswith("app.api")
            ):
                violations.append(f"{py_file.name}: imports higher layer '{mod}'")

    assert not violations, "Layering violation in shared/:\n" + "\n".join(violations)


def test_infrastructure_layer_has_no_domain_or_api_dependencies():
    """app/infrastructure must not depend on app.domains or app.api."""
    infra_dir = APP_DIR / "infrastructure"
    violations = []

    for py_file in _get_all_python_files(infra_dir):
        imported = _extract_imported_modules(py_file)
        for mod in imported:
            if mod.startswith("app.domains") or mod.startswith("app.api"):
                violations.append(f"{py_file.name}: imports higher layer '{mod}'")

    assert not violations, "Layering violation in infrastructure/:\n" + "\n".join(violations)


def test_domains_layer_has_no_api_dependencies():
    """app/domains must not depend on app.api."""
    domains_dir = APP_DIR / "domains"
    violations = []

    for py_file in _get_all_python_files(domains_dir):
        imported = _extract_imported_modules(py_file)
        for mod in imported:
            if mod.startswith("app.api"):
                violations.append(f"{py_file.name}: imports higher layer '{mod}'")

    assert not violations, "Layering violation in domains/:\n" + "\n".join(violations)


def test_no_public_api_directory():
    """Ensures app/api/public directory is completely eliminated."""
    public_dir = APP_DIR / "api" / "public"
    assert not public_dir.exists(), f"app/api/public must not exist, found: {public_dir}"


def test_single_canonical_api_namespace():
    """Ensures all application routes reside under /v1 or unversioned /health."""
    from app.main import app

    allowed_non_v1 = {"/health", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}
    for route in app.routes:
        path = getattr(route, "path", None)
        if not path:
            continue
        assert not path.startswith("/public"), f"Route '{path}' must not use /public namespace."
        if path in allowed_non_v1 or path.startswith("/docs"):
            continue
        assert path.startswith("/v1/"), f"Route '{path}' must be under canonical /v1 namespace."

    # Comprehensive schema route validation
    openapi_schema = app.openapi()
    paths = openapi_schema.get("paths", {})
    assert len(paths) > 0, "OpenAPI schema must contain registered endpoints."
    for endpoint in paths:
        assert not endpoint.startswith("/public"), (
            f"Endpoint '{endpoint}' must not contain /public."
        )
        assert not endpoint.endswith("/") and endpoint != "/", (
            f"Endpoint '{endpoint}' must not have a trailing slash."
        )
        if endpoint == "/health":
            continue
        assert endpoint.startswith("/v1/"), f"Endpoint '{endpoint}' must start with /v1/."
