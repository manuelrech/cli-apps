#!/usr/bin/env bash
#
# Installs the `cursor-mover` command so it is available from anywhere.
#
# Uses uv to create a shared virtualenv at the repo root (provisioning a
# compatible Python if needed), installs the package, then symlinks the
# generated console script into ~/.local/bin.
#
set -euo pipefail

APP_NAME="cursor-mover"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is not installed. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi

# --- create the shared virtualenv with uv (provisions Python 3.11+) ----------
if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Creating virtualenv at $VENV_DIR"
  uv venv --python ">=3.11" "$VENV_DIR"
fi

# --- install the package into the venv (creates the console script) ----------
echo "Installing $APP_NAME..."
uv pip install --python "$VENV_DIR/bin/python" -e "$REPO_ROOT"

# --- symlink the command into a directory on PATH ----------------------------
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/$APP_NAME" "$BIN_DIR/$APP_NAME"
echo "Installed: $BIN_DIR/$APP_NAME -> $VENV_DIR/bin/$APP_NAME"

# --- PATH check --------------------------------------------------------------
case ":$PATH:" in
  *":$BIN_DIR:"*) echo "Done. Run: $APP_NAME" ;;
  *)
    echo
    echo "warning: $BIN_DIR is not on your PATH."
    echo "Add this to your shell profile (e.g. ~/.zshrc):"
    echo "    export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac
