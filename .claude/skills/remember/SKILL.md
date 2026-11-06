---
name: remember
description: "Write new information into memory (ingest). Use whenever something new arrives: a file in memory/inbox/, a pasted document or message, a fact or decision the owner states in chat, an answer from a tool, a promise you made, owner feedback or a correction. Triggers: 'remember', 'note that', 'add to memory', 'process the inbox', 'from now on'."
---

# Remember

Rule: every piece of new information is a **source**. Keep it verbatim in `memory/raw/`, then compile
what matters into wiki pages. Format rules: `.claude/rules/memory-writing.md`.

## 1. Keep the source

- A file: put it in `memory/inbox/` if it isn't there.
- A chat statement or pasted text: write it to `memory/inbox/<slug>.md` with who said it, when, and
  the exact words.
- File it: `python3 tools/memory.py file memory/inbox/<file> --date <event date> --kind <kind> --slug <slug>`.
  kind: chat, email, notes, transcript, doc, sheet, export, contract, image, audio, other.
- Trivial chit-chat is not a source. When unsure, keep it: raw is cheap.

## 2. Summarize it

`python3 tools/memory.py new source "<title>"`. Fill `raw:` (file name), `date`, `from`, `summary`,
link the raw file by stem, and summarize. Evidence lines elsewhere will cite this `SRC-###`.

## 3. Compile targeted deltas

For each fact that matters (people, topics, decisions, commitments, dates, numbers, preferences):

1. Find the page: index + `grep -ril "<name or alias>" memory/wiki`. None → `memory.py new <type> "Title"`.
2. Decide ADD / UPDATE / SUPERSEDE / nothing by comparing with the page.
3. Edit the synthesis sentence(s) that changed, bump `updated:`, add aliases, then append the evidence line:
   `- YYYY-MM-DD · ADD · stated · Jane prefers invoices by email — [[SRC-004]]`
4. Routing:
   - Something decided → `decision` page (a change of mind → new page with `supersedes:`).
   - Something to do, chase or wait for → `task` page (`status`, `due`, `owner`). Done → `status: done`.
   - Owner feedback or correction → `lesson` page: **What** / **Why** / **How to apply**; `summary` = the
     rule in one line. If it changes a hard rule, propose the CLAUDE.md §2 edit too (§6).
   - A how-to you worked out → `procedure` page.
5. Secrets: never copied; write "credential present in source".

Touch only what the source changes. Don't rewrite pages.

## 4. Close

1. `python3 tools/memory.py log remember "<source title>: <pages touched>"`
2. `python3 tools/memory.py index` then `python3 tools/memory.py lint` (0 errors).
3. `git add memory && git commit -m "memory: <what was learned>"`
4. Tell the owner in one line what changed, if they're there.
