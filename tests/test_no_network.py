"""Enforces the one architectural rule of this package: no source file may import
anything capable of opening a network connection, shelling out, or loading code
that this scan cannot see.

LinkedIn's Terms of Service prohibit automating actions (including posting) on a
personal account, so this tool never talks to LinkedIn — a human copies each
approved draft into LinkedIn's own composer and posts it.

The check is an **allowlist**: every module imported under
``src/linkedin_content_manager/`` must appear in ``PERMITTED_MODULES`` below, and
no source file may name one of the builtins that loads or runs code chosen at
runtime. A denylist of known networking modules would wave through a file that
shelled out via ``subprocess``, opened a socket through ``asyncio``, or resolved
``socket`` by string with ``importlib.import_module`` — none of which produce a
matching import name. An allowlist fails closed on all of those, and on whatever
the next escape hatch turns out to be.

Scope, so the guarantee is not overstated: this is a static scan of the import
statements in ``src/``. It is not a runtime sandbox, and it does not cover the
test suite, the packaging metadata, or the container image.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

PACKAGE_NAME = "linkedin_content_manager"

#: Every module the package is allowed to import. Adding an entry here is the
#: only way to widen the tool's reach, which makes it a deliberate, reviewable act.
PERMITTED_MODULES = frozenset(
    {
        "__future__",
        "argparse",
        "dataclasses",
        "datetime",
        "enum",
        "json",
        "pathlib",
        "re",
        "sys",
        "uuid",
        PACKAGE_NAME,
    }
)

#: Builtins that load or execute code selected at runtime. A source file using one
#: of these could reach a networking module without ever naming it in an import.
FORBIDDEN_BUILTINS = frozenset({"__import__", "eval", "exec", "compile"})

#: The allowlist is the whole guarantee, so it is itself guarded: none of these may
#: be added to it, whatever the justification in the pull request that proposes it.
NEVER_PERMITTED_MODULES = frozenset(
    {
        "aiohttp",
        "asyncio",
        "ctypes",
        "ftplib",
        "http",
        "httpx",
        "imaplib",
        "importlib",
        "multiprocessing",
        "nntplib",
        "os",
        "poplib",
        "requests",
        "smtplib",
        "socket",
        "socketserver",
        "ssl",
        "subprocess",
        "telnetlib",
        "urllib",
        "webbrowser",
        "xmlrpc",
    }
)

SOURCE_ROOT = Path(__file__).resolve().parent.parent / "src" / PACKAGE_NAME


def _source_files() -> list[Path]:
    return sorted(SOURCE_ROOT.rglob("*.py"))


def _parse(source_path: Path) -> ast.Module:
    return ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))


def _imported_roots(tree: ast.Module) -> set[str]:
    """Top-level package of every import, so ``urllib.request`` reports ``urllib``."""
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # A relative import can only resolve inside this package.
                roots.add(PACKAGE_NAME)
            elif node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def _code_loading_builtins(tree: ast.Module) -> set[str]:
    return {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_BUILTINS
    }


class NoNetworkAccessTests(unittest.TestCase):
    def test_source_files_are_actually_scanned(self) -> None:
        self.assertGreater(
            len(_source_files()),
            0,
            f"found no source files under {SOURCE_ROOT}; the scan below would pass vacuously",
        )

    def test_every_import_is_on_the_allowlist(self) -> None:
        violations: dict[str, set[str]] = {}
        for path in _source_files():
            unexpected = _imported_roots(_parse(path)) - PERMITTED_MODULES
            if unexpected:
                violations[str(path.relative_to(SOURCE_ROOT))] = unexpected

        self.assertEqual(
            violations,
            {},
            f"{PACKAGE_NAME} may only import {sorted(PERMITTED_MODULES)} "
            "(LinkedIn ToS forbids automated posting on a personal account, so this "
            "package stays incapable of reaching the network or shelling out): "
            f"{violations}",
        )

    def test_no_source_file_loads_code_at_runtime(self) -> None:
        violations: dict[str, set[str]] = {}
        for path in _source_files():
            found = _code_loading_builtins(_parse(path))
            if found:
                violations[str(path.relative_to(SOURCE_ROOT))] = found

        self.assertEqual(
            violations,
            {},
            "no source file may use __import__/eval/exec/compile — they would let a "
            "forbidden module be reached without naming it in an import: "
            f"{violations}",
        )

    def test_allowlist_never_admits_a_networking_or_code_loading_module(self) -> None:
        self.assertEqual(
            PERMITTED_MODULES & NEVER_PERMITTED_MODULES,
            frozenset(),
            "PERMITTED_MODULES has been widened to include a module that can open a "
            "connection, spawn a process, or import by string; that defeats the scan.",
        )


if __name__ == "__main__":
    unittest.main()
