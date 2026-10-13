# zzc-skills

A curated, flat catalog of skills for the agent environments used here.
Requires Python 3.8+, Bash 3.2+, and Git.

## Layout and selection

Each skill lives directly at `<name>/SKILL.md`. Its supporting `scripts/`,
`references/`, assets, and other runtime files stay inside that skill.
There are no `self/`, `vendored/`, or generated `assembled/` trees.

`skills.json` is the explicit catalog. It records installation packs and update
policies independently of directory layout. A new upstream skill is never added
automatically. Only entries in this file are installed or checked for updates.

```bash
scripts/skills-catalog
scripts/skills-catalog --pack coding
```

| Pack | Skills | Update policy |
| --- | --- | --- |
| global | check-integration, distill-memory, read-working-memory, save-handoff, search-memory, status | Follow Nowledge's agent-neutral skills |
| global | i-have-adhd, grilling, handoff | Follow upstream |
| coding | archify, retro, writing-for-agents | Follow upstream |
| coding | wayfinder | Local customization |
| notes | Existing `ljg` and `ljg-*` skills | Local customization |

The catalog contains 34 skills: 12 following upstream and 22 locally customized.
The six Nowledge entries are explicitly selected; future additions to their
repository do not expand this set.

## Install

Preview a reconciliation before applying it:

```bash
scripts/skills-install global --dry-run
scripts/skills-install global
scripts/skills-install coding /path/to/project --dry-run
scripts/skills-install coding /path/to/project
scripts/skills-install notes ~/obsidian --copy
```

Packs are installation presets, not folders. `global` targets the agent home
folders. `coding` and `notes` target the supplied project directory (default:
current directory). Existing destinations and command syntax are preserved.

Install only named skills within a pack:

```bash
scripts/skills-install coding /path/to/project --skills wayfinder
scripts/skills-install coding /path/to/project --skills retro,writing-for-agents --agents agents
```

`--skills` is additive: it installs the named entries without removing other
previously installed skills. A later full-pack installation reconciles the entire
pack, including pruning names removed from the catalog.

Symlinks are the default. `--copy` creates detached copies. Project defaults are
`.claude/skills`, `.kiro/skills`, and `.agents/skills`. Global defaults are
`~/.claude/skills`, `~/.kiro/skills`, `~/.codex/skills`, `~/.hermes/skills`, and
`${DSH_HOME:-~/.dsh}/skills`. `--agents` narrows these destinations. The legacy
project `.codex/skills` target is available with `--agents codex`.

Each destination's `.zzc-skills-managed` records ownership by package and pack.
Reinstallation updates/prunes only that scope, preserving other scopes and
unrelated skills. All destinations are checked for collisions before any are
changed. Unmanaged same-name entries require explicit `--adopt-existing` after
inspection; links already pointing at the intended source are adopted safely.
`--dry-run` performs those checks and prints installs and removals without writing.

## Check and apply updates

```bash
scripts/skills-update                      # check selected upstream skills only
scripts/skills-update retro --diff         # review its changes
scripts/skills-update retro --apply        # apply this skill's clean update
scripts/skills-update --all --apply        # explicitly apply all tracked upstream skills
```

Checking fetches into the ignored `.cache/repos/` directory but does not change
skill files or `skills.json`. Repositories are fetched once per run and sparse
checkout selects only the requested skill paths. Failed fetches report errors
without deleting the existing cache.

Applying requires named skills or `--all`. Only `update: upstream` entries can
be selected; `update: custom` entries are rejected before fetching. There is no
force-overwrite option. Local edits are preserved and reported for manual review.
To accept upstream intentionally, inspect `--diff`, save your changes, and restore
the local tracked snapshot before applying; to retain ongoing customization,
change the entry to `update: custom`.

Each successful application records the content hash and fetched commit for that
skill. No repository-wide commit claims that unselected skills were refreshed.
File contents, executable bits, and symlink targets participate in change
checking. Replacements are staged and rolled back on swap failure. Nonzero exit
status signals a fetch, path, metadata, or local-edit conflict requiring attention.

The initial flat migration preserves the existing selected skill contents. Its
`hash` is a local safety baseline, not a claim that the snapshot equals upstream.
An absent `commit` means its exact upstream revision is unknown; the first
explicit update establishes that provenance. Archify follows the upstream
`archify/` skill directory, including its runtime resources.

## Maintain the catalog

To add a skill, create `<name>/SKILL.md` and add its entry to `skills.json`:

```json
"my-skill": { "pack": "coding", "update": "custom" }
```

An upstream entry also needs a known `repository`, its relative upstream `path`,
and a `hash` whenever a local copy already exists. Compute the baseline with:

```bash
PYTHONPATH=scripts python3 -c 'from pathlib import Path; from skills_common import folder_hash; print(folder_hash(Path("my-skill")))'
```

Custom entries may retain repository/path metadata as provenance; it never makes
them eligible for updates. To remove a skill, remove both its catalog entry and
folder, then preview/re-run the affected pack installation. Missing catalogued
skill files abort installation instead of silently pruning destinations.

## Migrating existing installations

Re-run the same pack install at each previously used destination. Existing
ownership records are retained, so old nested links are replaced with flat links
and deselected owned skills are removed. Detached project copies also need an
explicit reinstall. For installations lacking ownership records, inspect the
collisions and use `--adopt-existing` only for verified legacy installs.

## Validation

```bash
bash -n scripts/skills-install
python3 -m unittest discover -s tests -v
scripts/skills-catalog
```

Tests use temporary local Git repositories and installation directories; they
exercise selection, check-only behavior, conflicts, ownership, and rollback
without accessing the network or changing live agent installations.
