# linkedin-content-manager

[![CI](https://github.com/amasen02/linkedin-content-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/amasen02/linkedin-content-manager/actions/workflows/ci.yml)
[![CodeQL](https://github.com/amasen02/linkedin-content-manager/actions/workflows/codeql.yml/badge.svg)](https://github.com/amasen02/linkedin-content-manager/actions/workflows/codeql.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-blue)](CODE_OF_CONDUCT.md)

A small, zero-dependency CLI that stages LinkedIn posts through a review lifecycle —
draft → pending review → approved → posted — for a human to read, edit, and post
themselves. It **never** posts to LinkedIn, and it structurally cannot: there is no
LinkedIn API client anywhere in this codebase.

## Why this tool doesn't post for you

LinkedIn's Terms of Service prohibit automating actions, including posting, on a
personal account. Most "LinkedIn automation" tools either ignore that or rely on
fragile unofficial endpoints that get accounts flagged. This one takes the opposite
approach: it only ever manages local files, and a dedicated test enforces that as an
architectural invariant rather than a promise.

- **Zero runtime dependencies.** Standard library only — `argparse`, `dataclasses`,
  `json`, `pathlib`.
- **Zero network access, provably.** [`tests/test_no_network.py`](tests/test_no_network.py)
  parses every source file with Python's `ast` module and fails the build if any
  networking import (`socket`, `urllib`, `http`, `requests`, `httpx`, `aiohttp`,
  `ftplib`, `smtplib`, `telnetlib`) ever appears under `src/linkedin_content_manager/`.
  This isn't a comment promising good behaviour — it's a test that catches a future
  regression the moment someone adds one of those imports.
- **A real review lifecycle**, not just a text file. Every draft moves through
  explicit states with illegal transitions rejected (you cannot jump straight from
  `draft` to `posted`; `posted` is terminal).

## Install

Requires **Python 3.11+**. No third-party packages are needed to run it.

```bash
git clone https://github.com/amasen02/linkedin-content-manager.git
cd linkedin-content-manager
pip install -e .
```

Or run it directly from source without installing:

```bash
PYTHONPATH=src python -m linkedin_content_manager --help
```

## Review lifecycle

```
draft ──────► pending_review ──────► approved ──────► posted   (terminal)
  │                 │                    │
  └──────────────► archived ◄────────────┘
                     │
                     └──────► draft   (reopen)
```

`new` stages a draft directly into `pending_review` — the assumption is that content
you're staging with this tool is already meant for review, not further drafting.
`posted` can only be reached from `approved`, and once there it cannot be transitioned
anywhere else; the record is permanent.

## Usage

```bash
# Stage a new draft for review (source-repo and hashtags are optional):
echo "We shipped DupeSweep's quarantine + restore flow today." > /tmp/body.txt
python -m linkedin_content_manager new \
  --title "DupeSweep quarantine launch" \
  --body-file /tmp/body.txt \
  --source-repo https://github.com/amasen02/dupesweep \
  --hashtags dotnet,opensource,cli

# staged dupesweep-quarantine-launch-a1b2c3d4 (status=pending_review, 58 chars)

# List everything staged, optionally filtered by status:
python -m linkedin_content_manager list
python -m linkedin_content_manager list --status pending_review

# Print the exact text to copy into LinkedIn's own post composer:
python -m linkedin_content_manager show dupesweep-quarantine-launch-a1b2c3d4

# Approve it for posting:
python -m linkedin_content_manager approve dupesweep-quarantine-launch-a1b2c3d4

# After YOU post it manually on linkedin.com, record that it happened:
python -m linkedin_content_manager mark-posted dupesweep-quarantine-launch-a1b2c3d4 \
  --url https://www.linkedin.com/feed/update/urn:li:activity:1234567890

# Decide not to post something after all:
python -m linkedin_content_manager archive dupesweep-quarantine-launch-a1b2c3d4
```

Every command accepts a top-level `--staging-dir` flag (default: `content/staging`),
placed *before* the subcommand, e.g. `linkedin-content-manager --staging-dir /path new ...`,
to point at a different store. Each draft is written as a `<id>.json` record (the full
state) and a companion `<id>.md` snapshot (a human-readable copy/paste view) under that
directory.

### Content constraints

| Constraint | Value | Enforcement |
|---|---|---|
| Body + hashtags length | 3000 characters | Hard limit — `new` rejects anything longer, matching LinkedIn's own cap on personal-feed posts. |
| "See more" truncation | ~210 characters | Soft warning only — LinkedIn doesn't publish the exact mobile truncation point and it can change, so `new` prints a note rather than blocking you. |

## Docker

```bash
docker build -t linkedin-content-manager .
docker run --rm -v "$(pwd)/content:/app/content" linkedin-content-manager \
  --staging-dir content/staging new --title "Example" --body-file content/example-body.txt
docker run --rm -v "$(pwd)/content:/app/content" linkedin-content-manager \
  --staging-dir content/staging list
```

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

`tests/test_no_network.py` is the one test that matters most architecturally — every
other test can fail loudly during development, but this one exists specifically to
catch a *silent* regression of the tool's core promise.

## Architecture (separation of concerns)

```
src/linkedin_content_manager/
  models.py       PostDraft dataclass, PostStatus enum, the legal-transition table
  store.py        DraftStore — file-backed CRUD + lifecycle transitions, one JSON+MD pair per draft
  exceptions.py   ContentManagerError, DraftNotFoundError, InvalidTransitionError, DraftValidationError
  __main__.py     argparse CLI: new, list, show, approve, mark-posted, archive
tests/
  test_models.py      PostDraft rendering, character counting, dict round-trip
  test_store.py       CRUD + every lifecycle transition, legal and illegal
  test_cli.py          end-to-end CLI flows against a temp staging directory
  test_no_network.py    static AST scan — no networking import may ever appear in src/
```

## Contributing

Contributions are welcome — bug fixes, new lifecycle states, better docs. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow, the coding bar, and the one
non-negotiable rule (no networking imports, ever). Please be mindful of the
[Code of Conduct](CODE_OF_CONDUCT.md). Use the issue templates; green CI is required on
every pull request. Report security issues privately per [`SECURITY.md`](SECURITY.md) —
never as a public issue.

## Open source commitments

This project is, and will remain, free and open source. As maintainer I commit to:

- **A permissive licence, kept stable.** [MIT](LICENSE) — use it commercially, fork it, build on
  it. No relicensing of accepted contributions.
- **No CLA.** Contributions are accepted under the MIT licence; you keep the copyright to your work.
- **An honest history.** Real, walkable commits — no fabricated activity, no rewritten releases.
- **Best-effort, transparent triage.** Issues and pull requests are read and answered; security
  reports are acknowledged within 72 hours.
- **A welcoming community** governed by the [Code of Conduct](CODE_OF_CONDUCT.md).
- **Reproducible builds.** Green CI — tests on two OSes and CodeQL security analysis — on every change.

## License

MIT — see [`LICENSE`](LICENSE). You are free to use, modify, and distribute this software,
including for commercial purposes, provided the copyright notice is retained.

## Author

**Ama Senevirathne** — [GitHub](https://github.com/amasen02)
