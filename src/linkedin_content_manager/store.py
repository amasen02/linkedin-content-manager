"""File-backed storage for staged post drafts.

Each draft is one JSON file under the store directory (default
``content/staging``). There is no database and no network call — the store is
just a directory of files a human (or a future tool) can read directly.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from linkedin_content_manager.exceptions import (
    DraftNotFoundError,
    DraftValidationError,
    InvalidTransitionError,
)
from linkedin_content_manager.models import (
    ALLOWED_TRANSITIONS,
    HARD_CHARACTER_LIMIT,
    PostDraft,
    PostStatus,
)

_SLUG_DISALLOWED = re.compile(r"[^a-z0-9]+")


def _slugify(title: str) -> str:
    slug = _SLUG_DISALLOWED.sub("-", title.lower()).strip("-")
    return slug or "untitled"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DraftStore:
    """Reads and writes :class:`PostDraft` objects under ``directory``."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        title: str,
        body: str,
        source_repo: str = "",
        hashtags: tuple[str, ...] = (),
        notes: str = "",
    ) -> PostDraft:
        if not title.strip():
            raise DraftValidationError("title must not be empty")
        if not body.strip():
            raise DraftValidationError("body must not be empty")

        timestamp = _now_iso()
        draft = PostDraft(
            id=f"{_slugify(title)}-{uuid.uuid4().hex[:8]}",
            title=title,
            body=body,
            status=PostStatus.PENDING_REVIEW,
            created_at=timestamp,
            updated_at=timestamp,
            source_repo=source_repo,
            hashtags=hashtags,
            notes=notes,
        )
        if draft.character_count > HARD_CHARACTER_LIMIT:
            raise DraftValidationError(
                f"rendered post is {draft.character_count} characters, "
                f"LinkedIn's hard limit is {HARD_CHARACTER_LIMIT}"
            )
        self._save(draft)
        return draft

    def get(self, draft_id: str) -> PostDraft:
        path = self._path_for(draft_id)
        if not path.exists():
            raise DraftNotFoundError(f"no staged draft with id {draft_id!r}")
        return PostDraft.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def list(self, status: PostStatus | None = None) -> list[PostDraft]:
        drafts = [
            PostDraft.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(self._directory.glob("*.json"))
        ]
        if status is not None:
            drafts = [draft for draft in drafts if draft.status == status]
        return sorted(drafts, key=lambda draft: draft.created_at)

    def transition(self, draft_id: str, new_status: PostStatus, **updates: str) -> PostDraft:
        draft = self.get(draft_id)
        allowed = ALLOWED_TRANSITIONS[draft.status]
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"cannot move draft {draft_id!r} from {draft.status.value!r} "
                f"to {new_status.value!r} (allowed: {sorted(s.value for s in allowed)})"
            )
        draft.status = new_status
        draft.updated_at = _now_iso()
        for field_name, value in updates.items():
            setattr(draft, field_name, value)
        self._save(draft)
        return draft

    def _save(self, draft: PostDraft) -> None:
        self._path_for(draft.id).write_text(
            json.dumps(draft.to_dict(), indent=2), encoding="utf-8"
        )
        self._path_for(draft.id).with_suffix(".md").write_text(
            _render_markdown_snapshot(draft), encoding="utf-8"
        )

    def _path_for(self, draft_id: str) -> Path:
        return self._directory / f"{draft_id}.json"


def _render_markdown_snapshot(draft: PostDraft) -> str:
    """A human-readable copy/paste snapshot alongside the JSON record."""
    lines = [
        f"# {draft.title}",
        "",
        f"status: {draft.status.value} | characters: {draft.character_count}",
        "",
        "---",
        "",
        draft.render(),
        "",
    ]
    return "\n".join(lines)
