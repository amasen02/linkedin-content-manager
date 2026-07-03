"""Domain model for a staged LinkedIn post draft."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum

# LinkedIn's hard cap on personal-post body length. Enforced by validation below.
HARD_CHARACTER_LIMIT = 3000

# LinkedIn truncates a post behind a "see more" click well before the hard limit —
# roughly 140-210 characters on mobile, more on desktop. The exact figure is a
# platform detail LinkedIn does not publish and can change; this is a soft
# authoring guideline (a warning, never a validation error), not an enforced rule.
RECOMMENDED_HOOK_CHARACTER_BUDGET = 210


class PostStatus(str, Enum):
    """Review lifecycle of a staged post. Nothing in this package can move a
    draft to POSTED except a human explicitly recording that they posted it
    themselves through LinkedIn's own UI."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    POSTED = "posted"
    ARCHIVED = "archived"


# Legal status transitions. Anything not listed here is rejected.
ALLOWED_TRANSITIONS: dict[PostStatus, frozenset[PostStatus]] = {
    PostStatus.DRAFT: frozenset({PostStatus.PENDING_REVIEW, PostStatus.ARCHIVED}),
    PostStatus.PENDING_REVIEW: frozenset(
        {PostStatus.APPROVED, PostStatus.DRAFT, PostStatus.ARCHIVED}
    ),
    PostStatus.APPROVED: frozenset(
        {PostStatus.POSTED, PostStatus.PENDING_REVIEW, PostStatus.ARCHIVED}
    ),
    PostStatus.POSTED: frozenset(),
    PostStatus.ARCHIVED: frozenset({PostStatus.DRAFT}),
}


@dataclass(slots=True)
class PostDraft:
    """A single staged LinkedIn post and its review metadata."""

    id: str
    title: str
    body: str
    status: PostStatus
    created_at: str
    updated_at: str
    source_repo: str = ""
    hashtags: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""
    posted_url: str = ""
    posted_at: str = ""

    @property
    def character_count(self) -> int:
        return len(self.render())

    def render(self) -> str:
        """The exact text a human should copy into LinkedIn's post composer."""
        parts = [self.body.rstrip()]
        if self.hashtags:
            parts.append(" ".join(f"#{tag}" for tag in self.hashtags))
        return "\n\n".join(parts)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        data["hashtags"] = list(self.hashtags)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "PostDraft":
        payload = dict(data)
        payload["status"] = PostStatus(payload["status"])
        payload["hashtags"] = tuple(payload.get("hashtags", ()))
        return cls(**payload)
