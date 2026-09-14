# zzc-skills

AI agent skills — vendored from upstream repos plus self-authored — assembled into
packs and distributed across Claude Code, Kiro, Codex, Pi, and Hermes.

Canonical clone location: `~/projects/zzc-skills` — other repos' setup instructions
can reference this path directly, e.g. `~/projects/zzc-skills/scripts/skills-install coding .`.

## Layout

```
vendored/{global,notes,coding}/   # upstream skill copies, tracked, managed by vendored/.skill-lock.json
self/{global,notes,coding}/       # self-authored skills, tracked directly (no lockfile)
assembled/{global,notes,coding}/  # derived symlink layer, gitignored, rebuilt by skills-sync
manifest.tsv                       # pack \t skill \t source(vendored|self) — single source of truth
scripts/{skills-install,skills-sync,skills-update}
```

`manifest.tsv` drives assembly: `skills-sync` rebuilds `assembled/<pack>/` as symlinks
into either `vendored/<pack>/<skill>` or `self/<pack>/<skill>`, whichever the row says.

## Packs

- **global** — cross-scenario meta-skills (grilling, research, handoff, teach, defuddle, …).
  Installed into every agent's home-level skill dir.
- **notes** — installed into `~/org` (copy mode, detached, synced across machines via
  cloud drive — see `--copy` below).
- **coding** — installed per-project, on demand, via `skills-install coding <repo>`.
- **hermes-only** — extras that only make sense for the hermes agent (currently empty).

## Upstream sources

Every skill under `vendored/` is an unmodified copy from one of these repos, tracked in
`vendored/.skill-lock.json` and refreshed by `scripts/skills-update`.

| Upstream | Skills | Packs | Followed for new skills |
| --- | --- | --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 29 | coding, global | yes |
| [lijigang/ljg-skills](https://github.com/lijigang/ljg-skills) (`md` branch) | 25 | notes | yes |
| [axtonliu/axton-obsidian-visual-skills](https://github.com/axtonliu/axton-obsidian-visual-skills) | 3 | notes | no |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | 1 | global | no |
| [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) | 1 | global | yes |
| [tt-a1i/archify](https://github.com/tt-a1i/archify) | 1 | coding | yes |

"Followed" repos are scanned for *new* upstream skills on every `skills-update` run
(the `followNew` list in the lockfile); the others are cherry-picked only, so their
catalogs don't flood the prompt. Add a repo with `skills-update --add-repo <url>`.

### Branches

A repo is fetched at its default branch unless the lockfile entry carries a `ref`.
`lijigang/ljg-skills` publishes Org-mode output on its default `master` branch and
Markdown output on `md`; we track `md`, so every `ljg-*` entry pins `"ref": "md"`.

Switch a whole repo to another branch with the `url#branch` form — it re-clones at
that branch, re-fetches every skill of that repo, and repins their `ref`:

```bash
scripts/skills-update --add-repo https://github.com/lijigang/ljg-skills.git#md
```

## Usage

Fresh clone / after a pull:

```bash
scripts/skills-sync                  # rebuild assembled/ from vendored/ + self/
scripts/skills-install global        # distribute the global pack into the default agent home dirs
```

Add `--update` to `skills-sync` to pull the latest vendored upstreams first
(`scripts/skills-sync --update`).

Per-project install (coding or notes pack, into a specific repo):

```bash
~/projects/zzc-skills/scripts/skills-install coding /path/to/repo
~/projects/zzc-skills/scripts/skills-install notes ~/org --copy   # detached copy, for cloud-synced dirs
```

`--agents` narrows which agents get installed. Supported: `claude`, `kiro`, `codex`,
`pi`, `hermes`. Defaults are `claude,kiro,codex` for project-level packs and all five
for `global`:

```bash
scripts/skills-install coding /path/to/repo --agents claude,codex
```

Each agent has a project-level dir (`<project>/.codex/skills`) and a machine-level one
(`~/.codex/skills`); `skills-update` sweeps the machine-level dirs when pruning a skill
that disappeared upstream.
