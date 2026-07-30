#!/usr/bin/env bash
# Install all skills from this repo into OpenCode:
#   - skills   -> ~/.config/opencode/skill/<name>  (+ ~/.agents/skills)
#   - commands -> ~/.config/opencode/command/<name>.md
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OPENCODE_CONFIG="${OPENCODE_CONFIG_DIR:-$HOME/.config/opencode}"
SKILL_DST="$OPENCODE_CONFIG/skill"
COMMAND_DST="$OPENCODE_CONFIG/command"
AGENTS_SKILL_DST="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
MODE="${1:-link}" # link | copy

usage() {
  cat <<'EOF'
Usage: scripts/install-opencode.sh [link|copy]

  link  Symlink skills and commands into OpenCode config (default).
  copy  Copy files instead of symlinking.

Installs:
  ~/.config/opencode/skill/<skill-name>/
  ~/.config/opencode/command/<skill-name>.md
  ~/.agents/skills/<skill-name>/

Prefer opencode/command/<name>.md; if missing, wraps skills/*/commands/<name>.md.

After install, quit and restart OpenCode.
Slash commands: /git-auto-commit, /deep-review, ...
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$MODE" != "link" && "$MODE" != "copy" ]]; then
  echo "error: mode must be link or copy" >&2
  usage >&2
  exit 1
fi

mkdir -p "$SKILL_DST" "$COMMAND_DST" "$AGENTS_SKILL_DST"

install_path() {
  local src="$1"
  local dst="$2"
  if [[ -e "$dst" || -L "$dst" ]]; then
    rm -rf "$dst"
  fi
  if [[ "$MODE" == "link" ]]; then
    ln -s "$src" "$dst"
  else
    if [[ -d "$src" ]]; then
      cp -R "$src" "$dst"
    else
      mkdir -p "$(dirname "$dst")"
      cp "$src" "$dst"
    fi
  fi
  echo "  $dst"
}

skill_description() {
  local skill_md="$1"
  local fallback="$2"
  python3 - "$skill_md" "$fallback" <<'PY'
import re, sys
path, fallback = sys.argv[1], sys.argv[2]
try:
    text = open(path, encoding="utf-8").read()
except OSError:
    print(fallback)
    raise SystemExit
m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
if not m:
    print(fallback)
    raise SystemExit
fm = m.group(1)
# description: |\n  multi\n or description: single line
mm = re.search(r"^description:\s*[|>][+-]?\s*\n((?:[ \t]+.*\n?)+)", fm, re.M)
if mm:
    lines = [re.sub(r"^[ \t]+", "", ln).rstrip() for ln in mm.group(1).splitlines()]
    text = " ".join(x for x in lines if x)
else:
    sm = re.search(r"^description:\s*(.+)$", fm, re.M)
    text = sm.group(1).strip().strip("'\"") if sm else fallback
text = re.sub(r"\s+", " ", text).strip()
print((text[:180] or fallback))
PY
}

echo "OpenCode install ($MODE) from $REPO_ROOT"
echo "Skills:"

shopt -s nullglob
skill_dirs=("$REPO_ROOT"/skills/*/*)
command_files=("$REPO_ROOT"/opencode/command/*.md)
shopt -u nullglob

count_skills=0
for skill_dir in "${skill_dirs[@]}"; do
  [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
  name="$(basename "$skill_dir")"
  install_path "$skill_dir" "$SKILL_DST/$name"
  install_path "$skill_dir" "$AGENTS_SKILL_DST/$name"
  count_skills=$((count_skills + 1))
done

echo "Commands:"
count_commands=0
declared=()

for cmd in "${command_files[@]:-}"; do
  [[ -f "${cmd:-}" ]] || continue
  name="$(basename "$cmd")"
  install_path "$cmd" "$COMMAND_DST/$name"
  declared+=("${name%.md}")
  count_commands=$((count_commands + 1))
done

for skill_dir in "${skill_dirs[@]}"; do
  [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
  name="$(basename "$skill_dir")"
  skip=
  for d in "${declared[@]:-}"; do
    if [[ "$d" == "$name" ]]; then
      skip=1
      break
    fi
  done
  [[ -n "$skip" ]] && continue

  src_cmd="$skill_dir/commands/$name.md"
  dest_cmd="$COMMAND_DST/$name.md"
  [[ -f "$src_cmd" ]] || continue

  desc="$(skill_description "$skill_dir/SKILL.md" "Run $name skill")"
  tmp="$(mktemp)"
  {
    echo "---"
    echo "description: $desc"
    echo "---"
    echo
    echo "Load and follow the \`$name\` skill (Skill tool / SKILL.md). Then run it for this request."
    echo
    echo "User arguments: \$ARGUMENTS"
    echo
    cat "$src_cmd"
  } >"$tmp"
  if [[ -e "$dest_cmd" || -L "$dest_cmd" ]]; then
    rm -rf "$dest_cmd"
  fi
  cp "$tmp" "$dest_cmd"
  rm -f "$tmp"
  echo "  $dest_cmd (generated from skills/.../commands/)"
  count_commands=$((count_commands + 1))
done

echo
echo "Installed $count_skills skill(s), $count_commands command(s)."
echo "Restart OpenCode, then try: /git-auto-commit or /deep-review"
