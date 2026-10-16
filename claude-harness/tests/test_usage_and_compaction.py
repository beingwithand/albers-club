"""Tests for scripts/statusline.py and the usage / compaction hooks
(hooks/usage_guard.py, hooks/precompact_snapshot.py, hooks/postcompact_reinject.py).

Run from the harness root:  python3 -I -m unittest discover -s tests -t .
"""
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"
SCRIPTS = ROOT / "scripts"
HAS_GIT = shutil.which("git") is not None


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


statusline = load(SCRIPTS / "statusline.py", "harness_statusline")
NOW = 1_800_000_000.0


def payload(ctx=None, five=None, seven=None, cache=None, cost=1.5, sid="s1", cwd="/w", **extra):
    d = {"model": {"id": "claude-opus-5-5", "display_name": "Opus 5.5"}, "session_id": sid, "cwd": cwd,
         "cost": {"total_cost_usd": cost, "total_duration_ms": 1000},
         "context_window": {"total_input_tokens": 0, "total_output_tokens": 0, "context_window_size": 1_000_000,
                            "used_percentage": None, "remaining_percentage": None, "current_usage": None}}
    if ctx is not None:
        d["context_window"].update(
            total_input_tokens=ctx, used_percentage=ctx / 10_000,
            current_usage={"input_tokens": 1000, "output_tokens": 50,
                           "cache_creation_input_tokens": 0, "cache_read_input_tokens": ctx - 1000})
    rl = {}
    if five is not None:
        rl["five_hour"] = {"used_percentage": five, "resets_at": NOW + 2 * 3600 + 13 * 60}
    if seven is not None:
        rl["seven_day"] = {"used_percentage": seven, "resets_at": NOW + 3 * 86400 + 4 * 3600}
    if rl:
        d["rate_limits"] = rl
    if cache is not None:
        d["prompt_cache"] = cache
    d.update(extra)
    return d


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="harness-usage-"))
        self.state = self.tmp / "state" / "harness-state.json"
        self.data = self.tmp / "data"
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith("HARNESS_") and k not in ("NO_COLOR", "COLUMNS")}
        self.env.update(HARNESS_STATE=str(self.state), HARNESS_DATA=str(self.data), NO_COLOR="1")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


# ---------------------------------------------------------------- statusline

class StatuslineParseTest(Base):
    def test_full_line(self):
        line = statusline.run(json.dumps(payload(ctx=172_000, five=41, seven=78.2,
                                                 cache={"warm": True, "ttl": "5m", "expires_at": NOW + 250})),
                              self.env, NOW)
        self.assertEqual(line, "Opus 5.5 │ ctx 172k 69%⚠ │ 5h 41% ↻2h13m │ 7d 78% ↻3d4h │ cache warm 4m │ $1.50")

    def test_thresholds(self):
        render = lambda n: statusline.run(json.dumps(payload(ctx=n)), self.env, NOW)
        self.assertNotIn("⚠", render(159_999))
        self.assertIn("ctx 160k 64%⚠", render(160_000))
        self.assertIn("ctx 200k 80%⛔", render(200_000))
        self.assertNotIn("⚠", render(200_000))
        env = dict(self.env, HARNESS_CTX_BUDGET="100000")
        self.assertIn("ctx 50k 50%", statusline.run(json.dumps(payload(ctx=50_000)), env, NOW))

    def test_missing_and_null_fields(self):
        for raw in ["", "null", "[]", "not json", "{}", json.dumps({"model": None, "context_window": None}),
                    json.dumps(payload()), json.dumps(payload(rate_limits=None, prompt_cache=None, cost=None)),
                    json.dumps({"context_window": {"current_usage": {"input_tokens": None}},
                                "rate_limits": {"five_hour": None, "seven_day": {"used_percentage": None}}})]:
            line = statusline.run(raw, self.env, NOW)
            self.assertTrue(line, raw)
            self.assertIn("ctx ?", line, raw)
            self.assertNotIn("5h", line)

    def test_rate_limits_partially_absent(self):
        line = statusline.run(json.dumps(payload(ctx=10_000, seven=12)), self.env, NOW)
        self.assertIn("7d 12%", line)
        self.assertNotIn("5h", line)
        data = payload(ctx=10_000)
        data["rate_limits"] = {"five_hour": {"used_percentage": 3}}  # no resets_at
        self.assertIn("5h 3%", statusline.run(json.dumps(data), self.env, NOW))

    def test_context_fallbacks(self):
        d = payload()
        d["context_window"]["total_input_tokens"] = 42_000
        self.assertIn("ctx 42k", statusline.run(json.dumps(d), self.env, NOW))
        d = payload()
        d["context_window"]["used_percentage"] = 21.5
        self.assertIn("ctx 215k", statusline.run(json.dumps(d), self.env, NOW))

    def test_cache_cold_and_colour(self):
        self.assertIn("cache cold", statusline.run(json.dumps(payload(cache={"warm": False, "expires_at": None})),
                                                   self.env, NOW))
        env = {k: v for k, v in self.env.items() if k != "NO_COLOR"}
        line = statusline.run(json.dumps(payload(ctx=210_000)), env, NOW)
        self.assertIn("\033[", line)
        self.assertNotIn("\033[", statusline.run(json.dumps(payload(ctx=210_000)), self.env, NOW))

    def test_narrow_terminal_drops_cache_and_cost(self):
        env = dict(self.env, COLUMNS="40")
        line = statusline.run(json.dumps(payload(ctx=1000, five=1, cache={"warm": True})), env, NOW)
        self.assertNotIn("cache", line)
        self.assertNotIn("$", line)

    def test_subprocess_never_crashes_and_is_fast(self):
        for raw in ["garbage", json.dumps(payload(ctx=5000, five=10))]:
            t = time.time()
            p = subprocess.run([sys.executable, "-I", str(SCRIPTS / "statusline.py")], input=raw,
                               env=self.env, capture_output=True, text=True, timeout=30)
            self.assertLess(time.time() - t, 2.0)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(len(p.stdout.strip().splitlines()), 1)
        # unwritable state path: still prints a line
        env = dict(self.env, HARNESS_STATE="/proc/nope/state.json")
        p = subprocess.run([sys.executable, "-I", str(SCRIPTS / "statusline.py")], input=json.dumps(payload(ctx=1)),
                           env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0)
        self.assertIn("Opus 5.5", p.stdout)


class StatuslineStateTest(Base):
    def test_state_written_atomically(self):
        statusline.run(json.dumps(payload(ctx=123_000, five=50, seven=60, sid="abc", cwd="/proj")), self.env, NOW)
        st = json.loads(self.state.read_text())
        self.assertEqual(st["ctx_tokens"], 123_000)
        self.assertEqual(st["ctx_budget"], 250_000)
        self.assertEqual(st["five_hour_pct"], 50)
        self.assertEqual(st["seven_day_resets"], NOW + 3 * 86400 + 4 * 3600)
        self.assertEqual((st["session_id"], st["cwd"], st["ts"]), ("abc", "/proj", NOW))
        self.assertEqual(st["sessions"]["abc"]["ctx_tokens"], 123_000)
        self.assertEqual([p.name for p in self.state.parent.iterdir()], ["harness-state.json"])  # no tmp left

    def test_rate_limits_kept_until_reset_when_absent(self):
        statusline.run(json.dumps(payload(ctx=1000, five=50, seven=60)), self.env, NOW)
        statusline.run(json.dumps(payload(ctx=2000, sid="s2")), self.env, NOW + 60)
        st = json.loads(self.state.read_text())
        self.assertEqual((st["five_hour_pct"], st["seven_day_pct"], st["session_id"]), (50, 60, "s2"))
        self.assertEqual(set(st["sessions"]), {"s1", "s2"})
        statusline.run(json.dumps(payload(ctx=2000, sid="s2")), self.env, NOW + 3 * 3600)  # 5h window passed
        st = json.loads(self.state.read_text())
        self.assertIsNone(st["five_hour_pct"])
        self.assertEqual(st["seven_day_pct"], 60)

    def test_corrupt_state_is_replaced(self):
        self.state.parent.mkdir(parents=True)
        self.state.write_text("{oops")
        statusline.run(json.dumps(payload(ctx=1000)), self.env, NOW)
        self.assertEqual(json.loads(self.state.read_text())["ctx_tokens"], 1000)


class NtfyTest(Base):
    def setUp(self):
        super().setUp()
        self.env["HARNESS_NTFY_TOPIC"] = "test-topic-xyz"

    def run_line(self, now=NOW, **kw):
        with mock.patch.object(statusline, "_dispatch_ntfy") as disp:
            statusline.run(json.dumps(payload(ctx=1000, **kw)), self.env, now)
        return [a for call in disp.call_args_list for a in call.args[1]]

    def test_no_topic_no_push(self):
        del self.env["HARNESS_NTFY_TOPIC"]
        self.assertEqual(self.run_line(seven=95, five=95), [])

    def test_thresholds_and_dedup(self):
        self.assertEqual(self.run_line(seven=74, five=89), [])
        a = self.run_line(seven=76, five=89)
        self.assertEqual(len(a), 1)
        self.assertIn("7d", a[0][1])
        self.assertEqual(self.run_line(seven=80, five=89, now=NOW + 60), [])  # same window: once
        a = self.run_line(seven=91, five=89, now=NOW + 120)
        self.assertEqual([x[3] for x in a], ["high"])
        a = self.run_line(seven=91, five=92, now=NOW + 180)
        self.assertEqual(len(a), 1)
        self.assertIn("5h", a[0][1])
        self.assertEqual(self.run_line(seven=95, five=99, now=NOW + 240), [])

    def test_jump_straight_to_90_sends_one(self):
        a = self.run_line(seven=93)
        self.assertEqual(len(a), 1)
        self.assertIn("93%", a[0][1])
        self.assertEqual(self.run_line(seven=93, now=NOW + 5), [])

    def test_new_window_alerts_again(self):
        self.assertEqual(len(self.run_line(five=95)), 1)
        d = payload(ctx=1000)
        d["rate_limits"] = {"five_hour": {"used_percentage": 95, "resets_at": NOW + 6 * 3600 + 7200}}
        with mock.patch.object(statusline, "_dispatch_ntfy") as disp:
            statusline.run(json.dumps(d), self.env, NOW + 7200)
        self.assertEqual(disp.call_count, 1)

    def test_send_ntfy_uses_urllib_with_timeout(self):
        resp = mock.MagicMock()
        resp.__enter__.return_value.status = 200
        with mock.patch("urllib.request.urlopen", return_value=resp) as uo:
            ok = statusline.send_ntfy("topic", "Claude 7d usage 91%", "msg ✓", "high")
        self.assertTrue(ok)
        req = uo.call_args.args[0]
        self.assertEqual(uo.call_args.kwargs["timeout"], 2.0)
        self.assertEqual(req.full_url, "https://ntfy.sh/topic")
        self.assertEqual(req.data, "msg ✓".encode())
        self.assertEqual(req.get_header("Priority"), "high")
        with mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
            self.assertFalse(statusline.send_ntfy("topic", "t", "m"))


# ---------------------------------------------------------------- usage guard

class UsageGuardTest(Base):
    def write_state(self, **kw):
        st = {"ctx_tokens": None, "ctx_budget": 250000, "ctx_warn": 160000, "ctx_stop": 200000,
              "five_hour_pct": None, "five_hour_resets": None, "seven_day_pct": None, "seven_day_resets": None,
              "ts": time.time(), "session_id": "s1", "cwd": str(self.tmp)}
        st.update(kw)
        if "sessions" not in kw and st["session_id"]:
            st["sessions"] = {st["session_id"]: {"ctx_tokens": st["ctx_tokens"], "ts": st["ts"], "cwd": st["cwd"]}}
        self.state.parent.mkdir(parents=True, exist_ok=True)
        self.state.write_text(json.dumps(st))

    def guard(self, sid="s1", prompt="keep going", cwd=None):
        p = subprocess.run([sys.executable, "-I", str(HOOKS / "usage_guard.py")],
                           input=json.dumps({"session_id": sid, "cwd": cwd or str(self.tmp), "prompt": prompt,
                                             "hook_event_name": "UserPromptSubmit"}),
                           env=self.env, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0, p.stderr)
        if not p.stdout.strip():
            return None
        out = json.loads(p.stdout)
        self.assertNotIn("decision", out)  # never blocks
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        return out

    def test_no_state_or_low_usage_is_silent(self):
        self.assertIsNone(self.guard())
        self.write_state(ctx_tokens=50_000, five_hour_pct=40, seven_day_pct=50)
        self.assertIsNone(self.guard())

    def test_hard_stop_every_prompt(self):
        self.write_state(ctx_tokens=210_000)
        for _ in range(2):
            out = self.guard()
            ctx = out["hookSpecificOutput"]["additionalContext"]
            self.assertIn("/handoff", ctx)
            self.assertIn("/clear", ctx)
            self.assertIn("atomic step", ctx)
            self.assertIn("⛔", out["systemMessage"])

    def test_hard_stop_with_fresh_handoff_reminds_clear(self):
        (self.tmp / ".git").mkdir()
        (self.tmp / "HANDOFF.md").write_text("# HANDOFF\n")
        self.write_state(ctx_tokens=210_000)
        ctx = self.guard()["hookSpecificOutput"]["additionalContext"]
        self.assertIn("HANDOFF.md was refreshed", ctx)
        self.assertIn("/clear", ctx)

    def test_soft_warning_once_per_session(self):
        self.write_state(ctx_tokens=170_000)
        out = self.guard()
        self.assertIn("Heads-up", out["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.guard())
        self.write_state(ctx_tokens=170_000, session_id="s2")
        self.assertIsNotNone(self.guard(sid="s2"))

    def test_stale_state_ignored(self):
        self.write_state(ctx_tokens=250_000, seven_day_pct=95, seven_day_resets=time.time() + 86400,
                         ts=time.time() - 11 * 60)
        self.assertIsNone(self.guard())

    def test_other_session_context_ignored_but_rate_limits_count(self):
        self.write_state(ctx_tokens=250_000, session_id="other")
        self.assertIsNone(self.guard(sid="s1"))
        self.write_state(ctx_tokens=250_000, session_id="other", five_hour_pct=93,
                         five_hour_resets=time.time() + 3600)
        out = self.guard(sid="s1")
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("/handoff", ctx)
        self.assertIn("5-hour usage is 93%", ctx)
        self.assertIn("resets in", ctx)
        self.assertIn("cheaper models", ctx)

    def test_rate_advice_once_per_window(self):
        self.write_state(seven_day_pct=91, seven_day_resets=time.time() + 86400)
        self.assertIn("7-day usage is 91%", self.guard()["hookSpecificOutput"]["additionalContext"])
        self.assertIsNone(self.guard())
        self.write_state(seven_day_pct=91, seven_day_resets=time.time() - 5)  # window already reset
        self.assertIsNone(self.guard(sid="s9"))

    def test_skips_handoff_and_compact_prompts(self):
        self.write_state(ctx_tokens=230_000)
        for pr in ("/handoff", "/compact keep decisions", "/clear", "/compact-prep"):
            self.assertIsNone(self.guard(prompt=pr), pr)

    def test_disabled_and_garbage(self):
        self.write_state(ctx_tokens=230_000)
        self.env["HARNESS_USAGE_GUARD"] = "0"
        self.assertIsNone(self.guard())
        del self.env["HARNESS_USAGE_GUARD"]
        self.state.write_text("[1,2")
        self.assertIsNone(self.guard())
        for raw in ["", "nope", "[]"]:
            p = subprocess.run([sys.executable, "-I", str(HOOKS / "usage_guard.py")], input=raw,
                               env=self.env, capture_output=True, text=True, timeout=30)
            self.assertEqual((p.returncode, p.stdout), (0, ""))

    def test_end_to_end_with_statusline(self):
        statusline.run(json.dumps(payload(ctx=205_000, sid="live")), self.env, time.time())
        self.assertIn("/handoff", self.guard(sid="live")["hookSpecificOutput"]["additionalContext"])


# ---------------------------------------------------------------- compaction hooks

def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                            GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null"))


class CompactionBase(Base):
    def setUp(self):
        super().setUp()
        self.proj = self.tmp / "proj"
        self.proj.mkdir()
        (self.proj / "PROGRESS.md").write_text(
            "# Progress\n\n## Goal\nShip it\n\n## Done\n- [x] parser — proof: tests/test_p.py\n\n"
            "## In progress\n- writer module\n\n## Next\n- run `make test`\n- wire CLI\n\n## Blockers\nnone\n",
            encoding="utf-8")

    def init_git(self):
        git(self.proj, "init", "-q", "-b", "feature/x")
        (self.proj / "a.txt").write_text("a")
        git(self.proj, "add", "-A")
        git(self.proj, "commit", "-q", "-m", "init")
        (self.proj / "b.txt").write_text("untracked")
        p = subprocess.run(["git", "-C", str(self.proj), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True)
        return p.stdout.strip()

    def hook(self, script, data, *args):
        p = subprocess.run([sys.executable, "-I", str(HOOKS / script), *args], input=json.dumps(data),
                           env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout

    def events(self):
        out = []
        for f in sorted((self.data / "log").glob("*.jsonl")):
            out += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        return out

    def add_events(self, evs):
        (self.data / "log").mkdir(parents=True, exist_ok=True)
        with open(self.data / "log" / "2026-10.jsonl", "a", encoding="utf-8") as f:
            for e in evs:
                f.write(json.dumps(e) + "\n")


@unittest.skipUnless(HAS_GIT, "git not available")
class PreCompactTest(CompactionBase):
    def test_snapshot_contents(self):
        head = self.init_git()
        (self.proj / "HANDOFF.md").write_text("# HANDOFF\ngit_commit: 0000000   branch: main\n")
        evs = [{"id": f"evt_d{i}", "ts": f"2026-10-16T10:{i:02d}:00+00:00", "type": "decision",
                "scope_hint": str(self.proj), "content": f"decision {i}", "justification": f"because {i}"}
               for i in range(12)]
        evs += [{"id": "evt_m", "ts": "2026-10-16T11:00:00+00:00", "type": "mishap", "scope_hint": str(self.proj),
                 "content": "wrong file edited"},
                {"id": "evt_other", "ts": "2026-10-16T11:30:00+00:00", "type": "decision",
                 "scope_hint": "/elsewhere", "content": "not mine"},
                {"id": "evt_p", "ts": "2026-10-16T11:40:00+00:00", "type": "prompt", "scope_hint": str(self.proj)}]
        self.add_events(evs)
        sub = self.proj / "src"
        sub.mkdir()
        out = self.hook("precompact_snapshot.py", {
            "session_id": "sess-1", "transcript_path": "/t/x.jsonl", "cwd": str(sub),
            "hook_event_name": "PreCompact", "trigger": "manual", "custom_instructions": "keep the parser decisions"})
        msg = json.loads(out)
        self.assertNotIn("decision", msg)  # never blocks
        [snap] = list((self.proj / "log" / "handoffs").glob("auto_*.md"))
        self.assertIn(str(snap), msg["systemMessage"])
        text = snap.read_text(encoding="utf-8")
        for needle in ("trigger: `manual`", "keep the parser decisions", "/t/x.jsonl", "sess-1",
                       "branch: `feature/x`", f"HEAD: `{head}`", "?? b.txt", "## Next", "run `make test`",
                       "HANDOFF.md", "HEAD is now", "decision 11", "because 11", "wrong file edited"):
            self.assertIn(needle, text, needle)
        self.assertNotIn("decision 1 ", text)  # only the last 10 events (d3..d11 + mishap)
        self.assertNotIn("not mine", text)
        self.assertNotIn("decision 2", text)
        pre = [e for e in self.events() if e["type"] == "precompact"]
        self.assertEqual(len(pre), 1)
        self.assertEqual((pre[0]["trigger"], pre[0]["session_id"]), ("manual", "sess-1"))
        self.assertEqual(pre[0]["pointers"], [str(snap)])

    def test_progress_only_project_and_outside_project(self):
        out = self.hook("precompact_snapshot.py", {"cwd": str(self.proj), "trigger": "auto", "session_id": "s"})
        [snap] = list((self.proj / "log" / "handoffs").glob("auto_*.md"))
        text = snap.read_text(encoding="utf-8")
        self.assertIn("Not a git repository", text)
        self.assertIn("No HANDOFF.md", text)
        self.assertIn("trigger: `auto`", text)
        self.assertIn("custom_instructions: _none_", text)
        bare = self.tmp / "bare"
        bare.mkdir()
        self.assertEqual(self.hook("precompact_snapshot.py", {"cwd": str(bare), "trigger": "auto"}), "")
        self.assertFalse((bare / "log").exists())
        self.assertEqual(len([e for e in self.events() if e["type"] == "precompact"]), 2)

    def test_garbage_never_blocks(self):
        for raw in ["", "x", "[]", json.dumps({"cwd": 3})]:
            p = subprocess.run([sys.executable, "-I", str(HOOKS / "precompact_snapshot.py")], input=raw,
                               env=self.env, capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 0)
            self.assertNotIn("block", p.stdout)

    def test_prunes_old_snapshots(self):
        hd = self.proj / "log" / "handoffs"
        hd.mkdir(parents=True)
        for i in range(35):
            (hd / f"auto_20200101_0000{i:02d}.md").write_text("old")
        (hd / "20200101_000000.md").write_text("manual archive")
        self.hook("precompact_snapshot.py", {"cwd": str(self.proj), "trigger": "auto"})
        self.assertEqual(len(list(hd.glob("auto_*.md"))), 30)
        self.assertTrue((hd / "20200101_000000.md").exists())

    def test_postcompact_appends_summary(self):
        self.hook("precompact_snapshot.py", {"cwd": str(self.proj), "trigger": "auto", "session_id": "sx"})
        self.hook("precompact_snapshot.py", {"cwd": str(self.proj), "trigger": "auto", "session_id": "sx",
                                             "compact_summary": "We decided X because Y."}, "post")
        [snap] = list((self.proj / "log" / "handoffs").glob("auto_*.md"))
        self.assertIn("We decided X because Y.", snap.read_text(encoding="utf-8"))
        post = [e for e in self.events() if e["type"] == "postcompact"]
        self.assertEqual(post[0]["pointers"], [str(snap)])


@unittest.skipUnless(HAS_GIT, "git not available")
class PostCompactReinjectTest(CompactionBase):
    def reinject(self, source="compact", cwd=None):
        out = self.hook("postcompact_reinject.py", {"session_id": "s", "cwd": str(cwd or self.proj),
                                                   "hook_event_name": "SessionStart", "source": source})
        if not out:
            return None
        data = json.loads(out)
        self.assertEqual(set(data), {"hookSpecificOutput"})
        self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "SessionStart")
        ctx = data["hookSpecificOutput"]["additionalContext"]
        self.assertIsInstance(ctx, str)
        self.assertLessEqual(len(ctx), 8000)
        return ctx

    def test_shape_and_contents(self):
        head = self.init_git()
        (self.proj / "HANDOFF.md").write_text(f"# HANDOFF: proj\ngit_commit: {head}   branch: feature/x\n\n"
                                              "## 6. Next 3 actions\n1. run `make test`\n", encoding="utf-8")
        (self.proj / "CLAUDE.md").write_text("rules")
        (self.proj / ".claude" / "rules").mkdir(parents=True)
        (self.proj / ".claude" / "rules" / "style.md").write_text("x")
        (self.proj / ".claude" / "agents").mkdir()
        (self.proj / ".claude" / "agents" / "code-reviewer.md").write_text("x")
        (self.proj / ".claude" / "agents" / "writer.md").write_text("x")
        self.hook("precompact_snapshot.py", {"cwd": str(self.proj), "trigger": "auto"})
        ctx = self.reinject()
        for needle in ("Session compact", "## HANDOFF.md", "git_commit: " + head, "auto_", "## PROGRESS.md: Next",
                       "wire CLI", "## PROGRESS.md: In Progress", "writer module",
                       str(self.proj / "CLAUDE.md"), "style.md", "code-reviewer.md"):
            self.assertIn(needle, ctx, needle)
        self.assertNotIn("STALE", ctx)
        self.assertNotIn("writer.md`", ctx)
        self.assertNotIn("Blockers", ctx)
        self.assertIn("Session clear", self.reinject("clear"))

    def test_stale_commit_flagged(self):
        self.init_git()
        (self.proj / "HANDOFF.md").write_text("# H\ngit_commit: `deadbee`\n")
        self.assertIn("STALE", self.reinject())

    def test_size_cap_and_truncation_pointer(self):
        big = "# HANDOFF\n" + ("decision line with detail\n" * 2000)
        (self.proj / "HANDOFF.md").write_text(big, encoding="utf-8")
        (self.proj / "PROGRESS.md").write_text("## Next\n" + "- step\n" * 2000, encoding="utf-8")
        rules = self.proj / ".claude" / "rules"
        rules.mkdir(parents=True)
        for i in range(40):
            (rules / f"r{i:02d}.md").write_text("x")
        ctx = self.reinject()
        self.assertLessEqual(len(ctx), 8000)
        self.assertIn("truncated", ctx)
        self.assertIn(str(self.proj / "HANDOFF.md"), ctx)
        self.assertIn("+20 more", ctx)

    def test_old_handoff_pointer_only(self):
        p = self.proj / "HANDOFF.md"
        p.write_text("# H\nSECRET_BODY\n")
        old = time.time() - 72 * 3600
        os.utime(p, (old, old))
        ctx = self.reinject()
        self.assertIn("Older than 48 h", ctx)
        self.assertNotIn("SECRET_BODY", ctx)

    def test_outside_project_silent(self):
        bare = self.tmp / "bare"
        bare.mkdir()
        self.assertIsNone(self.reinject(cwd=bare))
        for raw in ["", "{", "[]"]:
            p = subprocess.run([sys.executable, "-I", str(HOOKS / "postcompact_reinject.py")], input=raw,
                               env=self.env, capture_output=True, text=True, timeout=30)
            self.assertEqual((p.returncode, p.stdout), (0, ""))


# ---------------------------------------------------------------- static wiring

class WiringTest(unittest.TestCase):
    def test_hooks_registered(self):
        h = json.loads((HOOKS / "hooks.json").read_text())["hooks"]
        cmds = lambda ev: [x["command"] for g in h.get(ev, []) for x in g["hooks"]]
        self.assertTrue(any("log_event.py" in c for c in cmds("UserPromptSubmit")))
        self.assertTrue(any("usage_guard.py" in c for c in cmds("UserPromptSubmit")))
        self.assertTrue(any("verify_gate.py" in c for c in cmds("Stop")))
        self.assertTrue(any("guard_protected.py" in c for c in cmds("PreToolUse")))
        self.assertTrue(any("precompact_snapshot.py" in c for c in cmds("PreCompact")))
        self.assertTrue(any(c.endswith(" post") for c in cmds("PostCompact")))
        [ss] = h["SessionStart"]
        self.assertIn("compact", ss["matcher"].split("|"))
        self.assertIn("postcompact_reinject.py", ss["hooks"][0]["command"])
        for ev, groups in h.items():
            for g in groups:
                for x in g["hooks"]:
                    m = re.search(r"/hooks/(\w+\.py)", x["command"])
                    self.assertTrue((HOOKS / m.group(1)).is_file(), x["command"])

    def test_settings(self):
        s = json.loads((ROOT / "config" / "settings.json").read_text())
        self.assertEqual(s["autoCompactWindow"], 250000)
        self.assertEqual(s["statusLine"]["type"], "command")
        self.assertIn("scripts/statusline.py", s["statusLine"]["command"])
        self.assertGreaterEqual(s["statusLine"]["refreshInterval"], 1)
        self.assertIn("Notification", s["hooks"])
        self.assertIn("defaultMode", s["permissions"])
        readme = (ROOT / "config" / "settings.README.md").read_text()
        for k in ("autoCompactWindow", "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", "idleCompaction", "/autocompact",
                  "/usage", "autoContinueAtUsageLimit", "ntfy", "statusLine"):
            self.assertIn(k, readme, k)

    def test_compact_instructions_section(self):
        text = (ROOT / "global" / "CLAUDE.md").read_text()
        m = re.search(r"^# Compact instructions\n(.*?)(?=^# |\Z)", text, re.M | re.S)
        self.assertTrue(m)
        body = [l for l in m.group(1).splitlines() if l.strip()]
        self.assertLessEqual(len(body), 10)
        self.assertIn("HANDOFF.md", m.group(1))

    def test_skills_and_rubric(self):
        for name in ("handoff", "compact-prep"):
            text = (ROOT / "skills" / name / "SKILL.md").read_text()
            self.assertRegex(text, rf"\A---\nname: {name}\ndescription: .+\n---\n")
        ho = (ROOT / "skills" / "handoff" / "SKILL.md").read_text()
        for k in ("Cold-read test", "haiku", "git_commit", "Dead ends", "Verify first", "Next 3 actions"):
            self.assertIn(k, ho)
        r = (ROOT / "rubrics" / "handoff.yaml").read_text()
        for key in ("criteria:", "automatic_checks:", "dimensions:", "anchors:", "model_must_differ_from_producer: true"):
            self.assertIn(key, r)
        for dim in ("correctness", "correction_rate", "cost", "time", "style_match", "outcome"):
            self.assertIn(f"  {dim}:", r)
        weights = [float(w) for w in re.findall(r"^\s+weight: ([0-9.]+)", r, re.M)]
        self.assertAlmostEqual(sum(weights), 1.0)
        for cid in ("resumability", "completeness", "accuracy", "concision", "proof_pointers"):
            self.assertIn(f"id: {cid}", r)


if __name__ == "__main__":
    unittest.main()
