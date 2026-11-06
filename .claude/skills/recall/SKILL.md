---
name: recall
description: "Answer from memory (query). Use before acting on anything that involves a person, topic, client, project or past decision, and whenever asked 'what do we know about X', 'what did we decide', 'when', 'who', 'did I tell you', 'remind me'."
---

# Recall

Memory is pulled on demand. Read as little as needed, in this order:

1. **Index**: `memory/index.md` (already in context from the session status). Find candidate pages by
   title, summary and type.
2. **Search** if the index isn't enough: `grep -ril "<name|alias|keyword>" memory/wiki` (aliases live in
   frontmatter), then `grep -rl` in `memory/raw` as a last resort.
3. **Pages**: open the matching pages and follow their `[[links]]` one hop when relevant. The synthesis
   is the current truth; the evidence log tells you when and from where.
4. **Raw** only to verify a quote, a number or a contradiction.

Answer:

- Cite pages: "Invoices go by email ([[PER-003]], since 2026-02-10)".
- Say what memory doesn't know, or what is `reviewed: false`, instead of guessing. Offer to find out.
- Superseded decisions are history: answer with the active one.

File it back: if the answer took real digging, combined several pages, or the owner corrected you,
run `remember` (a synthesis on a `topic` page, or a `lesson` for a correction) so next time it's one
lookup. Log notable lookups with `python3 tools/memory.py log recall "<question>"`.
