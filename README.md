# Tassel Agent Skills

面向 Coding Agent 的可安装 skills 集合。这个仓库后续可能会继续增加更多 skills；当前已发布的第一个技能是 `git-auto-commit`。

This is an installable collection of agent-neutral skills for coding agents. More skills may be added over time; the first published skill is `git-auto-commit`.

`git-auto-commit` 会读取真实 Git diff，学习当前仓库最近的提交风格，生成简洁的中英双语 commit message，并在安全检查通过后创建本地提交。

`git-auto-commit` analyzes real Git changes, learns recent commit style, generates concise Chinese-English commit messages, and creates safe local commits.

本仓库正式技能放在 `skills/` 目录，Claude Code plugin 元数据放在 `.claude-plugin/`，并可被 Agent Skills installer 识别。

This repo follows the layout: promoted skills live under `skills/`, Claude Code plugin metadata lives under `.claude-plugin/`, and the repo can be consumed by Agent Skills installers.

## 兼容性说明

这个技能不是“保证适配市面上所有 Agent 的私有插件系统”，但它尽量使用通用 Agent Skills 形态，适合以下几类工具：

- 支持 `SKILL.md` / Agent Skills 标准的工具。
- 支持 `npx skills@latest add owner/repo` 安装的工具。
- 能读取本地 Markdown 指令并执行 shell/Git 命令的 coding agent。
- Claude Code，可通过 `~/.claude/skills` 显示在 Skills 面板，也可通过 `.claude-plugin/` 作为 plugin 安装。
- Codex，可通过 `~/.codex/skills` 安装。

不同 Agent 对 slash command、插件 marketplace、自动发现路径的支持不一样，所以 `/git-auto-commit` 这类命令需要由对应客户端或插件系统映射。技能本体的通用入口是 `SKILL.md`，不是某个特定客户端的私有命令格式。

This skill is not guaranteed to support every proprietary agent plugin system on the market. It is designed around portable Agent Skills conventions: a `SKILL.md` entrypoint, bundled resources, optional slash-command prompt text, and installable metadata for common harnesses.

## 快速安装

使用 Agent Skills installer：

```bash
npx skills@latest add tasselx/skills
```

安装时选择你需要的 skill，以及你想安装到的 agent。当前仓库只有一个 skill：`git-auto-commit`。

只安装当前的 `git-auto-commit`，并安装到所有支持的 agent：

```bash
npx skills@latest add tasselx/skills --skill git-auto-commit --agent '*'
```

注意：`skills@latest` 当前会把通用 skill 安装到 `~/.agents/skills` 等 Agent Skills 目录；Claude Code 的 Skills 面板提示它扫描的是 `.claude/skills/` 或 `~/.claude/skills/`。如果你要让 Claude Code 的 Skills 面板显示这个技能，请看下面的 Claude Code Skills 安装。

如果你 fork 了仓库，把 `tasselx/skills` 替换成你的 `owner/repo`。

## Claude Code Skills 面板安装

让 Claude Code 的 Skills 面板显示 `git-auto-commit`：

```bash
mkdir -p ~/.claude/skills
cp -R skills/engineering/git-auto-commit ~/.claude/skills/
```

然后重启 Claude Code，或重新打开 Skills 面板。

如果你在当前项目里只想项目级启用，也可以安装到项目目录：

```bash
mkdir -p .claude/skills
cp -R skills/engineering/git-auto-commit .claude/skills/
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
```

通用 agent skills 目录：

```bash
mkdir -p ~/.agents/skills
cp -R skills/engineering/git-auto-commit ~/.agents/skills/
```

Claude 风格技能目录：

```bash
mkdir -p ~/.claude/skills
cp -R skills/engineering/git-auto-commit ~/.claude/skills/
```

本机已经同步安装到：

```text
~/.codex/skills/git-auto-commit
~/.claude/skills/git-auto-commit
```

## 使用方式

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

## 技能列表

当前仓库只有一个 skill。后续新增 skill 时，会继续按分类放在 `skills/<category>/<skill-name>/` 下，并在这里列出。

### Engineering

User-invoked:

- [`git-auto-commit`](./skills/engineering/git-auto-commit/SKILL.md) — 分析当前 Git 改动并创建安全的中英双语本地提交。

## 项目结构

```text
.
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── skills/
│   └── engineering/
│       ├── README.md
│       └── git-auto-commit/
│           ├── SKILL.md
│           ├── agents/openai.yaml
│           ├── commands/git-auto-commit.md
│           ├── references/commit-style.md
│           └── scripts/git_commit_snapshot.py
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

这个技能只创建本地 commit。遇到疑似密钥文件、大 diff、意图不清晰、破坏性改动、公共 API 变更、迁移、或混杂的无关改动时，会先停下来请求确认。除非用户明确要求 push，否则永远不会自动 push。

默认不会添加 `Co-Authored-By: Claude <noreply@anthropic.com>` 或其他 AI attribution trailer，除非用户明确要求。

The skill creates local commits only. It stops for confirmation when it detects secret-like paths, huge diffs, unclear intent, destructive changes, public API breaks, migrations, or mixed unrelated changes. It never pushes unless the user explicitly asks for push.
