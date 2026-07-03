import tempfile
import unittest
from pathlib import Path

from linkedin_content_manager.exceptions import (
    DraftNotFoundError,
    DraftValidationError,
    InvalidTransitionError,
)
from linkedin_content_manager.models import HARD_CHARACTER_LIMIT, PostStatus
from linkedin_content_manager.store import DraftStore


class DraftStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = DraftStore(Path(self._tmp.name))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_create_stages_draft_as_pending_review(self) -> None:
        draft = self.store.create(title="Shipped DupeSweep", body="Body text.")

        self.assertEqual(draft.status, PostStatus.PENDING_REVIEW)
        self.assertTrue(draft.id.startswith("shipped-dupesweep-"))

    def test_create_writes_both_json_and_markdown_snapshot(self) -> None:
        draft = self.store.create(title="Shipped DupeSweep", body="Body text.")

        json_path = Path(self._tmp.name) / f"{draft.id}.json"
        md_path = Path(self._tmp.name) / f"{draft.id}.md"
        self.assertTrue(json_path.exists())
        self.assertTrue(md_path.exists())
        self.assertIn("Body text.", md_path.read_text(encoding="utf-8"))

    def test_create_rejects_empty_title(self) -> None:
        with self.assertRaises(DraftValidationError):
            self.store.create(title="   ", body="Body.")

    def test_create_rejects_empty_body(self) -> None:
        with self.assertRaises(DraftValidationError):
            self.store.create(title="T", body="   ")

    def test_create_rejects_body_over_hard_character_limit(self) -> None:
        with self.assertRaises(DraftValidationError):
            self.store.create(title="T", body="x" * (HARD_CHARACTER_LIMIT + 1))

    def test_get_missing_draft_raises(self) -> None:
        with self.assertRaises(DraftNotFoundError):
            self.store.get("does-not-exist")

    def test_list_returns_all_drafts_oldest_first(self) -> None:
        first = self.store.create(title="First", body="Body.")
        second = self.store.create(title="Second", body="Body.")

        drafts = self.store.list()

        self.assertEqual([draft.id for draft in drafts], [first.id, second.id])

    def test_list_filters_by_status(self) -> None:
        pending = self.store.create(title="Pending", body="Body.")
        approved = self.store.create(title="Approved", body="Body.")
        self.store.transition(approved.id, PostStatus.APPROVED)

        approved_only = self.store.list(status=PostStatus.APPROVED)

        self.assertEqual([draft.id for draft in approved_only], [approved.id])
        self.assertNotIn(pending.id, [draft.id for draft in approved_only])

    def test_full_lifecycle_pending_to_approved_to_posted(self) -> None:
        draft = self.store.create(title="Lifecycle", body="Body.")

        approved = self.store.transition(draft.id, PostStatus.APPROVED)
        self.assertEqual(approved.status, PostStatus.APPROVED)

        posted = self.store.transition(
            draft.id, PostStatus.POSTED, posted_url="https://linkedin.com/feed/update/urn:li:activity:123"
        )
        self.assertEqual(posted.status, PostStatus.POSTED)
        self.assertEqual(posted.posted_url, "https://linkedin.com/feed/update/urn:li:activity:123")

    def test_posted_is_a_terminal_status(self) -> None:
        draft = self.store.create(title="Terminal", body="Body.")
        self.store.transition(draft.id, PostStatus.APPROVED)
        self.store.transition(draft.id, PostStatus.POSTED, posted_url="https://example.com")

        with self.assertRaises(InvalidTransitionError):
            self.store.transition(draft.id, PostStatus.ARCHIVED)

    def test_cannot_skip_straight_from_draft_to_posted(self) -> None:
        draft = self.store.create(title="Skip", body="Body.")
        # create() lands drafts in PENDING_REVIEW; force back to DRAFT to test the guard.
        self.store.transition(draft.id, PostStatus.DRAFT)

        with self.assertRaises(InvalidTransitionError):
            self.store.transition(draft.id, PostStatus.POSTED, posted_url="https://example.com")

    def test_archived_draft_can_be_reopened(self) -> None:
        draft = self.store.create(title="Reopen", body="Body.")
        self.store.transition(draft.id, PostStatus.ARCHIVED)

        reopened = self.store.transition(draft.id, PostStatus.DRAFT)

        self.assertEqual(reopened.status, PostStatus.DRAFT)


if __name__ == "__main__":
    unittest.main()
