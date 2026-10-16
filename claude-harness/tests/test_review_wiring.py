"""Wiring tests for the coder / code-reviewer pair, coding-standards, step verification docs and hooks.

Run from the harness root:  python3 -I -m unittest discover -s tests -t .
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent


def frontmatter(path):
    """Minimal YAML-frontmatter reader for agent/skill files: `key: value` and `key: [a, b]`."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise AssertionError(f"{path} has no frontmatter")
    out = {}
    for line in m.group(1).splitlines():
        k, sep, v = line.partition(":")
        if not sep or line.startswith(" "):
            continue
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            out[k.strip()] = [x.strip() for x in v[1:-1].split(",") if x.strip()]
        else:
            out[k.strip()] = v
    return out


def tool_list(value):
    if isinstance(value, list):
        return value
    return [t.strip() for t in (value or "").split(",") if t.strip()]


class ReviewWiringTest(unittest.TestCase):
    def setUp(self):
        self.coder = frontmatter(ROOT / "agents" / "coder.md")
        self.reviewer = frontmatter(ROOT / "agents" / "code-reviewer.md")

    def test_coding_standards_skill_is_preloadable(self):
        path = ROOT / "skills" / "coding-standards" / "SKILL.md"
        fm = frontmatter(path)
        self.assertEqual(fm["name"], "coding-standards")
        self.assertTrue(fm.get("description"))
        # skills with disable-model-invocation: true cannot be preloaded via `skills:`
        self.assertNotEqual(fm.get("disable-model-invocation", "false").lower(), "true")
        body = path.read_text(encoding="utf-8")
        for needle in ("Surgical", "Read before edit", "Never edit, delete, skip", "Review checklist",
                       "file:line", "Root cause", "No new dependency", "secrets"):
            self.assertIn(needle, body)
        self.assertLess(len(body.splitlines()), 500)

    def test_both_agents_preload_coding_standards(self):
        for fm in (self.coder, self.reviewer):
            self.assertIn("coding-standards", fm["skills"], fm["name"])
        self.assertIn("prior-art", self.coder["skills"])
        self.assertIn("mishap", self.coder["skills"])
        self.assertIn("mishap", self.reviewer["skills"])

    def test_reviewer_model_differs_from_coder(self):
        self.assertEqual(self.coder["model"], "sonnet")
        self.assertEqual(self.reviewer["model"], "opus")
        self.assertNotEqual(self.coder["model"], self.reviewer["model"])
        self.assertEqual(self.reviewer.get("effort"), "high")

    def test_no_agent_tool_in_either(self):
        for fm in (self.coder, self.reviewer):
            self.assertNotIn("Agent", tool_list(fm.get("tools")), fm["name"])
            self.assertNotIn("Task", tool_list(fm.get("tools")), fm["name"])
        self.assertIn("Agent", tool_list(self.reviewer.get("disallowedTools")))

    def test_reviewer_tools(self):
        tools = tool_list(self.reviewer["tools"])
        self.assertEqual(set(tools), {"Read", "Grep", "Glob", "Bash", "Edit"})
        self.assertIn("Write", tool_list(self.reviewer.get("disallowedTools")))

    def test_reviewer_modes_and_verdicts_documented(self):
        body = (ROOT / "agents" / "code-reviewer.md").read_text(encoding="utf-8")
        for needle in ("`step`", "`back-review`", "`approve`", "`fix-applied`", "`changes-requested`",
                       "`needs-human`", "file:line", "20", "mishap", "log/reviews.md"):
            self.assertIn(needle, body)

    def test_orchestrator_routes_coder_to_reviewer(self):
        body = (ROOT / "agents" / "orchestrator.md").read_text(encoding="utf-8")
        self.assertIn("code-reviewer", body)
        self.assertIn("back-review", body)
        self.assertIn("docs/VERIFICATION.md", body)
        fanout = (ROOT / "docs" / "FANOUT.md").read_text(encoding="utf-8")
        row = next(l for l in fanout.splitlines() if l.startswith("| **Writer + reviewer**"))
        self.assertIn("code-reviewer", row)
        self.assertIn("coder", row)

    def test_principle_21_and_verification_doc_linked(self):
        principles = (ROOT / "global" / "PRINCIPLES.md").read_text(encoding="utf-8")
        self.assertRegex(principles, r"(?m)^21\. \*\*Verify every step\.\*\*")
        self.assertIn("docs/VERIFICATION.md", principles)
        claude = (ROOT / "global" / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(sum("docs/VERIFICATION.md" in l for l in claude.splitlines()), 1)
        doc = (ROOT / "docs" / "VERIFICATION.md").read_text(encoding="utf-8")
        for needle in ("Precondition", "Postcondition", "Proof", "translation_qa.py", "textlen.py", "/check",
                       "read back", "kb.py lint", "--dry-run", "claim_check.py", "schema_check.py", "step_check"):
            self.assertIn(needle, doc)

    def test_step_check_hook_registered_and_existing_hooks_kept(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        [entry] = [e for e in hooks["PostToolUse"] if any("step_check.py" in h["command"] for h in e["hooks"])]
        self.assertEqual(set(entry["matcher"].split("|")), {"Edit", "Write", "MultiEdit", "NotebookEdit"})
        commands = " ".join(h["command"] for evs in hooks.values() for e in evs for h in e["hooks"])
        for script in ("log_event.py\" prompt", "usage_guard.py", "log_event.py\" session_end", "guard_protected.py",
                       "verify_gate.py", "precompact_snapshot.py\"", "precompact_snapshot.py\" post",
                       "postcompact_reinject.py", "step_check.py"):
            self.assertIn(script, commands)
        for evs in hooks.values():
            for e in evs:
                for h in e["hooks"]:
                    self.assertTrue((ROOT / "hooks" / re.search(r"hooks/(\w+\.py)", h["command"]).group(1)).is_file())


if __name__ == "__main__":
    unittest.main()
