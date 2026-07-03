# Security policy

linkedin-content-manager makes **zero outbound network calls of any kind**. That is
not just documented behaviour — `tests/test_no_network.py` statically parses every
source file with Python's `ast` module and fails the build if any networking module
(`socket`, `urllib`, `http`, `requests`, `httpx`, `aiohttp`, `ftplib`, `smtplib`,
`telnetlib`) is ever imported anywhere under `src/linkedin_content_manager/`.

## Why this exists

LinkedIn's Terms of Service prohibit automating actions, including posting, on a
personal account. Rather than rely on developer discipline to keep this tool
compliant, the constraint is enforced structurally: there is no LinkedIn API client
in this codebase, and CI will fail if one is ever added.

## Security-relevant behaviour

| Area | Behaviour |
|---|---|
| Network access | None. Zero imports of any networking module, enforced by a dedicated test. |
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
