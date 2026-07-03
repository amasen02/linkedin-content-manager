"""Enforces the one non-negotiable architectural property of this package:

LinkedIn's Terms of Service prohibit automating actions (including posting) on
a personal account. This tool must therefore be *structurally* incapable of
making a network call — not just documented as not doing so. This test scans
every source file for imports of networking modules and fails the build if
any appear, so the constraint cannot be silently violated by a future change.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

FORBIDDEN_MODULES = frozenset(
    {
        "socket",
        "urllib",
        "urllib.request",
        "http",
        "http.client",
        "requests",
        "httpx",
        "aiohttp",
        "ftplib",
        "smtplib",
        "telnetlib",
    }
)

SOURCE_ROOT = Path(__file__).resolve().parent.parent / "src" / "linkedin_content_manager"


def _imported_modules(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


class NoNetworkAccessTests(unittest.TestCase):
    def test_no_source_file_imports_a_networking_module(self) -> None:
        source_files = sorted(SOURCE_ROOT.rglob("*.py"))
        self.assertGreater(len(source_files), 0, "expected to find source files to scan")

        violations: dict[str, set[str]] = {}
        for path in source_files:
            found = _imported_modules(path) & FORBIDDEN_MODULES
            if found:
                violations[str(path.relative_to(SOURCE_ROOT))] = found

        self.assertEqual(
            violations,
            {},
            "linkedin_content_manager must never import a networking module "
            "(LinkedIn ToS forbids automated posting on a personal account): "
            f"{violations}",
        )


if __name__ == "__main__":
    unittest.main()
