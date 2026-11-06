---
name: tidy
description: "Maintain memory. Use when the owner asks to tidy, clean or review memory, when lint warnings pile up, or about weekly during active use."
---

# Tidy

Keep memory accurate and easy to navigate. Never delete a page or an evidence line, never touch `memory/raw/`.

1. `python3 tools/memory.py lint`: fix every error, read the warnings.
2. **now.md**: overdue or stale lines → do, re-date, move to Waiting on, or ask the owner. Durable facts
   in it → move to pages.
3. **Contradictions**: two pages disagree → `SUPERSEDES:` with the newest source, or ask the owner.
4. **Duplicates**: merge into the older page (synthesis, evidence lines with their original dates, the
   other title as an alias); the other becomes a stub: `merged_into: <slug>` and one line "Merged into
   [[slug]]", evidence log kept. Fix links to it.
5. **Orphans**: pages nothing links to → link them from the right topic, org or person.
6. **Long pages** (synthesis over ~150 lines): tighten the synthesis, move history to a dated topic
   page. The evidence log stays whole.
7. **Lessons**: merge repeats; a lesson that became a standing rule → propose moving it to CLAUDE.md §2
   (log a decision).
8. `python3 tools/memory.py log tidy "<what changed>"`, `index`, `lint`, commit `memory: tidy …`, then a
   3-line report to the owner.

Scaling: past ~200 index lines, session start shows only the head. When that hurts, propose one index
file per type with the root index listing them (a self-improvement decision, CLAUDE.md §6).
