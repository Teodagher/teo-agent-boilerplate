---
paths:
  - "memory/**"
  - "templates/**"
---

# Memory writing rules

`python3 tools/memory.py lint` enforces most of this. The Stop hook blocks the turn on lint errors.

## Page anatomy
- Create pages only with `python3 tools/memory.py new <type> "Title"`. It assigns the ID
  (`PER-001`, `TOP-001`, `DEC-001`, `SRC-001`, `PRO-001`, `LES-001`, `TSK-001`) and copies
  `templates/<type>.md`. IDs are never chosen by hand, reused or renumbered.
- Flat YAML frontmatter, lists as `[a, b]`. Required: `id`, `type`, `title`, `updated`, `reviewed`.
  Always fill `summary:` (one line: the index shows it every session) and keep `aliases:` current
  (every other name the entity goes by), so it is found again next time.
- Bump `updated:` on every edit.
- **Synthesis** = everything above `## Evidence log`. It states what is true now. Edit it in place
  with **targeted deltas**: change the sentences that changed. Never regenerate a whole page;
  repeated rewrites erode detail.
- **Evidence log** = append-only, oldest first. Never edit or delete a line (lint compares with the
  last commit). Exact format:

  `- YYYY-MM-DD · ADD|UPDATE|SUPERSEDE · stated|documented|observed|decided|inferred · fact — [[citation]]`

  - date: when the fact became true or was said, not when you wrote it.
  - ADD = new fact · UPDATE = more detail on a fact · SUPERSEDE = replaces an earlier line (quote the old value).
  - stated (someone said it) · documented (in a document) · observed (you saw it in data or a tool) ·
    decided (a decision) · inferred (your own conclusion: cite what it rests on).
  - citation: the `SRC-###` page of the source, or the raw file stem, or the page it comes from.
- Every claim in the synthesis traces to an evidence line. Mark your own conclusions in the synthesis
  with a `> [!inference]` callout.
- `reviewed: false` until the owner has confirmed the page. Don't present unreviewed facts that matter
  as confirmed.

## Links and citations
- Link with `[[ID]]` or the full file stem `[[PER-001-jane-doe]]`; `[[ID|label]]` for a short label.
  Raw files are linked by stem: `[[2026-01-31_email_invoice-dispute]]`. Lint flags broken links.
- Link generously between pages (person ↔ topic ↔ decision ↔ task). Links are what make memory compound.

## Write-time choices (per fact, before writing)
1. **Find the entity**: search `memory/index.md` and `aliases:` (`grep -ri "name" memory/wiki`). Exists →
   update that page (add any new alias). Doesn't → `memory.py new`.
2. **Compare** with what the page says: ADD, UPDATE, SUPERSEDE or nothing. Resolve contradictions now:
   the newest dated source wins and the old value stays in the log. If two sources conflict and
   neither is clearly newer, keep both under `## Open contradictions` and ask the owner.
3. **Never delete a page.** Obsolete → say so in the synthesis. Duplicate → merge into the older page,
   turn the other into a stub with `merged_into: <ID>` in its frontmatter and a one-line pointer.
4. **Decisions are never rewritten.** A change of mind is a new `DEC-` page with `supersedes:`; the old
   one gets `status: superseded` and `superseded_by:`.

## Where things go
| Information | Page type |
|---|---|
| Anyone the agent deals with | `person` |
| Any subject, project, account, client, product | `topic` (the general bucket) |
| Something decided, by whom, why | `decision` |
| One summary per ingested raw source | `source` |
| A how-to the agent learned | `procedure` |
| Owner feedback or a correction (What / Why / How to apply) | `lesson` |
| An open loop: something to do, chase or wait for | `task` (`status: todo|doing|waiting|done`, `due:`) |

## Secrets
Never copy a password, token, key, code or bank detail into the wiki, the log or a reply. Write
"credential present in source" and point to the raw file.
