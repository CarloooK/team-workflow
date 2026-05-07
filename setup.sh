#!/usr/bin/env bash
# setup.sh — 将 team-workflow 仓库同步到本地 ~/.hermes/ 配置
# 用法: cd ~/team-workflow && bash setup.sh
set -euo pipefail

HERMES_SKILLS="$HOME/.hermes/skills/software-development"
PIPELINE_DIR="$HERMES_SKILLS/hermes-multi-agent-pipeline"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Sync team-workflow to Hermes ==="

# 1. Pipeline skill
echo "[1/4] Pipeline skill..."
mkdir -p "$PIPELINE_DIR"
cp "$SCRIPT_DIR/pipeline/SKILL.md" "$PIPELINE_DIR/SKILL.md"

# 2. Profiles (SOUL.md templates)
echo "[2/4] Profiles..."
PROFILES_DIR="$PIPELINE_DIR/templates"
mkdir -p "$PROFILES_DIR"
for f in "$SCRIPT_DIR"/profiles/*.md; do
    name="$(basename "$f")"
    cp "$f" "$PROFILES_DIR/$name"
    echo "  → $name"
done

# 3. References
echo "[3/4] References..."
REFS_DIR="$PIPELINE_DIR/references"
mkdir -p "$REFS_DIR"
for f in "$SCRIPT_DIR"/references/*.md; do
    name="$(basename "$f")"
    cp "$f" "$REFS_DIR/$name"
    echo "  → $name"
done

# 4. Also copy pipeline skill to user-level skills for quick loading
echo "[4/4] Done."

echo ""
echo "=== 同步完成 ==="
echo "Pipeline skill: $PIPELINE_DIR"
echo "Profiles:       $PROFILES_DIR"
echo "References:     $REFS_DIR"
echo ""
echo "运行验证: ls -la $PIPELINE_DIR/"
