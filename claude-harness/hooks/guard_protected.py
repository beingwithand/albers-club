"""PreToolUse guard: block Bash commands that write to protected eval/rubric/test paths.

Edit/Write on these paths are already denied in settings.json; this closes the Bash gap
(sed -i, redirects, cp/mv/rm/tee into evals/, rubrics/, tests/). Exit code 2 blocks the call
and the stderr message is shown to Claude. Humans edit these files by hand.
"""
import json
import re
import sys

PROTECTED = re.compile(r"(^|[\s'\"/=])(evals|rubrics|tests)/")
WRITES = re.compile(r"(>>?|\bsed\s+(-[a-zA-Z]*i|--in-place)|\btee\b|\bcp\b|\bmv\b|\brm\b|\btruncate\b|\bdd\b|\bperl\s+-[a-zA-Z]*i|\bpython3?\b.*open\()")

try:
    payload = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if payload.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (payload.get("tool_input") or {}).get("command", "")
if PROTECTED.search(cmd) and WRITES.search(cmd):
    print("Blocked: evals/, rubrics/ and tests/ are protected from agent writes "
          "(reward-hacking guard). Propose the change to the user instead.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
