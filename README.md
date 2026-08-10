# zzc-skills

AI agent skills — vendored from upstream repos plus self-authored — assembled into
packs and distributed across Claude Code, Kiro, Pi, and Hermes.

Extracted from [dotconfig](https://github.com/zhengfran/dotconfig)'s `tools/ai/skills/`
on 2026-08-10 ([migration plan](https://github.com/zhengfran/dotconfig/issues/1)),
history preserved via `git subtree split`. Canonical clone location: `~/projects/zzc-skills`
— other repos' setup instructions can reference this path directly, e.g.
`~/projects/zzc-skills/scripts/skills-install coding .`.

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

## Usage

Fresh clone / after a pull:

```bash
scripts/skills-sync                  # rebuild assembled/ from vendored/ + self/
scripts/skills-install global        # distribute the global pack into all 4 agent home dirs
```

Add `--update` to `skills-sync` to pull the latest vendored upstreams first
(`scripts/skills-sync --update`).

Per-project install (coding or notes pack, into a specific repo):

```bash
~/projects/zzc-skills/scripts/skills-install coding /path/to/repo
~/projects/zzc-skills/scripts/skills-install notes ~/org --copy   # detached copy, for cloud-synced dirs
```

`--agents claude,kiro,pi,hermes` narrows which agents get installed; defaults are
`claude,kiro` for project-level packs and `claude,kiro,pi,hermes` for `global`.

## Notes

- Known tech debt: `pi`/`hermes` project-level skill directory conventions
  (`.pi/skills`, `.hermes/skills`) are best-guess, unverified against those agents'
  actual behavior. Machine-level paths (`~/.pi/agent/skills`, `~/.hermes/skills`) are
  confirmed.
- No repo-wide `LICENSE` — matches dotconfig's own convention. Individual vendored
  skills may carry their own license file (e.g. `vendored/coding/mcp-builder/LICENSE.txt`);
  those are redistributed as vendored, unmodified.
- This repo does not publish itself as a Claude Code plugin marketplace
  (`.claude-plugin/marketplace.json`) — the wholesale-install model doesn't map onto
  per-skill/per-pack selection or the symlink-lockstep convention above. Revisit if
  this repo ever needs to be shared/discovered by others.
