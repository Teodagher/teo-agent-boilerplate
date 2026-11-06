---
name: onboarding
description: "Run ONCE to turn this template into a specific agent with its owner. Use when CLAUDE.md or agent.json still hold TODO placeholders (the session status says NOT ONBOARDED), or when the user says 'onboard me', 'set up', 'set yourself up', 'get started' or 'who are you supposed to be'."
---

# Onboarding

Turn a fresh clone into a working agent in one short conversation. Ask, then do all the writing
yourself: the owner never edits a file. The TODO placeholders are the state: when none are left,
onboarding is done. (Some may already be filled if a previous onboarding stopped halfway: keep
those, ask only for what's missing.)

## Step 0: one question first

> "Are we creating a new agent from scratch, or do you have existing material I should learn from
> (documents, notes, an old prompt, exports, a previous assistant's memory)?"

- From scratch → Step 1.
- Existing material → ask them to drop it in `memory/inbox/` (or paste it), then Step 1. You'll
  import it in Step 3. Read it before Step 1 if it's already there, so you can propose answers
  ("here's what I gathered, correct me") instead of asking blind.

## Step 1: one batch of questions

Send these together in one message, numbered, and accept rough answers:

1. **Role and mission**: what am I, in one line? What am I for? What's my name?
2. **Owner**: who are you, and how do I reach you (email, chat...)?
3. **Who I serve**: only you, a team, customers? Who may talk to me?
4. **Success**: what does a great month with me look like?
5. **Hard rules**: what must I never do? What must I always ask you first?
6. **Tools and channels**: which tools, accounts, MCP servers or channels will I use? Timezone?
7. **Tone and language**: how should I sound, in which language(s)?
8. **First 3 jobs**: what should I do first?

If an answer is vague on something that matters (hard rules, who may instruct), ask one follow-up.
Otherwise use sensible defaults and say so in the recap.

## Step 2: write the agent

1. `CLAUDE.md`:
   - §0: replace the TODO line with `Onboarded on YYYY-MM-DD with <owner>.`
   - §1: fill every line from the answers.
   - §2: replace the owner's-rules TODO with their rules, one per line, in imperative form. Keep the
     safe defaults unless the owner explicitly removes one (then log it as a decision).
2. `agent.json`: fill every field (`channels` and `tools` as lists of short strings). No TODO left.
3. Memory, with `python3 tools/memory.py new ...` then editing each page:
   - Save the owner's answers verbatim: write them to `memory/inbox/onboarding-answers.md`, then
     `python3 tools/memory.py file memory/inbox/onboarding-answers.md --date <today> --kind chat --slug onboarding-answers`.
   - `new source "Onboarding answers"`: summary of the raw file, `raw:` its file name.
   - `new person "<owner name>"`: relation `owner`, contact, what they care about. Evidence lines cite the source.
   - `new decision "Agent created"`: who decided (the owner), role, mission, date; `status: active`.
   - One `new task` per first job: `status: todo`, `owner`, `due` if one was given.
   - A `new lesson` for any working preference already stated ("always cc me", "keep it short").
   - A `new topic` for each main subject, client or project they mentioned, only if it carries facts.
   - Every page: `summary:` filled, evidence lines in the exact format, `reviewed: true` for what the
     owner stated directly.

## Step 3: import existing material (only if Step 0 said so)

For each file in `memory/inbox/`: run the `remember` skill. Big batches: oldest first, and tell the
owner what you're importing. Existing assistant memories or prompts: their rules become `lesson`
pages or §2 rules (ask which when it's not obvious), their facts go to the wiki like any source.

## Step 4: finish

1. `python3 tools/memory.py log setup "Onboarded as <name>, <role>"`, then `python3 tools/memory.py index`.
2. `python3 tools/memory.py lint` must show 0 errors and no "not onboarded" info. Fix and rerun.
3. Recap to the owner in a few lines: who I am, who I serve, my hard rules, my first tasks, and any
   default you picked. Then the loop: "Talk to me or drop files in `memory/inbox/`. I remember
   everything important and pick up open tasks each session."
4. Commit: `git add -A && git commit -m "onboarding: <name>, <role>"`.
5. Ask whether to start on the first task now.
