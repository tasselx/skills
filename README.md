# Tassel Agent Skills

面向 Coding Agent 的可安装 skills 集合。这个仓库后续可能会继续增加更多 skills；当前已发布两个技能：`git-auto-commit` 和 `deep-review`。

This is an installable collection of agent-neutral skills for coding agents. More skills may be added over time; the currently published skills are `git-auto-commit` and `deep-review`.

`git-auto-commit` 会读取真实 Git diff，学习当前仓库最近的提交风格，生成中英文混排的 commit message（中文描述为主，技术术语用英文），并在安全检查通过后创建本地提交。内置密钥文件检测、合并冲突检测、生成物路径识别，以及 staged/unstaged 分阶段统计。

`git-auto-commit` analyzes real Git changes, learns recent commit style, generates mixed Chinese-English commit messages (Chinese description with English technical terms), and creates safe local commits. It includes built-in detection for secret-like files, merge conflicts, generated paths, and separate staged/unstaged line counts.

`deep-review` 对未提交的代码变更执行生产级只读审查。它通过 `git status`、`git diff`、`git diff --cached` 收集改动上下文，覆盖正确性、可靠性、安全、性能、架构、测试、回归、可观测性和部署安全等类别，返回按严重级别（Critical / High / Medium / Low）和置信度（Confirmed / Likely / Potential）分类的所有可执行发现，并给出风险评分和合并建议。

`deep-review` performs a production-level, read-only code review of uncommitted code changes. It gathers diff context via `git status`, `git diff`, and `git diff --cached`, then reviews across correctness, reliability, security, performance, architecture, testing, regression, observability, and deployment safety. It returns every actionable finding classified by severity (Critical / High / Medium / Low) and confidence (Confirmed / Likely / Potential), with a final risk score and merge recommendation.

本仓库正式技能放在 `skills/` 目录，Claude Code plugin 元数据放在 `.claude-plugin/`，并可被 Agent Skills installer 识别。

This repo follows the layout: promoted skills live under `skills/`, Claude Code plugin metadata lives under `.claude-plugin/`, and the repo can be consumed by Agent Skills installers.

## 兼容性说明

这个技能不是“保证适配市面上所有 Agent 的私有插件系统”，但它尽量使用通用 Agent Skills 形态，适合以下几类工具：

- 支持 `SKILL.md` / Agent Skills 标准的工具。
- 支持 `npx skills@latest add owner/repo` 安装的工具。
- 能读取本地 Markdown 指令并执行 shell/Git 命令的 coding agent。
- Claude Code，可通过 `~/.claude/skills` 显示在 Skills 面板，也可通过 `.claude-plugin/` 作为 plugin 安装。
- Codex，可通过 `~/.codex/skills` 安装。

不同 Agent 对 slash command、插件 marketplace、自动发现路径的支持不一样，所以 `/git-auto-commit`、`/deep-review` 这类命令需要由对应客户端或插件系统映射。技能本体的通用入口是 `SKILL.md`，不是某个特定客户端的私有命令格式。

This skill is not guaranteed to support every proprietary agent plugin system on the market. It is designed around portable Agent Skills conventions: a `SKILL.md` entrypoint, bundled resources, optional slash-command prompt text, and installable metadata for common harnesses.

## 快速安装

使用 Agent Skills installer：

```bash
npx skills@latest add tasselx/skills
```

安装时选择你需要的 skill，以及你想安装到的 agent。当前仓库有两个 skill：`git-auto-commit` 和 `deep-review`。

只安装 `git-auto-commit`，并安装到所有支持的 agent：

```bash
npx skills@latest add tasselx/skills --skill git-auto-commit --agent '*'
```

只安装 `deep-review`，并安装到所有支持的 agent：

```bash
npx skills@latest add tasselx/skills --skill deep-review --agent '*'
```

安装全部 skill：

```bash
npx skills@latest add tasselx/skills --agent '*'
```

注意：`skills@latest` 当前会把通用 skill 安装到 `~/.agents/skills` 等 Agent Skills 目录；Claude Code 的 Skills 面板提示它扫描的是 `.claude/skills/` 或 `~/.claude/skills/`。如果你要让 Claude Code 的 Skills 面板显示这个技能，请看下面的 Claude Code Skills 安装。

如果你 fork 了仓库，把 `tasselx/skills` 替换成你的 `owner/repo`。

## Claude Code Skills 面板安装

让 Claude Code 的 Skills 面板显示 `git-auto-commit` 和 `deep-review`：

```bash
mkdir -p ~/.claude/skills
cp -R skills/engineering/git-auto-commit ~/.claude/skills/
cp -R skills/engineering/deep-review ~/.claude/skills/
```

然后重启 Claude Code，或重新打开 Skills 面板。

如果你在当前项目里只想项目级启用，也可以安装到项目目录：

```bash
mkdir -p .claude/skills
cp -R skills/engineering/git-auto-commit .claude/skills/
cp -R skills/engineering/deep-review .claude/skills/
```

## Claude Code Plugin 安装

在 Claude Code 里：

```text
/plugin marketplace add tasselx/skills
/plugin install git-auto-commit-skills@tasselx
```

或者在 shell 里：

```bash
claude plugin marketplace add tasselx/skills
claude plugin install git-auto-commit-skills@tasselx
```

## 手动安装

Codex：

```bash
mkdir -p ~/.codex/skills
cp -R skills/engineering/git-auto-commit ~/.codex/skills/
cp -R skills/engineering/deep-review ~/.codex/skills/
```

通用 agent skills 目录：

```bash
mkdir -p ~/.agents/skills
cp -R skills/engineering/git-auto-commit ~/.agents/skills/
cp -R skills/engineering/deep-review ~/.agents/skills/
```

Claude 风格技能目录：

```bash
mkdir -p ~/.claude/skills
cp -R skills/engineering/git-auto-commit ~/.claude/skills/
cp -R skills/engineering/deep-review ~/.claude/skills/
```

本机已经同步安装到：

```text
~/.codex/skills/git-auto-commit
~/.claude/skills/git-auto-commit
~/.codex/skills/deep-review
~/.claude/skills/deep-review
```

## 使用方式

### git-auto-commit

Codex：

```text
$git-auto-commit
```

支持 slash command 的 agent：

```text
/git-auto-commit
```

通用 prompt：

```text
Use the git-auto-commit skill to analyze this repo and commit the current changes.
Use the git-auto-commit skill dry run, only generate the commit message.
Use the git-auto-commit skill to commit and then push.
```

中文 prompt：

```text
使用 git-auto-commit skill 分析当前仓库改动并提交。
使用 git-auto-commit skill 做 dry run，只生成 commit message，不提交。
使用 git-auto-commit skill 提交当前改动，然后 push。
```

### deep-review

Codex：

```text
$deep-review
```

支持 slash command 的 agent：

```text
/deep-review
```

通用 prompt：

```text
Use the deep-review skill to review the current uncommitted changes.
Use the deep-review skill to review only staged changes.
Use the deep-review skill to review commit abc123.
Use the deep-review skill to review this branch against main.
Use the deep-review skill to review specific files.
```

中文 prompt：

```text
使用 deep-review skill 审查当前未提交的改动。
使用 deep-review skill 只审查 staged 的改动。
使用 deep-review skill 审查 commit abc123。
使用 deep-review skill 审查当前分支相对 main 的差异。
使用 deep-review skill 审查指定文件。
```

## 技能列表

当前仓库有以下 skill。后续新增 skill 时，会继续按分类放在 `skills/<category>/<skill-name>/` 下，并在这里列出。

### Engineering

User-invoked:

- [`git-auto-commit`](./skills/engineering/git-auto-commit/SKILL.md) — 分析当前 Git 改动并创建安全的中英双语本地提交。
- [`deep-review`](./skills/engineering/deep-review/SKILL.md) — 对未提交的代码变更执行生产级只读审查，覆盖正确性、可靠性、安全、性能、架构、测试、回归、可观测性和部署安全，按严重级别和置信度分类，返回风险评分和合并建议。

## 项目结构

```text
.
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .gitignore
├── skills/
│   └── engineering/
│       ├── README.md
│       ├── git-auto-commit/
│       │   ├── SKILL.md
│       │   ├── agents/openai.yaml
│       │   ├── commands/git-auto-commit.md
│       │   ├── references/commit-style.md
│       │   └── scripts/
│       │       ├── git_commit_snapshot.py
│       │       └── test_git_commit_snapshot.py
│       └── deep-review/
│           ├── SKILL.md
│           ├── agents/openai.yaml
│           └── commands/deep-review.md
├── AGENTS.md
├── CLAUDE.md
├── package.json
└── README.md
```

后续新增 skill 时，推荐继续放在合适的分类目录中，例如：

```text
skills/
├── engineering/
│   └── another-engineering-skill/
└── productivity/
    └── another-productivity-skill/
```

## 安全行为

### git-auto-commit

这个技能只创建本地 commit。遇到疑似密钥文件、未解决的合并冲突、大 diff、意图不清晰、破坏性改动、公共 API 变更、迁移、或混杂的无关改动时，会先停下来请求确认。快照脚本会自动检测密钥类路径、冲突状态、生成物/缓存目录，并分别统计 staged 和 unstaged 改动行数。除非用户明确要求 push，否则永远不会自动 push。

默认不会添加 `Co-Authored-By: Claude <noreply@anthropic.com>` 或其他 AI attribution trailer，除非用户明确要求。

The skill creates local commits only. It stops for confirmation when it detects secret-like paths, unresolved merge conflicts, huge diffs, unclear intent, destructive changes, public API breaks, migrations, or mixed unrelated changes. The snapshot script automatically detects secret-like paths, conflict status, generated/cache directories, and reports separate staged/unstaged line counts. It never pushes unless the user explicitly asks for push.

### deep-review

这个技能是纯只读的：永远不会修改代码、staging、commit 或 push。它直接使用 `git status`、`git diff`、`git diff --cached` 等只读命令收集改动上下文，不写入或修改任何文件。审查结果按严重级别（Critical > High > Medium > Low）和置信度（Confirmed > Likely > Potential）分类，每条发现都包含文件路径、行号、证据描述和可执行的修复建议。不确定的发现会被降级或省略，以避免误报。最终输出包含风险评分和合并建议。

This skill is strictly read-only: it never modifies code, stages files, commits, or pushes. It gathers change context directly via read-only Git commands (`git status`, `git diff`, `git diff --cached`). Findings are classified by severity (Critical > High > Medium > Low) and confidence (Confirmed > Likely > Potential), each with a file path, line number, evidence, and actionable recommendation. Uncertain findings are downgraded or omitted to avoid false positives. The final output includes a risk score and merge recommendation.
