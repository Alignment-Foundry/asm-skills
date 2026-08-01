#!/usr/bin/env bash
# sync-skill.sh — Symlink or copy a skill from this repo to Hermes local skills dir.
# Usage: bash scripts/sync-skill.sh <category>/<skill-name> [--copy]
#
# --copy flag copies the skill instead of symlinking (for systems that don't
# support symlinks, or when you want to edit independently).

set -euo pipefail

SKILL_PATH="${1:-}"
COPY_MODE="${2:-}"

if [ -z "$SKILL_PATH" ]; then
    echo "Usage: $0 <category>/<skill-name> [--copy]"
    echo ""
    echo "Examples:"
    echo "  $0 productivity/code-review"
    echo "  $0 software-development/git-workflow --copy"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HERMES_SKILLS_DIR="${HERMES_SKILLS_DIR:-$HOME/{profile}/skills}"

CATEGORY="$(dirname "$SKILL_PATH")"
NAME="$(basename "$SKILL_PATH")"
SOURCE="$REPO_ROOT/skills/$SKILL_PATH"
TARGET="$HERMES_SKILLS_DIR/$CATEGORY/$NAME"

if [ ! -d "$SOURCE" ]; then
    echo "❌ Source not found: $SOURCE"
    echo "   Available categories:"
    ls "$REPO_ROOT/skills/"
    exit 1
fi

if [ ! -d "$HERMES_SKILLS_DIR" ]; then
    echo "📁 Creating Hermes skills directory: $HERMES_SKILLS_DIR"
    mkdir -p "$HERMES_SKILLS_DIR"
fi

# Remove existing target if it exists
if [ -e "$TARGET" ]; then
    echo "🗑️  Removing existing target: $TARGET"
    rm -rf "$TARGET"
fi

mkdir -p "$(dirname "$TARGET")"

if [ "$COPY_MODE" = "--copy" ]; then
    cp -r "$SOURCE" "$TARGET"
    echo "✅ Copied $SKILL_PATH → $TARGET"
else
    ln -sf "$SOURCE" "$TARGET"
    echo "✅ Linked $SKILL_PATH → $TARGET"
fi

# Show installed skill files
echo ""
echo "   Installed files:"
find "$TARGET" -type f | while read -r f; do
    echo "     • $f"
done
