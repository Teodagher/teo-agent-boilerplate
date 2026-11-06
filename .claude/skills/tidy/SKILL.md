---
name: tidy
description: "Maintain memory (lint and clean-up). Use when the owner asks to tidy, clean, review or check memory, when lint warnings pile up, about once a week of active use, or when the index nears 400 lines."
---

# Tidy

Keep memory accurate and small enough to navigate. Never lose evidence: no deleted pages, no
deleted evidence lines, nothing touched in `memory/raw/`.

1. `python3 tools/memory.py lint`. Fix every error; read the warnings.
2. **Tasks**: overdue or stale (`updated` a month old and not done) → finish, re-date, set `waiting`
   with `waiting_on`, or ask the owner whether to close. Report what's waiting on others.
3. **Inbox**: anything left in `memory/inbox/` → `remember`.
4. **Contradictions**: pages with `## Open contradictions`, or two pages saying different things →
   resolve with the newest source (SUPERSEDE line) or list them for the owner.
5. **Duplicates**: same entity on two pages → merge into the older ID: move the synthesis, copy the
   other page's evidence lines (append, with their original dates), add its title to `aliases:`.
   Turn the newer page into a stub: `merged_into: <ID>` in frontmatter, one line "Merged into [[ID]]",
   keep its evidence log. Fix links that pointed to it.
6. **Orphans**: pages nothing links to and the index summary doesn't explain → link them from the
   right topic or person page.
7. **Long pages** (synthesis over ~150 lines): compress the synthesis into a tighter current state,
   moving history into a `## History` section or a dated sub-topic page. Keep the evidence log whole.
8. **Lessons**: two lessons saying the same thing → merge. A lesson that has become a standing rule →
   propose moving it into CLAUDE.md §2 (log a decision).
9. **Unreviewed**: list important `reviewed: false` pages and ask the owner to confirm the key ones.
10. `python3 tools/memory.py log tidy "<what changed>"`, `index`, `lint` (0 errors), commit
    `memory: tidy …`. Give the owner a 3-line report.

Scaling: when `memory/index.md` passes ~400 lines, propose splitting it per type (one index file per
folder, root index listing them) as a self-improvement decision (CLAUDE.md §6).
