"""Command-line entry point: ``python -m linkedin_content_manager <command> ...``.

Every command here reads and writes local files only. There is no command that
posts to LinkedIn, and there never will be — see the package docstring and
``tests/test_no_network.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from linkedin_content_manager.exceptions import ContentManagerError
from linkedin_content_manager.models import RECOMMENDED_HOOK_CHARACTER_BUDGET, PostStatus
from linkedin_content_manager.store import DraftStore

DEFAULT_STAGING_DIR = "content/staging"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="linkedin_content_manager")
    parser.add_argument(
        "--staging-dir",
        default=DEFAULT_STAGING_DIR,
        help=f"directory holding staged drafts (default: {DEFAULT_STAGING_DIR})",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="stage a new post draft for review")
    new_parser.add_argument("--title", required=True)
    new_parser.add_argument("--body-file", required=True, help="path to a text file with the post body")
    new_parser.add_argument("--source-repo", default="", help="e.g. https://github.com/amasen02/dupesweep")
    new_parser.add_argument("--hashtags", default="", help="comma-separated, without '#', e.g. dotnet,cli")
    new_parser.add_argument("--notes", default="")

    list_parser = subparsers.add_parser("list", help="list staged drafts")
    list_parser.add_argument("--status", choices=[status.value for status in PostStatus], default=None)

    show_parser = subparsers.add_parser("show", help="print the full rendered text of a draft")
    show_parser.add_argument("id")

    approve_parser = subparsers.add_parser("approve", help="mark a draft as approved for posting")
    approve_parser.add_argument("id")

    mark_posted_parser = subparsers.add_parser(
        "mark-posted", help="record that a human has posted this draft on LinkedIn"
    )
    mark_posted_parser.add_argument("id")
    mark_posted_parser.add_argument("--url", required=True, help="the live LinkedIn post URL")

    archive_parser = subparsers.add_parser("archive", help="archive a draft without posting it")
    archive_parser.add_argument("id")

    return parser


def _print_draft_summary(draft) -> None:
    print(f"{draft.id}\t{draft.status.value}\t{draft.character_count} chars\t{draft.title}")


def _use_utf8_streams() -> None:
    """Force UTF-8 on stdout/stderr regardless of the OS console code page.

    Draft bodies are free-form text and routinely contain characters outside
    a Windows terminal's default code page (curly quotes, em dashes, arrows).
    Without this, ``show``/``list`` crash with ``UnicodeEncodeError`` on the
    exact platform (Windows) this tool's target users run it on.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _use_utf8_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    store = DraftStore(Path(args.staging_dir))

    try:
        if args.command == "new":
            body = Path(args.body_file).read_text(encoding="utf-8")
            hashtags = tuple(tag.strip() for tag in args.hashtags.split(",") if tag.strip())
            draft = store.create(
                title=args.title,
                body=body,
                source_repo=args.source_repo,
                hashtags=hashtags,
                notes=args.notes,
            )
            print(f"staged {draft.id} (status={draft.status.value}, {draft.character_count} chars)")
            if draft.character_count > RECOMMENDED_HOOK_CHARACTER_BUDGET:
                print(
                    f"note: LinkedIn truncates long posts behind 'see more' well before its "
                    f"3000-char hard limit (roughly the first ~{RECOMMENDED_HOOK_CHARACTER_BUDGET} "
                    "chars on mobile) - make sure the opening line carries the point."
                )
            return 0

        if args.command == "list":
            status_filter = PostStatus(args.status) if args.status else None
            drafts = store.list(status=status_filter)
            if not drafts:
                print("no staged drafts")
                return 0
            for draft in drafts:
                _print_draft_summary(draft)
            return 0

        if args.command == "show":
            draft = store.get(args.id)
            print(f"# {draft.title}")
            print(f"status: {draft.status.value} | {draft.character_count} chars | source: {draft.source_repo or '-'}")
            print()
            print(draft.render())
            return 0

        if args.command == "approve":
            draft = store.transition(args.id, PostStatus.APPROVED)
            print(f"{draft.id} -> approved")
            return 0

        if args.command == "mark-posted":
            draft = store.transition(args.id, PostStatus.POSTED, posted_url=args.url)
            print(f"{draft.id} -> posted ({draft.posted_url})")
            return 0

        if args.command == "archive":
            draft = store.transition(args.id, PostStatus.ARCHIVED)
            print(f"{draft.id} -> archived")
            return 0

    except (ContentManagerError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
