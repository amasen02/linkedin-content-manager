# Contributing to linkedin-content-manager

Pull requests are welcome — bug fixes, new lifecycle states, better docs — provided
they keep the tone, quality, and the one hard architectural rule of this codebase.

## Ground rules

1. **One concern per pull request.** No drive-by refactors mixed with feature work.
2. **Branch from `master`**, keep the branch short, and squash-merge back.
3. **Conventional commits** (`feat:`, `fix:`, `perf:`, `refactor:`, `test:`, `docs:`, `chore:`).
4. **Green CI is non-negotiable.** The unit test suite must pass on Ubuntu and Windows before review.
5. **The PR template must be filled.** Empty checkboxes block review.

## The one hard rule: no network access, ever

This tool exists to stage LinkedIn posts for a human to review and post by hand —
never to post automatically. LinkedIn's Terms of Service prohibit automating actions
on a personal account, so **no pull request may add an import of a networking module**
(`socket`, `urllib`, `http`, `requests`, `httpx`, `aiohttp`, or similar) anywhere under
`src/linkedin_content_manager/`. `tests/test_no_network.py` enforces this with a static
AST scan and will fail CI if violated. A PR that touches this constraint will not be merged.

## Coding standards

- **Python 3.11+, standard library only.** No runtime dependencies — that is a
  deliberate design constraint, not an oversight.
- **Type hints on every public function.**
- **Intention-revealing names.** Full descriptive identifiers; `c`, `tmp`, `mgr` are rejected.
- **Comments explain *why*, never *what*.** No filler comments.
- **SOLID / KISS / DRY / YAGNI.** One responsibility per module; the simplest correct solution wins.

## Build, test, run

```bash
PYTHONPATH=src python -m unittest discover -s tests -v   # unit tests
echo "Hello LinkedIn" > /tmp/body.txt
python -m linkedin_content_manager new --title "Example" --body-file /tmp/body.txt
python -m linkedin_content_manager list
```

## Tests

A pull request that ships behaviour without a test is sent back unless it is purely
documentation. Any new lifecycle transition needs both a positive test (the
transition succeeds) and a negative test (an illegal transition is rejected).

## Reporting bugs and proposing features

Use the issue templates. For security vulnerabilities, **do not open a public issue** —
follow [`SECURITY.md`](SECURITY.md).
