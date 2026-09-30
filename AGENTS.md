# specklepy

The Speckle Python SDK.

## Agent config (ADR-0008)

Tracked sources: this file, repo-local `agents/skills/` and `agents/mcp/`
(when the repo has any), the hooks `.claude/settings.json` +
`.codex/hooks.json`, and omp's `.omp/extensions/atlas-sync.js`.
`.claude/skills/`, `.agents/skills/`, `.mcp.json`, `.codex/config.toml` and
the block below are written by `../atlas/scripts/sync-agents.py` (session
start, `mise run agents-sync` at the atlas root) — edit the source, never the
output. Layout, opt-in shared MCP servers and collision rules:
`../atlas/agents/README.md`.

<!-- atlas:shared:begin -->

<!-- Duplicated from the atlas checkout root AGENTS.md by atlas/scripts/sync-agents.py for clients that stop at this repo's git root (Codex, Grok). Edit the atlas copy. -->

# Code comments: decision significance only

Write a comment only when it states a decision or constraint the code
cannot show — the why behind a non-obvious choice, with the ticket, spec,
or ADR reference when one exists. Never write comments that:

- describe the current state of the world elsewhere ("the chart ignores
  this value for now", "X hasn't landed yet") — they go stale silently
  the moment that other thing changes;
- retell the spec, plan, or PR narrative — reference the ticket instead;
- explain what the next line does.

That context belongs in the commit message, PR body, or ticket. This
policy overrides matching the comment density of the surrounding file:
a legacy heavy-comment file does not license new narrative comments.

# Ticket workflow: claim before you code

When starting implementation of a Linear ticket — via /implement, /tdd, or
no skill at all — first claim it:

1. Move the ticket to **In Progress**.
2. Assign it to the developer running the session (`linear-server`
   `get_user` with query "me").

If the ticket is already In Progress and assigned to someone else, stop
and confirm with the user before touching it — it may be claimed by a
parallel session, and double-resolving a claimed ticket has burned us
before.

This applies only to work tracked as a Linear ticket; untracked work and
repo-local trackers with their own conventions are unaffected. Claiming is
the only transition this rule owns — later states (review, done) belong to
the PR flow.

# Ways of working (Speckle stack)

When the user starts describing a feature, refactor, bug, or plan, suggest
the matching entry point instead of diving into implementation: `/wayfinder`
for big/foggy multi-session work, `/grill-me` (or `/grill-with-docs`) to
stress-test one plan, `/prototype` when "how should it look/behave" is open,
then `/to-spec` → `/to-tickets` → `/implement` (which calls `/code-review`).
The full loop: `atlas/ways-of-working.md` in the speckle-atlas checkout root
(`../atlas/ways-of-working.md` from this repo in the standard nested layout)
— read it before shaping non-trivial work.

Specs: cross-repo → the atlas repo's `atlas/specs/`; local to this repo →
this repo's `specs/` folder. Same structure everywhere: `YYYY-MM-title.md`,
a linked Linear project, worked via PR. Check both places when picking up
spec work.

ADR linking is two-way (atlas ADR-0003 + its amendment): a repo-local ADR
born from a cross-repo project back-links the owning atlas spec in its
header and is indexed from that spec; and when a stack-level ADR — standing
(`atlas/adr/`) or a spec's — governs a specific module of this repo, that
module carries a **pointer ADR** in its local ADR home. A pointer is a thin
stub, never a fork of the atlas content: it keeps the atlas ADR's number and
title, names the atlas text as canonical, links it and its spec by relative
path (never GitHub URLs), summarizes the decision and what it binds in this
module, and is registered in the module's docs index and the repo's context
map. The pointer lands with the work that makes the decision bind the
module. If a pointer's atlas links don't resolve, this checkout is missing
the atlas layer — ask the user to set up the speckle-atlas checkout above
this repo before acting on that decision.

Shared skills, MCP definitions, and conventions change **in the speckle-atlas
repo via PR** — never by editing synced outputs (`.agents/skills`,
`.claude/skills`, `.mcp.json`, `.codex/config.toml`, this block) or forking a
local copy in this repo. A repo-local skill with a shared skill's name fails
the sync (ADR-0008); there is no override.

<!-- atlas:shared:end -->
