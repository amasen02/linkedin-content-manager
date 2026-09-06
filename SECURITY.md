# Security policy

linkedin-content-manager makes no outbound network calls. Nothing under
`src/linkedin_content_manager/` imports a module that could make one, and
`tests/test_no_network.py` keeps it that way: it statically parses every source file
with Python's `ast` module and fails the build unless every import is on a short
allowlist — `argparse`, `dataclasses`, `datetime`, `enum`, `json`, `pathlib`, `re`,
`sys`, `uuid`, and the package's own modules — and no file uses `__import__`, `eval`,
`exec`, or `compile`.

## What that check covers, and what it does not

Because it is an allowlist rather than a list of banned modules, it fails closed:
`subprocess`, `asyncio`, `ctypes`, `webbrowser` and a dynamic
`importlib.import_module("socket")` are all rejected, even though none of them is
named as a networking module and a denylist would let every one of them through.

It is not a sandbox. It is a static scan of the import statements in `src/`, run in
CI, so it catches a regression at review time. It does not inspect the test suite, the
packaging metadata, or the container image, and it cannot constrain what a caller does
with the interpreter that imports this package.

## Why this exists

LinkedIn's Terms of Service prohibit automating actions, including posting, on a
personal account. Rather than rely on developer discipline to keep this tool
compliant, the constraint is enforced in CI: there is no LinkedIn API client in this
codebase, and the build fails if any import capable of becoming one is ever added.

## Security-relevant behaviour

| Area | Behaviour |
|---|---|
| Network access | None. Every import under `src/` must be on a standard-library allowlist that excludes anything able to open a connection or start a process; a dedicated test enforces it in CI. |
| Posting to LinkedIn | Never performed by this tool. Every staged draft requires a human to copy it into LinkedIn's own composer and click "Post" themselves. |
| `mark-posted` | Pure local record-keeping — it accepts a URL you supply *after* posting manually; it does not verify or fetch it. |
| File I/O | Reads only the body file path you pass on the command line. Writes only under the configured `--staging-dir`. |
| Secrets | None are used or stored — there is nothing to authenticate to. |

## Reporting a vulnerability

Email `amasen02@gmail.com` with the subject prefix `[SECURITY]`, or open a private
[GitHub security advisory](https://github.com/amasen02/linkedin-content-manager/security/advisories/new).
**Do not open a public issue.** Expect acknowledgement within 72 hours.

## Coordinated disclosure window

90 days from acknowledgement, unless mutually extended.
