"""Shared catalog validation and snapshot operations for the skills tools."""
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "skills.json"
CACHE = ROOT / ".cache" / "repos"
REPO_PATHS = {}
PACKS = ("global", "coding", "notes")
ID_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")

def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def folder_hash(d):
    """Stable hash of a folder's tracked content, ignoring .git.

    A regular file contributes its relative path, content, and an
    executable-bit marker (only present when the bit is set, so the
    common non-executable case hashes identically to a scheme that never
    tracked mode at all). A symlink contributes its relative path and
    raw target (via os.readlink, never followed) instead of content, so
    two skills that differ only in "real file" vs "symlink to identical
    content" no longer hash the same. Any other file type (fifo, socket,
    device, ...) is a hard error rather than being silently skipped or
    mis-hashed as something else.
    """
    h = hashlib.sha1()
    for p in sorted(x for x in d.rglob("*") if ".git" not in x.parts):
        if p.is_symlink():
            rel = str(p.relative_to(d))
            h.update(rel.encode()); h.update(b"\0")
            h.update(b"symlink\0")
            h.update(os.readlink(p).encode()); h.update(b"\0")
        elif p.is_dir():
            continue   # directory presence is implied by the files under it
        elif p.is_file():
            rel = str(p.relative_to(d))
            h.update(rel.encode()); h.update(b"\0")
            if os.access(p, os.X_OK):
                h.update(b"executable\0")
            h.update(p.read_bytes()); h.update(b"\0")
        else:
            raise ValueError(f"unsupported file type in {d}: {p}")
    return h.hexdigest()


def clone_or_fetch(repo_id, url, ref):
    """Fetch only the selected skill paths; never discard a cache on failure."""
    dest = CACHE / repo_id
    paths = REPO_PATHS.get(repo_id, [])
    if dest.exists():
        origin = sh(["git", "-C", str(dest), "remote", "get-url", "origin"])
        if origin.returncode or origin.stdout.strip() != url:
            return None, f"cache origin mismatch: {dest}; inspect or move it before retrying"
        result = sh(["git", "-C", str(dest), "fetch", "--depth", "1", "origin", ref or "HEAD"])
        if result.returncode:
            return None, result.stderr.strip()
        result = sh(["git", "-C", str(dest), "reset", "--hard", "FETCH_HEAD"])
    else:
        CACHE.mkdir(parents=True, exist_ok=True)
        args = ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse"]
        if ref:
            args += ["--branch", ref]
        result = sh(args + [url, str(dest)])
    if result.returncode:
        return None, result.stderr.strip()
    if paths:
        result = sh(["git", "-C", str(dest), "sparse-checkout", "set", "--", *paths])
        if result.returncode:
            return None, result.stderr.strip()
    return dest, None


def head_commit(repo_dir):
    out = sh(["git", "-C", str(repo_dir), "rev-parse", "HEAD"])
    return out.stdout.strip() if out.returncode == 0 else None


def atomic_replace_dir(dest, src):
    """Replace ``dest`` (a directory, may not yet exist) with a copy of
    ``src``, staging the copy at a sibling temp path first so ``dest`` is
    never left half-written. Symlinks under ``src`` are recreated as
    symlinks (not dereferenced), and file modes — including the
    executable bit — are preserved.

    If swapping the staged copy into place fails after the previous
    content was already moved aside, that previous content is rolled
    back into ``dest`` so it's never lost. If the rollback rename itself
    fails, the backup is left on disk (never deleted) rather than
    silently discarded, and the original exception propagates either
    way."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp_new = dest.parent / f".{dest.name}.new.{os.getpid()}"
    tmp_old = dest.parent / f".{dest.name}.old.{os.getpid()}"
    shutil.rmtree(tmp_new, ignore_errors=True)
    shutil.rmtree(tmp_old, ignore_errors=True)
    shutil.copytree(src, tmp_new, symlinks=True, ignore=shutil.ignore_patterns(".git"))

    had_old = dest.exists() or dest.is_symlink()
    if had_old:
        os.replace(dest, tmp_old)
    try:
        os.replace(tmp_new, dest)
    except Exception:
        if had_old:
            try:
                os.replace(tmp_old, dest)   # rollback: restore the previous content
            except Exception:
                # rollback itself failed: leave tmp_old as a recoverable backup
                raise
            else:
                shutil.rmtree(tmp_new, ignore_errors=True)
        raise
    else:
        if had_old:
            shutil.rmtree(tmp_old, ignore_errors=True)


def write_json_atomic(path, data):
    tmp = path.parent / f".{path.name}.tmp.{os.getpid()}"
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(tmp, path)



def load_catalog(path=CATALOG):
    data = json.loads(path.read_text())
    def fail(message):
        raise ValueError(f"invalid {path.name}: {message}")
    if not isinstance(data, dict) or data.get("version") != 2:
        fail("expected version 2")
    repositories, skills = data.get("repositories"), data.get("skills")
    if not isinstance(repositories, dict) or not isinstance(skills, dict):
        fail("repositories and skills must be objects")
    for name, repo in repositories.items():
        if not ID_RE.fullmatch(name) or not isinstance(repo, dict):
            fail(f"invalid repository: {name}")
        if not isinstance(repo.get("url"), str) or not repo["url"] or repo["url"].startswith("-"):
            fail(f"invalid URL for {name}")
        ref = repo.get("ref")
        if ref is not None and (not isinstance(ref, str) or not ref or ref.startswith("-")):
            fail(f"invalid ref for {name}")
    for name, entry in skills.items():
        if not ID_RE.fullmatch(name) or name in ("scripts", "tests", "assembled", "self", "vendored"):
            fail(f"unsafe skill name: {name}")
        if not isinstance(entry, dict) or entry.get("pack") not in PACKS:
            fail(f"invalid pack for {name}")
        if entry.get("update") not in ("upstream", "custom"):
            fail(f"invalid update policy for {name}")
        if entry["update"] == "upstream" or "repository" in entry or "path" in entry:
            if entry.get("repository") not in repositories:
                fail(f"unknown repository for {name}")
            source = entry.get("path")
            if (not isinstance(source, str) or not source or source.startswith(("/", "~", "-"))
                    or "\\" in source or any(p in ("", ".", "..") for p in source.split("/"))):
                fail(f"unsafe upstream path for {name}")
        h = entry.get("hash")
        if h is not None and (not isinstance(h, str) or not SHA1_RE.fullmatch(h)):
            fail(f"invalid hash for {name}")
        local = path.parent / name
        if local.is_symlink():
            fail(f"skill directory must not be a symlink: {name}")
        if entry["update"] == "upstream" and local.exists() and h is None:
            fail(f"missing baseline hash for {name}")
        if entry.get("commit") is not None and (not isinstance(entry["commit"], str)
                or not SHA1_RE.fullmatch(entry["commit"])):
            fail(f"invalid commit for {name}")
    return data
