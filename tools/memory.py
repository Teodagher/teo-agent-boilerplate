#!/usr/bin/env python3
"""Agent memory: deterministic bookkeeping for the agent's wiki.

The agent writes knowledge; this script owns what must be deterministic:
IDs, file placement, the generated index, the log, lint and the hooks.
Stdlib only. Runs from anywhere: paths resolve from the repo root.

  python3 tools/memory.py new <type> "Title" [--slug s]
  python3 tools/memory.py file <path> --date YYYY-MM-DD --kind <kind> --slug <slug>
  python3 tools/memory.py log <op> "title"
  python3 tools/memory.py index
  python3 tools/memory.py lint [--hook]
  python3 tools/memory.py status
  python3 tools/memory.py guard          # PreToolUse hook (reads hook JSON on stdin)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEM = ROOT / "memory"
WIKI, RAW, INBOX = MEM / "wiki", MEM / "raw", MEM / "inbox"
INDEX, LOG = MEM / "index.md", MEM / "log.md"
TEMPLATES = ROOT / "templates"

# type -> (ID prefix, folder under memory/wiki/, index heading). Order = index order.
TYPES = {
    "lesson": ("LES", "lessons", "Lessons (owner feedback: apply these)"),
    "task": ("TSK", "tasks", "Tasks"),
    "person": ("PER", "people", "People"),
    "topic": ("TOP", "topics", "Topics"),
    "decision": ("DEC", "decisions", "Decisions"),
    "procedure": ("PRO", "procedures", "Procedures"),
    "source": ("SRC", "sources", "Sources"),
}
RAW_KINDS = {"chat", "email", "notes", "transcript", "doc", "sheet", "export",
             "contract", "image", "audio", "other"}
LOG_OPS = {"setup", "remember", "recall", "tidy", "decision", "update"}
TASK_STATUS = {"todo", "doing", "waiting", "done"}
DECISION_STATUS = {"active", "superseded"}
REQUIRED = ("id", "type", "title", "updated", "reviewed")
PLACEHOLDER = "_TODO:"
INDEX_SPLIT_AT = 400  # lines; past this, split the index per type (see README, scaling)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`|<!--.*?-->", re.S)  # examples, not content
EVIDENCE_RE = re.compile(
    r"^- \d{4}-\d{2}-\d{2} · (ADD|UPDATE|SUPERSEDE) · "
    r"(stated|documented|observed|decided|inferred) · .+ — \[\[.+\]\].*$")
LOG_RE = re.compile(r"^- \d{4}-\d{2}-\d{2} \d{2}:\d{2} · \w+ · .+$")


def today() -> str:
    return dt.date.today().isoformat()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:60].rstrip("-") or "untitled"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


# ------------------------------------------------------------------ pages

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Flat YAML only: `key: value` and `key: [a, b]`. Trailing ` # comments` ignored."""
    if not text.startswith("---\n") or (end := text.find("\n---", 4)) == -1:
        return {}, text
    meta = {}
    for line in text[4:end].splitlines():
        line = line.split(" #", 1)[0].rstrip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            meta[key.strip()] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = val.strip("'\"")
    return meta, text[end + 4:].lstrip("\n")


def evidence_bullets(body: str) -> list[str] | None:
    """Bullets of `## Evidence log` (None if the section is missing)."""
    m = re.search(r"^## Evidence log[ \t]*$(.*?)(?=^## |\Z)", body, re.S | re.M)
    if not m:
        return None
    section = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
    return [l.rstrip() for l in section.splitlines() if l.startswith("- ")]


class Page:
    def __init__(self, path: Path):
        self.path, self.stem = path, path.stem
        self.meta, self.body = parse_frontmatter(path.read_text(encoding="utf-8"))
        self.links = sorted({l.strip() for l in LINK_RE.findall(CODE_RE.sub("", self.body))})
        self.evidence = evidence_bullets(self.body)

    def get(self, key: str, default: str = "") -> str:
        v = self.meta.get(key, default)
        return ", ".join(v) if isinstance(v, list) else v


def load_pages() -> list[Page]:
    return [Page(p) for p in sorted(WIKI.rglob("*.md"))]


# ------------------------------------------------------------------ commands

def cmd_new(a) -> None:
    if a.type not in TYPES:
        die(f"unknown type {a.type!r}; one of: {', '.join(TYPES)}")
    prefix, folder, _ = TYPES[a.type]
    nums = [int(m.group(1)) for p in (WIKI / folder).glob(f"{prefix}-*.md")
            if (m := re.match(rf"{prefix}-(\d+)", p.name))]
    pid = f"{prefix}-{max(nums, default=0) + 1:03d}"
    path = WIKI / folder / f"{pid}-{a.slug or slugify(a.title)}.md"
    text = (TEMPLATES / f"{a.type}.md").read_text(encoding="utf-8")
    for k, v in {"id": pid, "title": a.title, "today": today()}.items():
        text = text.replace("{{" + k + "}}", v)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(rel(path))


def cmd_file(a) -> None:
    src = Path(a.path).resolve()
    if not src.is_file():
        die(f"no such file: {a.path}")
    if not DATE_RE.match(a.date):
        die("--date must be YYYY-MM-DD (the date of the event, not today)")
    if a.kind not in RAW_KINDS:
        die(f"--kind must be one of: {', '.join(sorted(RAW_KINDS))}")
    dest = RAW / f"{a.date}_{a.kind}_{slugify(a.slug)}{src.suffix.lower()}"
    if dest.exists():
        die(f"{rel(dest)} already exists; raw files are never overwritten (pick another --slug)")
    if src.is_relative_to(RAW):
        die("already in memory/raw/")
    # Inbox items move (the inbox empties); files from elsewhere are copied, never deleted.
    (shutil.move if src.is_relative_to(INBOX) else shutil.copy2)(src, dest)
    print(rel(dest))


def append_log(op: str, title: str) -> None:
    line = f"- {dt.datetime.now():%Y-%m-%d %H:%M} · {op} · {title.strip()}\n"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())


def cmd_log(a) -> None:
    if a.op not in LOG_OPS:
        die(f"op must be one of: {', '.join(sorted(LOG_OPS))}")
    append_log(a.op, a.title)


def build_index(pages: list[Page]) -> str:
    L = ["# Memory index", "",
         "<!-- Generated by `python3 tools/memory.py index`. Do not edit by hand. -->",
         "One line per page. Open a page only when the task needs it.", ""]
    for type_, (_, _, heading) in TYPES.items():
        group = [p for p in pages if p.get("type") == type_]
        if type_ == "task":  # open tasks first, by due date
            group.sort(key=lambda p: (p.get("status") == "done", p.get("due") or "9999", p.stem))
        L += [f"## {heading} ({len(group)})", ""]
        for p in group:
            tags = []
            if type_ == "task":
                tags = [p.get("status") or "?"] + ([f"due {p.get('due')}"] if p.get("due") else [])
            elif type_ == "decision" and p.get("status") == "superseded":
                tags = ["superseded"]
            tag = f" ({' · '.join(tags)})" if tags else ""
            L.append(f"- [[{p.stem}]]{tag} — {p.get('summary') or p.get('title')}")
        L += (["_none yet_"] if not group else []) + [""]
    return "\n".join(L).rstrip() + "\n"


def cmd_index(a=None, quiet: bool = False) -> None:
    new = build_index(load_pages())
    old = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    if new != old:
        INDEX.write_text(new, encoding="utf-8")
    if not quiet:
        print(f"{rel(INDEX)}: {new.count(chr(10))} lines" + (" (unchanged)" if new == old else ""))


def git(*args: str) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
        return r.stdout if r.returncode == 0 else None
    except FileNotFoundError:
        return None


def not_onboarded() -> bool:
    if PLACEHOLDER in (ROOT / "CLAUDE.md").read_text(encoding="utf-8"):
        return True
    return "TODO" in (ROOT / "agent.json").read_text(encoding="utf-8")


def lint() -> tuple[list[str], list[str], list[str]]:
    """Returns (errors, warnings, infos). Errors block the Stop hook."""
    E, W, I = [], [], []
    pages = load_pages()
    known = {p.stem for p in pages} | {p.get("id") for p in pages}
    known |= {f.stem for f in RAW.iterdir()} | {f.name for f in RAW.iterdir()}
    ids: dict[str, str] = {}
    for p in pages:
        where = rel(p.path)
        for k in REQUIRED:
            if not p.get(k):
                E.append(f"{where}: missing frontmatter `{k}`")
        pid, type_ = p.get("id"), p.get("type")
        if type_ not in TYPES:
            E.append(f"{where}: unknown type {type_!r}")
        else:
            prefix, folder, _ = TYPES[type_]
            if p.path.parent != WIKI / folder:
                E.append(f"{where}: a {type_} page belongs in memory/wiki/{folder}/")
            if not re.fullmatch(rf"{prefix}-\d{{3,}}", pid or ""):
                E.append(f"{where}: id {pid!r} should look like {prefix}-001")
        if pid and not p.stem.startswith(pid + "-"):
            E.append(f"{where}: filename must start with its id `{pid}-`")
        if pid in ids:
            E.append(f"{where}: duplicate id {pid} (also {ids[pid]})")
        ids[pid] = where
        if p.get("updated") and not DATE_RE.match(p.get("updated")):
            E.append(f"{where}: `updated` must be YYYY-MM-DD")
        if p.get("reviewed") not in ("true", "false"):
            E.append(f"{where}: `reviewed` must be true or false")
        if not p.get("summary"):
            W.append(f"{where}: empty `summary` (the index shows the title instead)")
        for link in p.links:
            if link not in known:
                E.append(f"{where}: broken link [[{link}]]")
        if p.evidence is None:
            E.append(f"{where}: missing `## Evidence log` section")
        for b in p.evidence or []:
            if not EVIDENCE_RE.match(b):
                E.append(f"{where}: bad evidence line (see .claude/rules/memory-writing.md): {b[:90]}")
        if type_ == "task":
            if p.get("status") not in TASK_STATUS:
                E.append(f"{where}: task status must be one of {sorted(TASK_STATUS)}")
            if p.get("due") and not DATE_RE.match(p.get("due")):
                E.append(f"{where}: `due` must be YYYY-MM-DD or empty")
            if p.get("status") != "done" and p.get("due") and p.get("due") < today():
                W.append(f"{where}: overdue (due {p.get('due')})")
        if type_ == "decision" and p.get("status") not in DECISION_STATUS:
            E.append(f"{where}: decision status must be active or superseded")
    # Append-only checks against the last commit (skipped outside git).
    changed = git("diff", "--name-status", "HEAD", "--", "memory/")
    for line in (changed or "").splitlines():
        status, path = line.split("\t")[0], line.split("\t")[-1]
        if path.startswith("memory/raw/") and status[0] in "MD":
            E.append(f"{path}: raw files are immutable (modified/deleted since last commit); restore it")
        elif path.startswith("memory/wiki/") and path.endswith(".md"):
            if status[0] == "D":
                E.append(f"{path}: wiki pages are never deleted; supersede or merge instead")
            elif status[0] == "M":
                old = evidence_bullets(parse_frontmatter(git("show", f"HEAD:{path}") or "")[1]) or []
                new = set(evidence_bullets(Page(ROOT / path).body) or [])
                for b in old:
                    if b not in new:
                        E.append(f"{path}: evidence log is append-only; removed/edited line: {b[:80]}")
    if LOG.exists():
        for n, l in enumerate(LOG.read_text(encoding="utf-8").splitlines(), 1):
            if l.startswith("- ") and not LOG_RE.match(l):
                W.append(f"memory/log.md:{n}: line not written by `memory.py log`")
    if INDEX.exists() and INDEX.read_text(encoding="utf-8") != build_index(pages):
        E.append("memory/index.md is stale: run `python3 tools/memory.py index`")
    if INDEX.exists() and INDEX.read_text(encoding="utf-8").count("\n") > INDEX_SPLIT_AT:
        W.append(f"memory/index.md is over {INDEX_SPLIT_AT} lines: time to split it per type (README, scaling)")
    if not_onboarded():
        I.append("not onboarded yet: CLAUDE.md / agent.json still hold TODO placeholders; run the onboarding skill")
    return E, W, I


def cmd_lint(a) -> None:
    if a.hook:
        try:
            payload = json.load(sys.stdin)
        except Exception:
            payload = {}
        cmd_index(quiet=True)  # self-heal the generated index every turn
        errors, _, _ = lint()
        if errors and not payload.get("stop_hook_active"):
            reason = "Memory lint failed; fix these before finishing:\n" + "\n".join(f"  - {e}" for e in errors)
            print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)
    errors, warnings, infos = lint()
    for tag, items in (("error", errors), ("warning", warnings), ("info", infos)):
        for i in items:
            print(f"{tag}: {i}")
    print(f"lint: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


def cmd_status(a) -> None:
    if not_onboarded():
        print("## Agent: NOT ONBOARDED. Do no other work: run the onboarding skill first (the owner can say \"onboard me\").")
    else:
        c = json.loads((ROOT / "agent.json").read_text(encoding="utf-8"))
        owner = c.get("owner", {}).get("name", "?")
        print(f"## Agent: {c.get('name')}, {c.get('role')} · serves {c.get('serves')} · owner {owner} "
              f"· {c.get('language')} · {c.get('timezone')} · today {today()}")
    inbox = [f for f in INBOX.iterdir() if f.name not in ("README.md", ".gitkeep")]
    if inbox:
        print(f"\nInbox: {len(inbox)} file(s) waiting; run the remember skill: " + ", ".join(f.name for f in inbox[:10]))
    tasks = [p for p in load_pages() if p.get("type") == "task" and p.get("status") != "done"]
    tasks.sort(key=lambda p: (p.get("due") or "9999", p.stem))
    print(f"\n## Open tasks ({len(tasks)})")
    for p in tasks[:15]:
        due = p.get("due")
        flag = " OVERDUE" if due and due < today() else ""
        print(f"- [[{p.stem}]] {p.get('status')}{f' · due {due}' if due else ''}{flag} — {p.get('title')}")
    if not tasks:
        print("_none_")
    log = LOG.read_text(encoding="utf-8").splitlines() if LOG.exists() else []
    print("\n## Recent log")
    print("\n".join([l for l in log if l.startswith("- ")][-5:]) or "_empty_")
    if INDEX.exists():
        lines = INDEX.read_text(encoding="utf-8").splitlines()
        print("\n" + "\n".join(lines[:INDEX_SPLIT_AT]))
        if len(lines) > INDEX_SPLIT_AT:
            print(f"... index truncated at {INDEX_SPLIT_AT} lines; read memory/index.md")


def cmd_guard(a) -> None:
    """PreToolUse hook for Write|Edit|MultiEdit|NotebookEdit: memory/raw/ is immutable."""
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    ti = data.get("tool_input") or {}
    target = ti.get("file_path") or ti.get("notebook_path")
    if target:
        p = Path(target)
        p = (p if p.is_absolute() else Path(data.get("cwd") or ROOT) / p).resolve()
        if p.is_relative_to(RAW.resolve()):
            print("memory/raw/ is immutable: never write or edit there. Put the file in memory/inbox/, "
                  "then `python3 tools/memory.py file ...`. Record corrections in the wiki.", file=sys.stderr)
            sys.exit(2)
    sys.exit(0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new", help="create a page from templates/<type>.md with the next ID")
    s.add_argument("type"); s.add_argument("title"); s.add_argument("--slug")
    s.set_defaults(fn=cmd_new)
    s = sub.add_parser("file", help="move an inbox file (or copy any file) into memory/raw/")
    s.add_argument("path"); s.add_argument("--date", required=True)
    s.add_argument("--kind", required=True); s.add_argument("--slug", required=True)
    s.set_defaults(fn=cmd_file)
    s = sub.add_parser("log", help="append a line to memory/log.md")
    s.add_argument("op"); s.add_argument("title")
    s.set_defaults(fn=cmd_log)
    sub.add_parser("index", help="regenerate memory/index.md").set_defaults(fn=cmd_index)
    s = sub.add_parser("lint", help="check memory structure; exit 1 on errors")
    s.add_argument("--hook", action="store_true", help="Stop-hook mode: JSON block decision on errors")
    s.set_defaults(fn=cmd_lint)
    sub.add_parser("status", help="session-start context").set_defaults(fn=cmd_status)
    sub.add_parser("guard", help="PreToolUse hook: block writes under memory/raw/").set_defaults(fn=cmd_guard)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
