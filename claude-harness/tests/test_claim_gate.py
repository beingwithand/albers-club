import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = ROOT / "hooks" / "claim_gate.py"


def sh(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                   check=True, capture_output=True)


def run(mode, payload):
    r = subprocess.run([sys.executable, "-I", str(HOOK), mode], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout.strip()


class TestClaimGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self.tmp.name)
        self.remote = base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)], check=True)
        self.repo = base / "work"
        subprocess.run(["git", "clone", "-q", str(self.remote), str(self.repo)], check=True,
                       capture_output=True)
        (self.repo / "a.txt").write_text("1")
        sh(self.repo, "add", "a.txt")
        sh(self.repo, "commit", "-q", "-m", "one")
        sh(self.repo, "push", "-q", "-u", "origin", "HEAD:refs/heads/main")
        sh(self.repo, "branch", "-q", "--set-upstream-to=origin/main")

    def tearDown(self):
        self.tmp.cleanup()

    def stop(self, msg):
        return run("stop", {"cwd": str(self.repo), "last_assistant_message": msg})

    def test_true_claim_passes(self):
        self.assertEqual(self.stop("Done — pushed to GitHub."), (0, ""))

    def test_false_push_claim_blocks(self):
        (self.repo / "a.txt").write_text("2")
        sh(self.repo, "commit", "-q", "-am", "two")  # committed but not pushed
        code, out = self.stop("All changes are pushed.")
        self.assertEqual(code, 0)
        d = json.loads(out)
        self.assertEqual(d["decision"], "block")
        self.assertIn("not pushed", d["reason"])

    def test_remote_mismatch_detected_even_if_tracking_ref_stale(self):
        (self.repo / "a.txt").write_text("3")
        sh(self.repo, "commit", "-q", "-am", "three")
        sh(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")  # fake "pushed" tracking ref
        d = json.loads(self.stop("Pushed!")[1])
        self.assertIn("remote origin/main is at", d["reason"])

    def test_commit_claim_with_dirty_tree_blocks(self):
        (self.repo / "b.txt").write_text("x")
        d = json.loads(self.stop("Everything is committed.")[1])
        self.assertIn("uncommitted", d["reason"])

    def test_korean_claim(self):
        (self.repo / "a.txt").write_text("4")
        sh(self.repo, "commit", "-q", "-am", "four")
        d = json.loads(self.stop("깃허브에 푸시했습니다.")[1])
        self.assertEqual(d["decision"], "block")

    def test_negated_claim_ignored(self):
        (self.repo / "b.txt").write_text("x")
        self.assertEqual(self.stop("Holding the commit; not pushing yet."), (0, ""))

    def test_loop_guard_and_disable(self):
        (self.repo / "b.txt").write_text("x")
        self.assertEqual(run("stop", {"cwd": str(self.repo), "stop_hook_active": True,
                                      "last_assistant_message": "committed"}), (0, ""))

    def test_post_push_verifier(self):
        (self.repo / "a.txt").write_text("5")
        sh(self.repo, "commit", "-q", "-am", "five")
        code, out = run("post", {"cwd": str(self.repo), "tool_input": {"command": "git push -q"}})
        self.assertIn("NOT VERIFIED", out)
        sh(self.repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        self.assertEqual(run("post", {"cwd": str(self.repo), "tool_input": {"command": "git push"}}), (0, ""))

    def test_not_a_repo_and_garbage(self):
        self.assertEqual(run("stop", {"cwd": self.tmp.name, "last_assistant_message": "pushed"}), (0, ""))
        r = subprocess.run([sys.executable, "-I", str(HOOK), "stop"], input="nope", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
