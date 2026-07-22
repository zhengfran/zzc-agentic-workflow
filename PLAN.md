# Skills 治理与重建方案

状态：进行中（地基已建，重建中）。起草 2026-07-22。

## 背景 / 病根诊断

Skill 来自 6+ 上游 repo，靠 Vercel Labs `skills` CLI 的 `.skill-lock.json` 半自动 vendor，但从未分层。三个叠加问题：

1. **4 份 copy 各自漂移**，无单一真相源：
   - claude `~/.claude/skills` → symlink 到 dotconfig（55）
   - kiro `~/.kiro/skills` 独立实体目录（48）
   - pi `~/.pi/agent/skills` 独立目录
   - hermes `~/.hermes/skills` 仅 ljg 子集 + 一个别处没有的 `ljg-push`
2. **多上游拍平混装**进一个 global 目录，从不分作用域。
3. **lockfile 漂移**：记 76 条，实际目录仅 55 —— 24 条是已删的幽灵（含 `ljg-push`）。
4. 自建 skill 混在 vendored 里，分不清。实际自建仅 3 个。

## 已定决策（grill 结论）

1. **更新机制**：保留 skills CLI + lockfile（copy 落地），写统一 `skills-sync` 脚本。不改用 plugin/marketplace（只有 Claude 认，pi/hermes/kiro 吃不到）。
2. **作用域**：薄 global + 双 pack。global 只留跨场景元技能；笔记 pack → `~/org`；coding pack → 按需装进代码库。
3. **agent 分发**：统一全量、只按作用域分，4 agent 的目录 symlink 到同一组装目录 → 根除 drift。**例外**：允许「agent 专属」附加（`garmin-runcoach` 只挂 hermes）。
4. **自建 repo**：`~/projects/zzc-skills`，生态兼容结构（`skills/<name>/SKILL.md` + `.claude-plugin/`），已 `git init`。
5. `garmin-runcoach` → hermes 专属；`ljg-push` → 废弃；`diagnosing-bugs` → 与 `diagnose` 去重，留 `diagnose`。

## 目标拓扑

```
三个源(git 各自独立)                作用域                      四个 agent
A. dotconfig/tools/ai/skills/vendored/  ┐   global(薄~10)   claude → ~/.claude/skills
   (skills-sync 拉上游, lockfile 管)     ├─组装→ notes  →~/org   kiro   → ~/.kiro/skills
B. ~/projects/zzc-skills/ (独立 repo)   ┘   coding →按需装      pi     → ~/.pi/agent/skills
C. 上游本体在 GitHub                                            hermes → ~/.hermes/skills(+garmin 专属)
```

原则：每个作用域只维护一份 `assembled/` 组装目录，4 agent 目录 symlink 过去。

## 目录结构

```
~/dotconfig/tools/ai/skills/
├── vendored/{global,notes,coding}/   # 源 A：只读上游，勿手改
│   └── .skill-lock.json              # 沿用并清理漂移
├── assembled/{global,notes,coding}/  # 组装层(symlink，不落实体)
├── scripts/{skills-sync,skills-install}
└── PLAN.md (本文件)

~/projects/zzc-skills/                 # 源 B(已 init)
├── .claude-plugin/marketplace.json
└── skills/{new-org-project,sync-jira-to-denote,garmin-runcoach}/
```

## Skill 分类清单

**Global（元技能，全 4 agent）**：caveman, handoff, zoom-out, teach, research, defuddle,
grilling(+grill-me/grill-with-docs), write-a-skill, writing-great-skills, ljg-skill-map

**笔记 pack → ~/org**：全部 ljg-*（book/card/invest/learn/paper/paper-flow/paper-river/
plain/present/qa/rank/read/relationship/roundtable/think/travel/word/word-flow/writes）
+ new-org-project*, sync-jira-to-denote*（*=自建，来自 zzc-skills）
+ 可视化组：excalidraw-diagram, mermaid-visualizer, obsidian-canvas-creator（coding 按需也可装）

**coding pack → 按需装进代码库**：code-review, codebase-design, diagnose, domain-modeling,
implement, improve-codebase-architecture, prototype, tdd, mcp-builder, to-issues, to-prd,
to-spec, to-tickets, triage, wayfinder, ask-matt, setup-matt-pocock-skills

**agent 专属**：garmin-runcoach → 仅 hermes（来自 zzc-skills）

**废弃**：ljg-push, diagnosing-bugs

## 分发机制

| 作用域 | 组装目录 | 分发方式 |
|---|---|---|
| global | assembled/global | 4 agent 的 global skill 目录 symlink 过去 |
| 笔记 | assembled/notes  | copy 进 ~/org 下各 agent 项目目录(随 drive 云盘同步多机) |
| coding | assembled/coding | `skills-install coding` 在当前 repo 建 .claude/skills 等 |
| hermes 专属 | zzc-skills/garmin-runcoach | 只 symlink 进 ~/.hermes/skills |

## skills-sync 职责

1. 读 lockfile，逐个拉上游最新，比对 skillFolderHash；有更新则刷新，**hack 过则报冲突不静默覆盖**。
2. 清理 lockfile 漂移(幽灵条目)。
3. 按分类清单重建 assembled/{global,notes,coding} 的 symlink（源含 vendored/ + zzc-skills/）。
4. 幂等。ljg 用 master(org-mode) 分支。

## 执行阶段 / checklist

- [x] 备份 4 份现状（scratchpad skills-backup-*）
- [x] init ~/projects/zzc-skills + 迁 3 个自建 skill
- [x] 建 dotconfig/tools/ai/skills 骨架
- [x] 按来源把 vendored 分进 vendored/{global,notes,coding}，去重、去幽灵
- [x] 写 skills-sync + skills-install
- [x] 改 setup-config.sh：先跑 skills-sync，再把 assembled/global 逐 skill 分发进 4 agent
- [x] 收敛 drift：删 kiro/pi/hermes 独立实体目录，统一 symlink；hermes 加挂 garmin
- [x] 装笔记 pack 到 ~/org（claude + hermes，copy 模式）
- [x] 提交（conventional commits，不加 AI 署名）
- [ ] 后续：在某个代码库试跑 `skills-install coding`（挑一个 repo 时做）

## 待验证（执行期）

- pi/hermes 的**项目级** skill 目录约定（global 级已知：~/.pi/agent/skills、~/.hermes/skills）。
- ~/org 是 symlink→~/drive/org 且非 git；笔记 pack 用 copy 落地，随云盘同步到多机（可接受）。
- zzc-skills 的 marketplace.json 精确 schema（先占位，后按 skills CLI 实测校正）。
