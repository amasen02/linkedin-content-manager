import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from linkedin_content_manager.__main__ import main


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)
        self.staging_dir = str(self.tmp_path / "staging")
        self.body_file = self.tmp_path / "body.txt"
        self.body_file.write_text("We shipped a thing today.", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(["--staging-dir", self.staging_dir, *args])
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_new_then_list_then_show(self) -> None:
        exit_code, stdout, _ = self._run(
            "new", "--title", "Shipped DupeSweep", "--body-file", str(self.body_file), "--hashtags", "dotnet,cli"
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("staged shipped-dupesweep-", stdout)

        draft_id = stdout.split()[1]

        exit_code, stdout, _ = self._run("list")
        self.assertEqual(exit_code, 0)
        self.assertIn(draft_id, stdout)
        self.assertIn("pending_review", stdout)

        exit_code, stdout, _ = self._run("show", draft_id)
        self.assertEqual(exit_code, 0)
        self.assertIn("We shipped a thing today.", stdout)
        self.assertIn("#dotnet #cli", stdout)

    def test_list_when_empty_reports_no_drafts(self) -> None:
        exit_code, stdout, _ = self._run("list")

        self.assertEqual(exit_code, 0)
        self.assertIn("no staged drafts", stdout)

    def test_approve_then_mark_posted_lifecycle(self) -> None:
        _, stdout, _ = self._run("new", "--title", "Lifecycle", "--body-file", str(self.body_file))
        draft_id = stdout.split()[1]

        exit_code, stdout, _ = self._run("approve", draft_id)
        self.assertEqual(exit_code, 0)
        self.assertIn("approved", stdout)

        exit_code, stdout, _ = self._run(
            "mark-posted", draft_id, "--url", "https://linkedin.com/feed/update/urn:li:activity:123"
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("posted", stdout)
        self.assertIn("urn:li:activity:123", stdout)

    def test_show_unknown_id_returns_error(self) -> None:
        exit_code, _, stderr = self._run("show", "does-not-exist")

        self.assertEqual(exit_code, 1)
        self.assertIn("error:", stderr)

    def test_new_with_empty_body_file_returns_error(self) -> None:
        empty_body = self.tmp_path / "empty.txt"
        empty_body.write_text("   ", encoding="utf-8")

        exit_code, _, stderr = self._run("new", "--title", "T", "--body-file", str(empty_body))

        self.assertEqual(exit_code, 1)
        self.assertIn("error:", stderr)


if __name__ == "__main__":
    unittest.main()
