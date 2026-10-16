# Live test: hook IDs for causal tracing (2026-10-16, Claude Code headless, model haiku)

I ran a real `claude -p` session with logging hooks on every event. The prompt was: run `echo hi` in Bash, then start a general-purpose subagent that runs `echo sub`.

Observed sequence (IDs shortened):
```
SessionStart      source=startup
UserPromptSubmit  prompt_id=bd5c4757
PreToolUse        prompt_id=bd5c4757 tool_use_id=toolu_01… tool=Bash
PostToolUse       prompt_id=bd5c4757 tool_use_id=toolu_01… tool=Bash
PreToolUse        prompt_id=bd5c4757 tool_use_id=toolu_01… tool=Agent
SubagentStart     prompt_id=bd5c4757 agent_id=aca20b49 agent_type=general-purpose
PostToolUse       prompt_id=bd5c4757 tool=Agent  tool_response={isAsync:true, status:async_launched, agentId:aca20b49…}
Stop              prompt_id=bd5c4757
PreToolUse        prompt_id=bd5c4757 agent_id=aca20b49 tool=Bash     <- the subagent's tool calls
PostToolUse       prompt_id=bd5c4757 agent_id=aca20b49 tool=Bash
SubagentStop      prompt_id=bd5c4757 agent_id=aca20b49
UserPromptSubmit  prompt_id=d3162afe     <- synthetic turn: the async subagent's result delivered back
Stop              prompt_id=d3162afe
SessionEnd        prompt_id=d3162afe
```

## Confirmed facts
1. **`prompt_id` is on every event,** including the subagent's own tool calls. The subagent inherits the prompt_id of the prompt that spawned it, so intent propagates structurally for free.
2. **`agent_id` tags every subagent event.** The Agent tool's PostToolUse `tool_response.agentId` matches the SubagentStart `agent_id` as a prefix. That gives the parent → child join: the Agent call's `tool_use_id` links to its `agentId`.
3. **`tool_use_id` pairs each PreToolUse with its PostToolUse.**
4. **Background subagents finish *after* the parent's Stop,** and their result comes back as a new UserPromptSubmit, a synthetic turn with a new prompt_id. The tracer must mark those as `actor: harness` rather than the user. Detect them by content (task-notification) or by timing after a background Agent launch.
5. **SessionEnd carries the last prompt_id.**

These hold for the version used here, but they're internal behaviour, so re-check after Claude Code upgrades. A regression test is planned.
