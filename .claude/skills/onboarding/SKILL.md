---
name: onboarding
description: "Run ONCE to turn this template into a specific agent with its owner. Use when CLAUDE.md or agent.json still hold _TODO: placeholders (status says NOT ONBOARDED), or when the user says 'onboard me', 'set up', 'set yourself up' or 'get started'. Skip if the owner says they are working on the template itself."
---

# Onboarding

Turn a fresh clone into a working agent in one short conversation. Ask, then do all the writing
yourself. The `_TODO:` placeholders are the state: keep any already filled, ask only for the rest.

## Step 0: one question first

> "Are we creating a new agent from scratch, or do you have existing material I should learn from
> (documents, notes, an old prompt, a previous assistant's memory)?"

Existing material → ask them to paste it or give file paths. Read it before Step 1 so you can
propose answers ("here's what I gathered, correct me") instead of asking blind.

## Step 1: one batch of questions

One message, numbered; rough answers are fine:

1. **Role and mission**: what am I, what am I for, what's my name?
2. **Owner**: who are you, how do I reach you?
3. **Who I serve**: only you, a team, customers? Who may talk to me?
4. **Success**: what does a great month with me look like?
5. **Hard rules**: what must I never do? What must I always ask you first?
6. **Tools and channels**: which tools, accounts, MCP servers, channels? Timezone?
7. **Tone and language**
8. **First 3 jobs**

One follow-up at most, only if hard rules or who may instruct are unclear. Otherwise pick sensible
defaults and say so in the recap.

## Step 2: write the agent

1. `CLAUDE.md`: §0 → `Onboarded on YYYY-MM-DD with <owner>.`; §1 every line; §2 the owner's rules
   in imperative form (keep the safe defaults unless the owner removes one, then log a decision).
2. `agent.json`: every field; `channels` and `tools` as lists of short strings.
3. Memory:
   - File the answers verbatim: `python3 tools/memory.py file --text - --date <today> --kind chat --slug onboarding-answers`
     with the owner's words on stdin (heredoc).
   - `new person "<owner>"`, `new decision "Agent created"` (who decided, role, mission), a `new lesson`
     per working preference already stated, a `new topic` or `new org` per main subject with facts.
     Fill `summary`, and add evidence lines citing `[[raw/<date>_chat_onboarding-answers.md]]`.
   - `memory/now.md`: the first jobs under **Next** (or **Focus** for the one to start with), with `due:`
     if given.

## Step 3: import existing material (only if Step 0 said so)

For each document or paste: run `remember`, oldest first. Rules from an old prompt or memory become
`lesson` pages or §2 rules (ask which when unclear); facts go to the wiki like any source.

## Step 4: finish

1. `python3 tools/memory.py log setup "Onboarded as <name>, <role>"` and `python3 tools/memory.py index`.
2. `python3 tools/memory.py lint`: 0 errors and no "not onboarded" line. Fix and rerun.
3. Recap in a few lines: who I am, who I serve, hard rules, first jobs, defaults picked. Then: "Talk to
   me or hand me files; I remember what matters and pick up `now.md` every session."
4. `git add -A && git commit -m "onboarding: <name>, <role>"`, then ask whether to start the first job.
