# Teo Agent Boilerplate

A template repo for [Claude Code](https://claude.com/claude-code) that turns any fresh clone into a
specific agent (bookkeeper, marketer, support, research assistant, anything) with a durable memory
that grows without bloating its context. Open it once: the agent interviews its owner, writes its own
identity, rules and first jobs, then works session after session, remembering what matters.

By Teo Dagher.

## Quickstart

1. **Create your copy**: *Use this template* on GitHub, or
   `gh repo create my-agent --template <owner>/teo-agent-boilerplate --private --clone`
2. **Open Claude Code** in it: `cd my-agent && claude`
3. **Say "onboard me"**: one question, then one batch of eight. The agent fills `CLAUDE.md`,
   `agent.json` and its first memory, checks it, and commits.

Requirements: Claude Code, `git`, `python3` 3.9+ (stdlib only).

## How memory works

```
 owner / chat / files / tools
            │  memory.py file   (verbatim, named YYYY-MM-DD_<kind>_<slug>)
            ▼
     memory/raw/           immutable sources, kept forever
            │  remember skill   (targeted edits + evidence lines citing [[raw/...]])
            ▼
     memory/wiki/
       entities/           person | org | topic | decision   facts about things
       howto/              procedure | lesson                how to act
     memory/now.md         open loops: Focus / Waiting on / Next
     memory/index.md       one line per page (generated) ──► shown every session
     memory/log.md         what happened, append-only
```

- **Small context, unlimited memory.** Each session loads only `CLAUDE.md` and a status (identity,
  overdue items, recent log, `now.md`, the index head, capped at ~200 lines / 10k characters, the
  limit Claude Code puts on hook output). Everything else is pulled on demand by `recall`.
- **No inbox.** Sources mostly arrive through chat and tools, so they're filed straight to `raw/`
  (`memory.py file --text -` for a chat statement, or a path), and pages cite the raw file directly.
- **Types live in frontmatter**, not in folders: two folders, six types. Every page has a synthesis
  on top, edited in place, and an append-only evidence log as its last section:
  `- 2026-02-10 · Invoices go by email, never by post — [[raw/2026-02-10_chat_invoices.md]]`
- **Lessons make it improve**: each owner correction becomes a page (What / Why / How to apply) whose
  one-line rule is listed first in the index every session.

The page types borrow from three sources: Karpathy's
[LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) (raw sources compiled
into an interlinked wiki the model maintains), Anthropic's
[Claude Code memory](https://code.claude.com/docs/en/memory) types (user, feedback, project,
reference), and [LangMem](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/)'s
semantic / episodic / procedural split. In this repo, entities are semantic memory, howto pages are
procedural memory (lessons = feedback), and raw + log are the episodic record.

**Guard rails** (`.claude/settings.json`):

| Hook | Runs | Does |
|---|---|---|
| SessionStart | `memory.py status` | injects identity, overdue items, log, `now.md`, index head |
| PreToolUse | `memory.py guard` | blocks Write/Edit/MultiEdit/NotebookEdit under `memory/raw/`, and Bash commands that would write, move or delete there (only `memory.py file` may add files) |
| Stop | `memory.py lint --hook` | rebuilds the index; blocks the turn once if lint fails; errors still left go to stderr and `log.md` |

## What's in the repo

| Path | What it is |
|---|---|
| `CLAUDE.md` | First-run gate, identity, never-break rules, session start, memory, working loop, self-improvement |
| `agent.json` | Name, role, owner, who it serves, language, timezone, channels, tools |
| `.claude/skills/` | `onboarding` (once), `remember`, `recall`, `tidy` |
| `.claude/rules/memory-writing.md` | Page format, evidence line, superseding, `now.md`, secrets |
| `templates/` | `entity.md`, `lesson.md`, `procedure.md`, used by `memory.py new` |
| `tools/memory.py` | `new`, `file`, `log`, `index`, `lint`, `status`, `guard` |

## Customize

- **Change identity or rules**: ask the agent; it edits `CLAUDE.md` and logs each change as a decision.
- **Add a job**: a skill in `.claude/skills/<job>/SKILL.md`, or a `procedure` page for lighter how-tos.
- **Add tools**: MCP servers in `.mcp.json`, listed in `agent.json`.
- **Add a page type**: a line in `TYPES` in `tools/memory.py` (folder + template).

## Scaling notes (don't build early)

- Past ~200 index lines, session start shows only the head: split the index per type.
- Thousands of pages: add local search (BM25 or embeddings) as a derived index, never the source of truth.
