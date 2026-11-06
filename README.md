# Teo Agent Boilerplate

A template repo for [Claude Code](https://claude.com/claude-code) that turns any fresh clone into a
specific agent (bookkeeper, marketer, support, research assistant, anything) with a durable memory
that grows without bloating its context.

Open it once: the agent interviews its owner, writes its own identity, rules and first tasks, then
works session after session, remembering everything that matters.

By Teo Dagher.

## Quickstart

1. **Create your copy**: click *Use this template* on GitHub, or
   `gh repo create my-agent --template <owner>/teo-agent-boilerplate --private --clone`
2. **Open Claude Code** in the folder: `cd my-agent && claude`
3. **Say "onboard me"**. Answer one question, then one batch of eight. The agent fills `CLAUDE.md`,
   `agent.json` and its first memory pages, checks them, and commits.

From then on, talk to it or drop files in `memory/inbox/`.

Requirements: Claude Code, `git`, `python3` 3.9+ (stdlib only, nothing to install).

## How memory works

```
 you / tools / chat ──► memory/inbox/          drop zone
                             │  tools/memory.py file   (verbatim, renamed by date)
                             ▼
                        memory/raw/            immutable sources, kept forever
                             │  remember skill  (targeted deltas + evidence lines)
                             ▼
                        memory/wiki/           compiled pages, one per thing:
                          people/ topics/ decisions/ sources/ procedures/ lessons/ tasks/
                             │  tools/memory.py index
                             ▼
                        memory/index.md        one line per page  ──► loaded every session
                        memory/log.md          what happened, append-only
```

**Why it's effectively unlimited.** Context only ever holds `CLAUDE.md`, the index and a short status
(identity, inbox, open tasks, last log lines), injected by the SessionStart hook. Everything else is
pulled on demand by the `recall` skill: index → page → raw. The raw layer keeps the truth forever;
the wiki compiles it into current, cited pages; the index stays small at one line per page.

**Page types.** `person` (anyone the agent deals with), `topic` (any subject, project, account: the
general bucket), `decision` (what was decided, by whom, superseding older ones), `source` (one summary
per raw file), `procedure` (how-tos it learned), `lesson` (owner feedback: What / Why / How to apply,
which is how the agent improves), `task` (open loops with status and due date, so nothing is forgotten
between sessions).

**Every page** has a synthesis on top, edited in place, and an append-only evidence log underneath:

```
- 2026-02-10 · UPDATE · stated · Prefers invoices by email, not post — [[SRC-004]]
```

**Guard rails** (`.claude/settings.json`):

| Hook | Does |
|---|---|
| SessionStart | `memory.py status`: who the agent is, inbox, open tasks, recent log, index |
| PreToolUse (Write/Edit) | `memory.py guard`: blocks any write under `memory/raw/` |
| Stop | `memory.py lint --hook`: rebuilds the index, blocks the turn if memory is broken |

Lint checks frontmatter, IDs vs filenames, broken `[[links]]`, evidence line format, task statuses
and due dates, and (with git) that raw files and evidence lines were not changed since the last commit.

## What's in the repo

| Path | What it is |
|---|---|
| `CLAUDE.md` | The agent's manual: first-run trigger, identity, never-break rules, memory, working loop, self-improvement |
| `agent.json` | Name, role, owner, who it serves, language, timezone, channels, tools |
| `.claude/skills/` | `onboarding` (once), `remember` (ingest), `recall` (query), `tidy` (maintenance) |
| `.claude/rules/memory-writing.md` | Page format, evidence log, citations, superseding, secrets |
| `templates/` | One skeleton per page type, used by `memory.py new` |
| `tools/memory.py` | `new`, `file`, `log`, `index`, `lint`, `status`, `guard` |
| `memory/` | inbox, raw, wiki, index, log |

## Customize

- **Re-onboard or adjust**: edit `CLAUDE.md` §1/§2 by asking the agent; it logs each change as a decision.
- **Add a job**: ask the agent to write a skill in `.claude/skills/<job>/SKILL.md` (one skill per job),
  or a `procedure` page for lighter how-tos.
- **Add tools**: MCP servers in `.mcp.json` or Claude Code settings; list them in `agent.json`.
- **Add a page type**: a template in `templates/`, a line in `TYPES` in `tools/memory.py`, a folder
  in `memory/wiki/`, a row in the rules table.

## Scaling notes (don't build these early)

- Index past ~400 lines: split it per type (one index per wiki folder, the root index lists them).
  Lint warns when it's time.
- Thousands of pages: add local search (BM25 or embeddings) as a derived index, never the source of truth.
- Many raw files: subfolders per year under `memory/raw/`.

Inspired by Andrej Karpathy's "LLM wiki" idea: the model writes and maintains the wiki; the human
curates sources and asks questions.
