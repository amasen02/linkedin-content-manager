import unittest

from linkedin_content_manager.models import PostDraft, PostStatus


class PostDraftRenderTests(unittest.TestCase):
    def test_render_appends_hashtags_with_hash_prefix(self) -> None:
        draft = PostDraft(
            id="x",
            title="T",
            body="Body text.",
            status=PostStatus.DRAFT,
            created_at="2026-07-03T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
            hashtags=("dotnet", "cli"),
        )

        self.assertEqual(draft.render(), "Body text.\n\n#dotnet #cli")

    def test_render_without_hashtags_is_just_the_body(self) -> None:
        draft = PostDraft(
            id="x",
            title="T",
            body="Body text.",
            status=PostStatus.DRAFT,
            created_at="2026-07-03T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )

        self.assertEqual(draft.render(), "Body text.")

    def test_character_count_matches_rendered_length(self) -> None:
        draft = PostDraft(
            id="x",
            title="T",
            body="1234567890",
            status=PostStatus.DRAFT,
            created_at="2026-07-03T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
        )

        self.assertEqual(draft.character_count, 10)

    def test_round_trips_through_dict(self) -> None:
        original = PostDraft(
            id="x",
            title="T",
            body="Body.",
            status=PostStatus.PENDING_REVIEW,
            created_at="2026-07-03T00:00:00+00:00",
            updated_at="2026-07-03T00:00:00+00:00",
            hashtags=("a", "b"),
        )

        restored = PostDraft.from_dict(original.to_dict())

        self.assertEqual(restored, original)


if __name__ == "__main__":
    unittest.main()
