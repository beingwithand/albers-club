import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("changelog", ROOT / "scripts" / "changelog.py")
changelog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog)


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


class TestChangelog(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name) / "proj"
        self.repo.mkdir()
        self.data = pathlib.Path(self.tmp.name) / "data"
        os.environ["HARNESS_DATA"] = str(self.data)
        git(self.repo, "init", "-q")
        (self.repo / "a.txt").write_text("1")
        git(self.repo, "add", "a.txt")
        git(self.repo, "commit", "-q", "-m", "Add first feature")
        (self.repo / "a.txt").write_text("2")
        git(self.repo, "commit", "-q", "-am", "Fix off-by-one in counter")

    def tearDown(self):
        os.environ.pop("HARNESS_DATA", None)
        self.tmp.cleanup()

    def test_draft_groups_commits(self):
        d = changelog.draft(self.repo)
        self.assertIn("### Added", d)
        self.assertIn("Add first feature", d)
        self.assertIn("### Fixed", d)

    def test_check_behind_then_current_after_update(self):
        ok, _ = changelog.check(self.repo)
        self.assertFalse(ok)
        changelog.update(self.repo, changelog.draft(self.repo))
        text = (self.repo / "CHANGELOG.md").read_text()
        self.assertIn("## [Unreleased]", text)
        self.assertIn("last-update:", text)
        ok, pending = changelog.check(self.repo)
        self.assertTrue(ok, pending)
        log = list((self.data / "log").glob("*.jsonl"))
        self.assertTrue(log)
        ev = json.loads(log[0].read_text().splitlines()[-1])
        self.assertIn("changelog_updated", ev["labels"])

    def test_decision_events_included(self):
        (self.data / "log").mkdir(parents=True)
        ev = {"id": "evt_x", "ts": "2999-01-01T00:00:00+00:00", "type": "decision",
              "claim": "Use flat project folders", "scope_hint": str(self.repo.resolve())}
        (self.data / "log" / "2999-01.jsonl").write_text(json.dumps(ev) + "\n")
        self.assertIn("Use flat project folders", changelog.draft(self.repo))

    def test_wip_snapshots_ignored(self):
        (self.repo / "b.txt").write_text("x")
        git(self.repo, "add", "b.txt")
        git(self.repo, "commit", "-q", "-m", "WIP snapshot (builders) - safety copy")
        self.assertNotIn("WIP snapshot", changelog.draft(self.repo))


if __name__ == "__main__":
    unittest.main()
