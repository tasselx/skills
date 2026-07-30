Skills are organized into bucket folders under `skills/`.

- `engineering/` contains daily code-work skills.

Every promoted skill under `skills/<bucket>/` should have:

- A `SKILL.md` file.
- A top-level README entry.
- A bucket README entry.
- A `.claude-plugin/plugin.json` `skills` array entry.
- An OpenCode command at `opencode/command/<skill-name>.md` (frontmatter `description` + body with `$ARGUMENTS` that loads the skill).

When adding or renaming a skill, keep `opencode/command/<name>.md` in sync and run `scripts/install-opencode.sh` to refresh local OpenCode links.

When changing the plugin release version, keep `package.json` and `.claude-plugin/plugin.json` versions in sync.
