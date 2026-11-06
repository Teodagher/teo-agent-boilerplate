#!/usr/bin/env python3
"""Agent memory bookkeeping. Stdlib only; paths resolve from the repo root.

  memory.py new <person|org|topic|decision|lesson|procedure> "Title" [--slug s]
  memory.py file <path> | --text "<text>|-"  --date YYYY-MM-DD --kind <kind> --slug <slug>
  memory.py log <op> "title"
  memory.py index | lint [--hook] | status
  memory.py guard        # PreToolUse hook: memory/raw/ is immutable
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "memory"
WIKI, RAW = MEM / "wiki", MEM / "raw"
INDEX, LOG, NOW = MEM / "index.md", MEM / "log.md", MEM / "now.md"
# type -> (folder, template, index heading). Order = index order.
TYPES = {
    "lesson": ("howto", "lesson", "Lessons (owner feedback: apply these)"),
    "procedure": ("howto", "procedure", "Procedures"),
    "person": ("entities", "entity", "People"),
    "org": ("entities", "entity", "Organizations"),
    "topic": ("entities", "entity", "Topics"),
    "decision": ("entities", "entity", "Decisions"),
}
KINDS = {"chat", "email", "notes", "transcript", "doc", "sheet", "export", "contract", "image", "audio", "other"}
LOG_OPS = {"setup", "remember", "recall", "tidy", "decision", "done", "lint"}
MARKER = "_TODO:"  # onboarding placeholders in CLAUDE.md and agent.json
MAX_LINES, MAX_CHARS = 200, 10_000  # Claude Code caps SessionStart hook output

DATE = r"\d{4}-\d{2}-\d{2}"
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`|<!--.*?-->", re.S)
EVIDENCE_RE = re.compile(rf"^- {DATE} · .+ — \[\[[^\]]+\]\]\s*$")
DUE_RE = re.compile(r"due:\s*(\S+)")


def today() -> str:
    return dt.date.today().isoformat()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:60].rstrip("-") or "untitled"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


class Page:
    def __init__(self, path: Path):
        self.path, self.stem = path, path.stem
        text = read(path)
        self.meta, self.body = {}, text
        if text.startswith("---\n") and (end := text.find("\n---", 4)) != -1:
            for line in text[4:end].splitlines():
                k, sep, v = line.partition(":")
                if sep:
                    self.meta[k.strip()] = v.strip()
            self.body = text[end + 4:]
        clean = CODE_RE.sub("", self.body)
        self.links = sorted({l.strip() for l in LINK_RE.findall(clean)})
        parts = re.split(r"^## Evidence log[ \t]*$", clean, maxsplit=1, flags=re.M)
        self.evidence = None if len(parts) < 2 else [l.rstrip() for l in parts[1].splitlines() if l.strip()]

    def get(self, k: str) -> str:
        return self.meta.get(k, "")


def pages() -> list[Page]:
    return [Page(p) for p in sorted(WIKI.rglob("*.md"))]


def onboarded() -> bool:
    return not any(MARKER in read(ROOT / f) for f in ("CLAUDE.md", "agent.json"))


# ------------------------------------------------------------------ commands

def cmd_new(a) -> None:
    if a.type not in TYPES:
        die(f"type must be one of: {', '.join(TYPES)}")
    folder, template, _ = TYPES[a.type]
    slug = slugify(a.slug or a.title)
    if any(p.stem == slug for p in pages()):
        die(f"a page named {slug} already exists: update it, or pass --slug")
    text = read(ROOT / "templates" / f"{template}.md")
    for k, v in {"title": a.title, "type": a.type, "today": today()}.items():
        text = text.replace("{{" + k + "}}", v)
    if a.type == "decision":
        text = text.replace("\nupdated:", "\nstatus: active\nupdated:", 1)
    path = WIKI / folder / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path.relative_to(ROOT))


def cmd_file(a) -> None:
    if not re.fullmatch(DATE, a.date):
        die("--date must be YYYY-MM-DD (the event's date)")
    if a.kind not in KINDS:
        die(f"--kind must be one of: {', '.join(sorted(KINDS))}")
    if (a.path is None) == (a.text is None):
        die("give either a file path or --text")
    src = Path(a.path).resolve() if a.path else None
    if src and not src.is_file():
        die(f"no such file: {a.path}")
    dest = RAW / f"{a.date}_{a.kind}_{slugify(a.slug)}{src.suffix.lower() if src else '.md'}"
    if dest.exists():
        die(f"{dest.name} already exists; raw files are never overwritten (pick another --slug)")
    if src:
        shutil.copy2(src, dest)  # the original is left where it was
    else:
        dest.write_text(sys.stdin.read() if a.text == "-" else a.text, encoding="utf-8")
    print(f"memory/raw/{dest.name}  (cite as [[raw/{dest.name}]])")


def append_log(op: str, title: str) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"- {dt.datetime.now():%Y-%m-%d %H:%M} · {op} · {' '.join(title.split())}\n")


def cmd_log(a) -> None:
    if a.op not in LOG_OPS:
        die(f"op must be one of: {', '.join(sorted(LOG_OPS))}")
    append_log(a.op, a.title)


def build_index(ps: list[Page]) -> str:
    L = ["# Memory index", "", "<!-- Generated by `python3 tools/memory.py index`. Do not edit. -->", ""]
    for type_, (_, _, heading) in TYPES.items():
        group = [p for p in ps if p.get("type") == type_]
        if group:
            L += [f"## {heading}", ""]
            for p in group:
                tag = (f" (merged into [[{p.get('merged_into')}]])" if p.get("merged_into")
                       else " (superseded)" if p.get("status") == "superseded" else "")
                L.append(f"- [[{p.stem}]]{tag} — {p.get('summary') or p.get('title')}")
            L.append("")
    if len(L) == 4:
        L += ["_Nothing remembered yet._", ""]
    return "\n".join(L).rstrip() + "\n"


def cmd_index(a=None) -> None:
    new = build_index(pages())
    if new != read(INDEX):
        INDEX.write_text(new, encoding="utf-8")
    if a is not None:
        print(f"memory/index.md: {new.count(chr(10))} lines")


def overdue() -> list[str]:
    return [l.strip() for l in read(NOW).splitlines()
            if (m := DUE_RE.search(l)) and re.fullmatch(DATE, m.group(1)) and m.group(1) < today()]


def lint() -> tuple[list[str], list[str]]:
    E, W = [], []
    ps = pages()
    names = {p.stem for p in ps}
    raws = {f.name for f in RAW.iterdir()} | {f.stem for f in RAW.iterdir()}
    seen: dict[str, Path] = {}
    for p in ps:
        where = str(p.path.relative_to(ROOT))
        if p.stem in seen:
            E.append(f"{where}: same name as {seen[p.stem].relative_to(ROOT)}; names are unique across the wiki")
        seen[p.stem] = p.path
        for k in ("title", "type", "updated"):
            if not p.get(k):
                E.append(f"{where}: missing frontmatter `{k}`")
        t = p.get("type")
        if t not in TYPES:
            E.append(f"{where}: type must be one of {', '.join(TYPES)}")
        elif p.path.parent != WIKI / TYPES[t][0]:
            E.append(f"{where}: a {t} page belongs in memory/wiki/{TYPES[t][0]}/")
        if p.get("updated") and not re.fullmatch(DATE, p.get("updated")):
            E.append(f"{where}: `updated` must be YYYY-MM-DD")
        if p.get("status") and p.get("status") not in ("active", "superseded"):
            E.append(f"{where}: status must be active or superseded")
        for k in ("supersedes", "superseded_by", "merged_into"):
            if p.get(k) and p.get(k) not in names:
                E.append(f"{where}: `{k}: {p.get(k)}` is not a page")
        if not p.get("summary") and not p.get("merged_into"):
            W.append(f"{where}: empty summary (the index shows the title instead)")
        for link in p.links:
            ok = link[4:] in raws if link.startswith("raw/") else link in names
            if not ok:
                E.append(f"{where}: broken link [[{link}]] (pages: [[slug]], sources: [[raw/<file>]])")
        if p.evidence is None:
            E.append(f"{where}: missing `## Evidence log` (last section)")
        for line in p.evidence or []:
            if line.startswith("## "):
                E.append(f"{where}: `{line}` comes after the evidence log, which must be the last section")
            elif not EVIDENCE_RE.match(line):
                E.append(f"{where}: bad evidence line, want `- YYYY-MM-DD · fact — [[source]]`: {line[:80]}")
    now = read(NOW)
    for h in ("## Focus", "## Waiting on", "## Next"):
        if not re.search(rf"^{h}\s*$", now, re.M):
            E.append(f"memory/now.md: missing `{h}` section")
    for m in DUE_RE.finditer(CODE_RE.sub("", now)):
        if not re.fullmatch(DATE, m.group(1)):
            E.append(f"memory/now.md: `due: {m.group(1)}` must be YYYY-MM-DD")
    W += [f"memory/now.md: overdue: {l}" for l in overdue()]
    if read(INDEX) != build_index(ps):
        E.append("memory/index.md is stale: run `python3 tools/memory.py index`")
    return E, W


def cmd_lint(a) -> None:
    if a.hook:  # Stop hook: rebuild the index, block once on errors, never loop
        try:
            payload = json.load(sys.stdin)
        except ValueError:
            payload = {}
        cmd_index()
        errors, _ = lint()
        if errors and payload.get("stop_hook_active"):
            print(f"memory lint: {len(errors)} error(s) left after a Stop block:\n" + "\n".join(errors), file=sys.stderr)
            append_log("lint", f"{len(errors)} error(s) left unfixed after Stop block; first: {errors[0]}")
        elif errors:
            reason = "Memory lint failed; fix before finishing:\n" + "\n".join(f"  - {e}" for e in errors)
            print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)
    errors, warnings = lint()
    for tag, items in (("error", errors), ("warning", warnings)):
        for i in items:
            print(f"{tag}: {i}")
    if not onboarded():
        print("info: not onboarded yet (_TODO: placeholders in CLAUDE.md / agent.json)")
    print(f"lint: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


def cmd_status(a) -> None:
    if not onboarded():
        out = ["## NOT ONBOARDED: run the onboarding skill before any other work (the owner can say "
               "\"onboard me\"), unless the owner says they are working on the template itself."]
    else:
        c = json.loads(read(ROOT / "agent.json"))
        out = [f"## {c.get('name')}, {c.get('role')} · serves {c.get('serves')} · owner "
               f"{c.get('owner', {}).get('name')} · {c.get('timezone')} · today {today()}"]
    out += [f"OVERDUE: {l}" for l in overdue()]
    log = [l for l in read(LOG).splitlines() if l.startswith("- ")][-3:]
    out += ["", "## Recent log", *(log or ["_empty_"]), "", *read(NOW).splitlines(), "", *read(INDEX).splitlines()]
    text, cut = "\n".join(out), False
    if len(out) > MAX_LINES:
        text, cut = "\n".join(out[:MAX_LINES]), True
    if len(text) > MAX_CHARS:
        text, cut = text[:text.rfind("\n", 0, MAX_CHARS - 100)], True
    print(text + ("\n... truncated: read memory/index.md for the rest." if cut else ""))


WRITE_RE = re.compile(r"""\b(rm|mv|cp|tee|truncate|touch|chmod|ln|dd|install|rsync)\b|sed\s+(-\w*\s+)*-i|>>?\s*["']?[^\s"']*memory/raw|\bgit\s+(rm|mv|checkout|restore)\b""")


def cmd_guard(a) -> None:
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    ti, raw = data.get("tool_input") or {}, RAW.resolve()
    blocked = False
    if data.get("tool_name") == "Bash":
        for seg in re.split(r"&&|\|\||;|\||\n", ti.get("command", "")):
            if "memory/raw" in seg and WRITE_RE.search(seg) and "tools/memory.py" not in seg:
                blocked = True
    elif target := ti.get("file_path") or ti.get("notebook_path"):
        p = Path(target)
        blocked = (p if p.is_absolute() else Path(data.get("cwd") or ROOT) / p).resolve().is_relative_to(raw)
    if blocked:
        print("memory/raw/ is immutable: never write, move or delete there. File sources with "
              "`python3 tools/memory.py file`; record corrections in the wiki.", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("type"); s.add_argument("title"); s.add_argument("--slug")
    s.set_defaults(fn=cmd_new)
    s = sub.add_parser("file"); s.add_argument("path", nargs="?"); s.add_argument("--text")
    for k in ("--date", "--kind", "--slug"):
        s.add_argument(k, required=True)
    s.set_defaults(fn=cmd_file)
    s = sub.add_parser("log"); s.add_argument("op"); s.add_argument("title"); s.set_defaults(fn=cmd_log)
    s = sub.add_parser("lint"); s.add_argument("--hook", action="store_true"); s.set_defaults(fn=cmd_lint)
    for name, fn in (("index", cmd_index), ("status", cmd_status), ("guard", cmd_guard)):
        sub.add_parser(name).set_defaults(fn=fn)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
