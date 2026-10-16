"""Claim gate: never let Claude say "pushed"/"committed" unless git proves it.

Two modes (registered in hooks/hooks.json):
  post   PostToolUse(Bash): after any `git push`/`git commit`, compare local vs remote and inject
         "PUSH NOT VERIFIED: ..." into context if they differ (never blocks).
  stop   Stop: if the final assistant message claims a push/commit (EN or KO) and the repo state
         contradicts it, BLOCK the stop with the exact discrepancy so Claude must fix or retract.

Checks (deterministic, read-only, 8 s budget): uncommitted/untracked changes, commits ahead of
upstream, missing upstream, and `git ls-remote` of the current branch vs local HEAD (network).
Disable with HARNESS_CLAIM_GATE=0. Never crashes: any internal error -> exit 0.
"""
import json
import os
import re
import subprocess
import sys

PUSH_CLAIM = re.compile(
    r"\b(pushed|pushing done|is (now )?on (github|the remote)|synced to (github|origin))\b"
    r"|푸시(했|완료|됐|되었)|올렸(습니다|어요|다)", re.I)
COMMIT_CLAIM = re.compile(r"\b(committed|everything is committed|all committed)\b|커밋(했|완료|됐|되었)", re.I)
NEGATED = re.compile(r"\b(not|n't|never|holding|haven't|won't)\b[^.\n]{0,40}\b(push|commit)", re.I)


def git(cwd, *args, timeout=4):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout.strip()


def repo_state(cwd, check_remote=True):
    """Return list of problems (empty = local and remote agree, tree clean)."""
    code, top = git(cwd, "rev-parse", "--show-toplevel")
    if code != 0:
        return None  # not a git repo: nothing to verify
    problems = []
    _, porcelain = git(top, "status", "--porcelain")
    dirty = [l for l in porcelain.splitlines() if l.strip()]
    _, branch = git(top, "rev-parse", "--abbrev-ref", "HEAD")
    _, head = git(top, "rev-parse", "HEAD")
    code, upstream = git(top, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if code != 0:
        problems.append(f"branch '{branch}' has no upstream (never pushed)")
    else:
        _, ahead = git(top, "rev-list", "--count", f"{upstream}..HEAD")
        if ahead.isdigit() and int(ahead) > 0:
            problems.append(f"{ahead} local commit(s) on '{branch}' not pushed to {upstream}")
        if check_remote:
            remote = upstream.split("/", 1)[0]
            rbranch = upstream.split("/", 1)[1] if "/" in upstream else branch
            try:
                code, out = git(top, "ls-remote", remote, f"refs/heads/{rbranch}", timeout=8)
            except subprocess.TimeoutExpired:
                code, out = 1, ""
                problems.append("could not reach the remote to confirm (ls-remote timed out)")
            if code == 0:
                rsha = out.split()[0] if out else ""
                if not rsha:
                    problems.append(f"remote has no branch '{rbranch}'")
                elif rsha != head:
                    problems.append(f"remote {remote}/{rbranch} is at {rsha[:8]}, local HEAD is {head[:8]}")
    return {"top": top, "branch": branch, "dirty": dirty, "problems": problems}


def claims(text):
    if not text or NEGATED.search(text):
        return set()
    out = set()
    if PUSH_CLAIM.search(text):
        out.add("push")
    if COMMIT_CLAIM.search(text):
        out.add("commit")
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "stop"
    if os.environ.get("HARNESS_CLAIM_GATE", "1").lower() in ("0", "false", "off", "no"):
        return 0
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    if not isinstance(payload, dict):
        return 0
    cwd = payload.get("cwd") or os.getcwd()
    if mode == "post":
        cmd = str((payload.get("tool_input") or {}).get("command", ""))
        if not re.search(r"\bgit\b[^\n|;&]*\b(push|commit)\b", cmd):
            return 0
        st = repo_state(cwd, check_remote="push" in cmd)
        if not st:
            return 0
        issues = list(st["problems"]) if "push" in cmd else []
        if "commit" in cmd and st["dirty"]:
            issues.append(f"{len(st['dirty'])} uncommitted/untracked path(s) remain")
        if issues:
            msg = "PUSH/COMMIT NOT VERIFIED: " + "; ".join(issues) + ". Do not claim it succeeded; fix or report it."
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))
        return 0
    # stop mode
    if payload.get("stop_hook_active"):
        return 0
    said = claims(str(payload.get("last_assistant_message") or ""))
    if not said:
        return 0
    st = repo_state(cwd, check_remote="push" in said)
    if not st:
        return 0
    issues = list(st["problems"]) if "push" in said else []
    if "commit" in said and st["dirty"]:
        issues.append(f"{len(st['dirty'])} uncommitted/untracked path(s) in {st['top']}")
    if issues:
        print(json.dumps({"decision": "block", "reason":
              "Your message claims " + "/".join(sorted(said)) + " succeeded, but git disagrees: "
              + "; ".join(issues) + ". Verify with `git status -sb` and `git ls-remote`, then push or correct the claim."}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
