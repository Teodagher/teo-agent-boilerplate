# Raw sources (immutable)

The verbatim evidence behind everything in the wiki. Files arrive here only through
`python3 tools/memory.py file <path> --date --kind --slug`, never by hand.

- Name: `YYYY-MM-DD_<kind>_<slug>.<ext>`. The date is the event's date, not the filing date.
- kind: chat, email, notes, transcript, doc, sheet, export, contract, image, audio, other.
- Never edited, never deleted. A hook blocks writes here and lint flags any change since the
  last commit. Corrections go in the wiki as a SUPERSEDE evidence line.
- Secrets inside a source stay in the raw file only; the wiki says "credential present in source".
