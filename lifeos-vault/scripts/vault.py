#!/usr/bin/env python3
"""Link-safe file operations for the LifeOS Obsidian vault. Standard library only.

  vault.py name TITLE KEYWORD... [--dir D] [--id ID]   print a free Denote path
  vault.py refs PATH                                   list notes linking to PATH
  vault.py move SRC DST                                move a file or folder, rewrite links
  vault.py trash PATH                                  move into .trash/, list now-broken links
  vault.py attachments NOTE                            list a note's non-Markdown references
  vault.py attach FILE DIR                             copy FILE into DIR, print its embed

Paths are vault-relative. The vault is $LIFEOS_VAULT, else ~/LifeOS.
"""
import argparse
import filecmp
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, unquote
from zoneinfo import ZoneInfo

VAULT = Path(os.environ.get("LIFEOS_VAULT", Path.home() / "LifeOS")).expanduser().resolve()
TEXT_SUFFIXES = {".md", ".canvas", ".base"}
STAMP = "%Y%m%dT%H%M%S"
# Target stops at |, # or ^; a table-escaped alias leaves a trailing backslash on it.
WIKI = re.compile(r"(!?)\[\[([^\]|#^]+?)(\\?)([#^][^\]|]*)?((?:\\?\|)[^\]]*)?\]\]")
MDLINK = re.compile(r"(!?)\[([^\]]*)\]\((<[^>]+>|[^)\s]+)\)")


def slug(title):
    title = unicodedata.normalize("NFC", title).lower()
    return re.sub(r"-+", "-", "".join(c if c.isalnum() else "-" for c in title)).strip("-")


def vault_files():
    for base, dirs, names in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in names:
            yield Path(base, name).relative_to(VAULT)


def notes():
    return [p for p in vault_files() if p.suffix in TEXT_SUFFIXES]


class Index:
    def __init__(self, files):
        self.paths = {p.as_posix() for p in files}
        self.by_name = {}
        for p in sorted(files, key=lambda p: (len(p.parts), p.as_posix())):
            self.by_name.setdefault(p.name, []).append(p.as_posix())

    def resolve(self, target, source):
        """Resolve a link target the way Obsidian does; return a vault path or None."""
        target = unquote(target).strip()
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            return None
        candidates = [target] if Path(target).suffix else [target + ".md", target]
        for t in candidates:
            relative = os.path.normpath((Path(source).parent / t).as_posix())
            for path in (t.lstrip("/"), relative):
                if path in self.paths:
                    return path
            hits = self.by_name.get(Path(t).name)
            if hits and "/" not in t:
                return hits[0]
            if hits:
                tail = [h for h in hits if h.endswith("/" + t)]
                if tail:
                    return tail[0]
        return None


def links(text):
    """Yield (match, kind, target) for every wiki and Markdown link."""
    for m in WIKI.finditer(text):
        yield m, "wiki", m.group(2)
    for m in MDLINK.finditer(text):
        yield m, "md", m.group(3).strip("<>")


def cmd_name(args):
    zone = ZoneInfo("Asia/Singapore")
    used = {p.name.split("--")[0] for p in vault_files()}
    if args.id:
        stamp = args.id
    else:
        moment = datetime.now(zone).replace(microsecond=0)
        while moment.strftime(STAMP) in used:
            moment += timedelta(seconds=1)
        stamp = moment.strftime(STAMP)
    keywords = "_".join(k for k in (re.sub(r"[^\w]", "", k.lower()) for k in args.keywords) if k)
    name = f"{stamp}--{slug(args.title)}__{keywords}.md"
    path = Path(args.dir) / name
    if (VAULT / path).exists():
        sys.exit(f"exists: {path}")
    print(path.as_posix())


def referrers(index, targets):
    """Return {note: [(match, kind, resolved)]} for links that resolve into targets."""
    found = {}
    for note in notes():
        text = (VAULT / note).read_text(encoding="utf-8", errors="replace")
        for m, kind, target in links(text):
            resolved = index.resolve(target, note.as_posix())
            if resolved in targets:
                found.setdefault(note, []).append((m, kind, resolved))
    return found


def members(path):
    full = VAULT / path
    if full.is_dir():
        return [p.relative_to(VAULT).as_posix() for p in full.rglob("*") if p.is_file()]
    return [Path(path).as_posix()]


def cmd_refs(args):
    index = Index(list(vault_files()))
    for note, hits in sorted(referrers(index, set(members(args.path))).items()):
        for m, _, _ in hits:
            print(f"{note}: {m.group(0)}")


def new_target(old_target, kind, new_path, index):
    new = Path(new_path)
    if kind == "md":
        return quote(new.as_posix(), safe="/")
    unique = len(index.by_name.get(new.name, [])) <= 1
    stem = new.with_suffix("") if new.suffix == ".md" else new
    if "/" not in old_target and unique:
        return stem.name if new.suffix == ".md" else new.name
    return stem.as_posix()


def cmd_move(args):
    src, dst = Path(args.src), Path(args.dst)
    if not (VAULT / src).exists():
        sys.exit(f"missing: {src}")
    if (VAULT / dst).exists():
        sys.exit(f"exists: {dst}")
    before = Index(list(vault_files()))
    mapping = {m: (dst / Path(m).relative_to(src)).as_posix() if (VAULT / src).is_dir() else dst.as_posix()
               for m in members(src)}
    hits = referrers(before, set(mapping))
    # A moved note's own relative Markdown links break even when their targets stay put.
    for moved in mapping:
        if Path(moved).suffix not in TEXT_SUFFIXES:
            continue
        text = (VAULT / moved).read_text(encoding="utf-8", errors="replace")
        known = {h[0].start() for h in hits.get(Path(moved), [])}
        for m, kind, target in links(text):
            resolved = before.resolve(target, moved)
            if kind == "md" and resolved and m.start() not in known and not target.startswith("/"):
                hits.setdefault(Path(moved), []).append((m, kind, resolved))
    (VAULT / dst).parent.mkdir(parents=True, exist_ok=True)
    os.rename(VAULT / src, VAULT / dst)
    after = Index(list(vault_files()))
    for note, found in hits.items():
        note_now = Path(mapping.get(note.as_posix(), note.as_posix()))
        text = (VAULT / note_now).read_text(encoding="utf-8")
        for m, kind, resolved in sorted(found, key=lambda h: h[0].start(), reverse=True):
            if kind == "wiki":
                target = new_target(m.group(2), kind, mapping[resolved], after)
                replacement = f"{m.group(1)}[[{target}{m.group(3)}{m.group(4) or ''}{m.group(5) or ''}]]"
            else:
                moved_to = mapping.get(resolved, resolved)
                target = moved_to if m.group(3).lstrip("<").startswith("/") else os.path.relpath(moved_to, note_now.parent)
                replacement = f"{m.group(1)}[{m.group(2)}]({quote(Path(target).as_posix(), safe='/.')})"
            text = text[:m.start()] + replacement + text[m.end():]
        (VAULT / note_now).write_text(text, encoding="utf-8")
        print(f"relinked {note_now} ({len(found)})")
    print(f"moved {src} -> {dst}")


def cmd_trash(args):
    path = Path(args.path)
    index = Index(list(vault_files()))
    hits = referrers(index, set(members(path)))
    destination = VAULT / ".trash" / path
    if destination.exists():
        destination = destination.with_name(f"{destination.name}.{datetime.now().strftime(STAMP)}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.rename(VAULT / path, destination)
    print(f"trashed {path} -> {destination.relative_to(VAULT)}")
    for note, found in sorted(hits.items()):
        if not (VAULT / note).exists():
            continue
        for m, _, _ in found:
            print(f"broken link in {note}: {m.group(0)}")


def cmd_attachments(args):
    note = Path(args.note)
    index = Index(list(vault_files()))
    text = (VAULT / note).read_text(encoding="utf-8")
    seen = set()
    for m, kind, target in links(text):
        raw = unquote(target).strip()
        suffix = Path(raw).suffix.lower()
        if raw in seen or not suffix or suffix in TEXT_SUFFIXES or re.match(r"^https?:", raw):
            continue
        seen.add(raw)
        resolved = index.resolve(raw, note.as_posix())
        if resolved:
            print(f"ok\t{resolved}\t{m.group(0)}")
        elif Path(raw.removeprefix("file://")).expanduser().is_absolute() and Path(raw.removeprefix("file://")).expanduser().exists():
            print(f"outside\t{Path(raw.removeprefix('file://')).expanduser()}\t{m.group(0)}")
        else:
            print(f"missing\t{raw}\t{m.group(0)}")


def cmd_attach(args):
    source = Path(args.file).expanduser().resolve()
    if not source.is_file():
        sys.exit(f"missing: {source}")
    index = Index(list(vault_files()))
    for existing in index.by_name.get(source.name, []):
        if filecmp.cmp(source, VAULT / existing, shallow=False):
            print(f"present\t{existing}\t![[{Path(existing).name}]]")
            return
    name, n = source.name, 1
    while name in index.by_name or (VAULT / args.dir / name).exists():
        name = f"{source.stem}-{n}{source.suffix}"
        n += 1
    destination = VAULT / args.dir / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"copied\t{destination.relative_to(VAULT)}\t![[{name}]]")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("name"); p.add_argument("title"); p.add_argument("keywords", nargs="+")
    p.add_argument("--dir", default="00-Inbox"); p.add_argument("--id"); p.set_defaults(run=cmd_name)
    p = sub.add_parser("refs"); p.add_argument("path"); p.set_defaults(run=cmd_refs)
    p = sub.add_parser("move"); p.add_argument("src"); p.add_argument("dst"); p.set_defaults(run=cmd_move)
    p = sub.add_parser("trash"); p.add_argument("path"); p.set_defaults(run=cmd_trash)
    p = sub.add_parser("attachments"); p.add_argument("note"); p.set_defaults(run=cmd_attachments)
    p = sub.add_parser("attach"); p.add_argument("file"); p.add_argument("dir"); p.set_defaults(run=cmd_attach)
    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
