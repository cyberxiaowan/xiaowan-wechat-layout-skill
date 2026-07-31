#!/bin/zsh
set -euo pipefail

PACKAGE_DIR="${0:A:h}"
SKILL_NAME="xiaowan-wechat-layout-lite"
CODEX_ROOT="${CODEX_HOME:-$HOME/.codex}"
SKILLS_TARGET="$CODEX_ROOT/skills"
TARGET_DIR="$SKILLS_TARGET/$SKILL_NAME"

mkdir -p "$TARGET_DIR"
rsync -a --delete \
  --exclude ".git" \
  --exclude ".DS_Store" \
  --exclude "README.md" \
  --exclude "NOTICE.md" \
  --exclude "LICENSE" \
  --exclude "install.command" \
  "$PACKAGE_DIR/" "$TARGET_DIR/"

echo "✓ 已安装：$SKILL_NAME"

if [[ ! -f "$SKILLS_TARGET/gzh-design/SKILL.md" ]]; then
  echo ""
  echo "正在从官方仓库安装底层依赖 gzh-design…"
  DEPENDENCY_TMP="$(mktemp -d)"
  trap 'rm -rf "$DEPENDENCY_TMP"' EXIT
  git clone --depth 1 https://github.com/isjiamu/gzh-design-skill.git "$DEPENDENCY_TMP/gzh-design"
  mkdir -p "$SKILLS_TARGET/gzh-design"
  rsync -a --delete \
    --exclude ".git" \
    --exclude ".DS_Store" \
    "$DEPENDENCY_TMP/gzh-design/" "$SKILLS_TARGET/gzh-design/"
  echo "✓ 已安装：gzh-design（甲木 × 摸鱼小李，AGPL-3.0）"
else
  echo "✓ 已检测到依赖：gzh-design"
fi

echo ""
echo "安装完成。请重新打开一个 Codex 任务。"
echo '调用方式：用 $xiaowan-wechat-layout-lite 排版这篇公众号文章。'
echo ""
if [[ -t 0 ]]; then
  read -k 1 "?按任意键关闭…"
fi
