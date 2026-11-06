# Teo Agent Boilerplate

A template repo for [Claude Code](https://claude.com/claude-code) that turns any fresh clone into a
specific agent (bookkeeper, marketer, support, research assistant, anything) with a durable memory
that grows without bloating its context. Open it once: the agent interviews its owner, writes its own
identity, rules and first jobs, then works session after session, remembering what matters.

By Teo Dagher. MIT licence: copy it, change it, share it.

It is also an **agent template** in the open agent template format (v0.2): `agent.yaml` describes
it, so a host such as [agent8](https://www.agent8.sh) can install it, ask the setup questions, and
update it later without touching what your agent has learned. Without a host it works exactly
like a normal template repo.

## Quickstart

1. **Create your copy**: *Use this template* on GitHub, or
   `gh repo create my-agent --template <owner>/teo-agent-boilerplate --private --clone`
2. **Open Claude Code** in it: `cd my-agent && claude`
3. **Say "onboard me"**: one question, then one batch of eight. The agent fills in `identity.md`,
   `LOCAL.md` and its first memory, checks it, and commits its own files (only if you want your
   memory in git: keep the repo private).

On the first run `tools/memory.py` copies the starting files from `seed/` (`identity.md`,
`LOCAL.md`, `memory/`), so there is nothing to set up by hand.

Requirements: Claude Code, `git`, `python3` 3.9+ (stdlib only). Codex works too, partially: it
reads `AGENTS.md` and the skills, but not the Claude Code hooks.

## Template files and your agent's own files

The repo keeps what makes the agent (instructions, skills, tools) apart from what belongs to
*your* agent, so the template can be improved and updated without ever overwriting it:

| Whose | Files | On a template update |
|---|---|---|
| **Template** | `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.agents/skills`, `templates/`, `tools/`, `agent.yaml`, `seed/` | replaced |
| **Your agent's own layer** | `identity.md` (who it is, owner, hard rules), `LOCAL.md` (its own rules and improvements), `skills/` (its own skills) | never touched |
| **Your agent's data** | `memory/` (and `logs/`, `exports/` if you add them) | never touched, never shared |

The agent improves itself by writing to its own layer, never to the template's files. None of
your agent's files exist in this repo: they start from `seed/` on the first run.

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

- **Small context, unlimited memory.** Each session loads only `AGENTS.md`, `identity.md`,
  `LOCAL.md` and a status (identity,
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
| SessionStart | `memory.py status` | copies missing starting files from `seed/`, then injects identity, overdue items, log, `now.md`, index head |
| PreToolUse | `memory.py guard` | blocks Write/Edit/MultiEdit/NotebookEdit under `memory/raw/` (and under `.agent8/template/` in a copy installed by agent8), and Bash commands that would write, move or delete there (only `memory.py file` may add files) |
| Stop | `memory.py lint --hook` | rebuilds the index; blocks the turn once if lint fails; errors still left go to stderr and `log.md` |

## What's in the repo

| Path | What it is |
|---|---|
| `AGENTS.md` | The manual: whose files are whose, first-run gate, never-break rules, session start, memory, working loop, self-improvement |
| `CLAUDE.md` | Three imports: `@AGENTS.md`, `@identity.md`, `@LOCAL.md` |
| `agent.yaml` | Template manifest: name, version, licence, setup questions, the data list (what never leaves your agent), requirements |
| `seed/` | Starting `identity.md`, `LOCAL.md` and `memory/`, copied on the first run |
| `.claude/skills/` | `onboarding` (once), `remember`, `recall`, `tidy` (`.agents/skills` points here, for Codex) |
| `.claude/rules/memory-writing.md` | Page format, evidence line, superseding, `now.md`, secrets |
| `templates/` | `entity.md`, `lesson.md`, `procedure.md`, used by `memory.py new` |
| `tools/memory.py` | `new`, `file`, `log`, `index`, `lint`, `status`, `commit`, `guard` |
| `LICENSE` | MIT |

## Customize

For **your agent** (its own layer, kept across template updates):

- **Change identity or rules**: ask the agent; it edits `identity.md` and logs each change as a decision.
- **Change how it works**: it writes the rule in `LOCAL.md`.
- **Add a job**: a skill in `skills/<job>/SKILL.md` (linked into `.claude/skills/` at the next
  session), or a `procedure` page for lighter how-tos.

For **the template** (when you are improving the boilerplate itself, for everyone):

- Edit `AGENTS.md`, the skills in `.claude/skills/`, `tools/`; add MCP servers in `.mcp.json`.
- **Add a page type**: a line in `TYPES` in `tools/memory.py` (folder + template).
- Bump `version` in `agent.yaml` and tag the release (`v0.2.1`) so hosts can offer the update.
- Check it with the format's validator (`validate.py template .`, from the format's reference tools).
- Tell your Claude session you are working on the template itself, so it skips onboarding. Running
  it here creates `identity.md`, `LOCAL.md` and `memory/` from `seed/`: never commit them to the
  template.

## Scaling notes (don't build early)

- Past ~200 index lines, session start shows only the head: split the index per type.
- Thousands of pages: add local search (BM25 or embeddings) as a derived index, never the source of truth.
