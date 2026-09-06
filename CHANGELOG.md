# Changelog

All notable changes to linkedin-content-manager are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- `tests/test_no_network.py` now enforces the no-network rule with an allowlist of
  permitted standard-library imports instead of a list of ten banned networking
  modules. The old denylist passed a source file that shelled out with `subprocess`,
  opened a connection through `asyncio`, or resolved `socket` by string via
  `importlib`/`__import__`; the allowlist fails closed on all of those.
- README, SECURITY.md and CONTRIBUTING.md now describe what that check actually
  guarantees — a static scan of imports under `src/`, run in CI — instead of claiming
  the tool is provably or structurally incapable of network access.

## [1.0.0] - 2026-07-03

### Added
- Initial release of linkedin-content-manager (1.0.0).
- CLI with a rich TUI for staging, reviewing, and approving LinkedIn posts before manual submission.
- Post lifecycle: draft to review to approved to posted, with metadata tracked locally.
- Zero runtime dependencies beyond Python 3.10+.
- Docker support: multi-stage Dockerfile for reproducible cross-platform usage.
- GitHub Actions CI: linting (ruff) and test suite on every push and pull request.
- Full open-source community profile: LICENSE (MIT), CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md.
