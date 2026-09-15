# zzc-skills

Curated AI-agent skills for Claude Code, Kiro, Codex, Pi, Hermes, and DeepSeek Harness.
The repository keeps authored skills and pinned upstream snapshots in one portable tree; there is no generated assembly layer.

## Layout

```text
self/{global,notes,coding}/<skill>/      # locally owned skills
vendored/{global,notes,coding}/<skill>/  # unmodified upstream snapshots
upstreams.json                           # provenance for vendored snapshots
scripts/skills-install                   # safe destination reconciliation
scripts/skills-update                    # explicit upstream refresh
```

The directory tree is the active catalog. Every immediate child containing `SKILL.md` is installed; removing or moving that directory disables it. `skills-install` rejects duplicate `<pack>/<skill>` names across `self/` and `vendored/`.

## Packs

- **global** — cross-scenario skills installed in agent home directories.
- **notes** — note and knowledge workflows, normally copied into `~/org`.
- **coding** — project-specific engineering skills installed on demand.

## Install

The scripts resolve the repository from their own location, so commands do not depend on a canonical clone path. When this repository's `scripts/` directory is on `PATH`:

```bash
skills-install global
skills-install coding /path/to/repo
skills-install notes ~/org --copy
```

For a one-time migration of an old copied install or broken assembly symlink that has no ownership file, add `--adopt-existing`. Ordinary runs reject unmanaged same-name entries. Live symlinks resolving to the same source are adopted automatically.

Project packs default to Claude Code, Kiro, and Codex. Global installs default to all supported agents. Narrow the targets when needed:

```bash
skills-install coding /path/to/repo --agents claude,kiro
```

Symlink mode is the default. `--copy` creates detached files for cloud-synced directories.

Each destination receives `.zzc-skills-managed`, an ownership record scoped by package and pack. Reinstallation updates and prunes only entries owned by that scope; unrelated skills, another pack, and agent-owned directories such as `.system` are preserved.

## Update vendored skills

```bash
skills-update                 # refresh every explicit upstream entry
skills-update tdd research    # refresh selected entries
```

The updater:

1. reads only explicitly declared entries from `upstreams.json`;
2. validates cached origins, fetches each repository once, and resets to the fetched commit;
3. compares content, executable modes, symlinks, and file types;
4. replaces snapshots atomically with rollback;
5. records per-skill commits and exits nonzero on malformed metadata, missing paths, fetch failures, or unresolved conflicts.

A locally edited vendored snapshot is preserved while upstream is unchanged. If both changed, resolve the conflict or intentionally overwrite it with `--force`. Locally maintained variants belong under `self/`, not `vendored/`.

`upstreams.json` groups shared repository data and records each skill's repository, pack, upstream path, baseline hash, and last refreshed commit. A repository-wide commit is updated only after a successful full-source refresh. The committed files under `vendored/` remain the reproducible runtime snapshot.

## Add or remove a skill

### Self-authored

Create or delete:

```text
self/<pack>/<name>/SKILL.md
```

### Vendored

1. Copy the upstream runtime directory to `vendored/<pack>/<name>/`.
2. Add its repository and skill mapping to `upstreams.json`.
3. Set `hash` to the stable content hash used by `scripts/skills-update`.
4. Run `skills-update <name>` and `skills-install <pack> ...`.

New upstream skills are never auto-discovered or assigned to a pack. Selection is an explicit repository decision.

## Ownership policy

- `self/` may be simplified, forked, and tailored to this environment.
- `vendored/` follows the exact upstream path recorded in `upstreams.json`.
- A removed upstream skill must be deleted or promoted to `self/`; there is no permanent orphan state.
- Full applications should ship a runtime artifact. Archify is therefore self-owned and excludes upstream tests and pre-rendered examples while retaining its complete runtime.
