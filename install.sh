#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ITERM2_SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
PLUGIN_NAME="paw.py"
CONFIG_DIR="$HOME/.config/paw"

echo "=== Paw - Terminal Text Enhancement ==="
echo

# Check iTerm2
if [ ! -d "/Applications/iTerm.app" ]; then
    echo "[Error] iTerm2 not found. Install from: https://iterm2.com"
    exit 1
fi

# Check Python API
PYTHON_API_ENABLED=$(defaults read com.googlecode.iterm2 EnableAPIServer 2>/dev/null || echo "0")
if [ "$PYTHON_API_ENABLED" != "1" ]; then
    echo "[Warning] iTerm2 Python API is NOT enabled!"
    echo ""
    echo "  Settings (Cmd+,) → General → Magic → Enable Python API"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
    echo
fi

# Feature selection
echo "Select features to enable:"
echo ""

read -p "  [1] Clipboard image pasting (Cmd+V)? [Y/n] " -n 1 -r PASTE_IMG
echo
PASTE_IMG=${PASTE_IMG:-Y}

read -p "  [2] Chinese word jump (Option+Arrow)? [Y/n] " -n 1 -r WORD_JUMP
echo
WORD_JUMP=${WORD_JUMP:-Y}

read -p "  [3] Chinese word delete (Option+Delete)? [Y/n] " -n 1 -r WORD_DEL
echo
WORD_DEL=${WORD_DEL:-Y}

echo

# Find iTerm2 Python and install jieba if word features enabled
if [[ $WORD_JUMP =~ ^[Yy]$ ]] || [[ $WORD_DEL =~ ^[Yy]$ ]]; then
    echo "[*] Installing jieba (Chinese word segmentation)..."
    ITERM2_PYTHON=""
    for env_dir in "$HOME/Library/Application Support/iTerm2"/iterm2env*/versions/*/bin/python3; do
        if "$env_dir" -c "import iterm2" 2>/dev/null; then
            ITERM2_PYTHON="$env_dir"
            break
        fi
    done

    if [ -n "$ITERM2_PYTHON" ]; then
        "$ITERM2_PYTHON" -m pip install jieba -q 2>/dev/null && echo "[OK] jieba installed" || echo "[Warning] Failed to install jieba, will use fallback segmenter"
    else
        echo "[Warning] Could not find iTerm2 Python, jieba not installed"
    fi
fi

# Optional: pngpaste
if [[ $PASTE_IMG =~ ^[Yy]$ ]] && ! command -v pngpaste &>/dev/null; then
    echo "[Info] pngpaste not found (optional, for faster image saving)"
    echo "       Install with: brew install pngpaste"
    echo
fi

# Create config
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    # Generate config based on user selection
    FEAT_PASTE=$([[ $PASTE_IMG =~ ^[Yy]$ ]] && echo "true" || echo "false")
    FEAT_JUMP=$([[ $WORD_JUMP =~ ^[Yy]$ ]] && echo "true" || echo "false")
    FEAT_DEL=$([[ $WORD_DEL =~ ^[Yy]$ ]] && echo "true" || echo "false")

    cat > "$CONFIG_DIR/config.json" << EOF
{
    "features": {
        "paste_image": $FEAT_PASTE,
        "word_jump": $FEAT_JUMP,
        "word_delete": $FEAT_DEL
    },
    "paste_image": {
        "save_directory": "~/.config/paw/images",
        "filename_format": "%Y%m%d_%H%M%S",
        "output_format": "{path}"
    }
}
EOF
    echo "[OK] Config: $CONFIG_DIR/config.json"
else
    echo "[Skip] Config already exists at $CONFIG_DIR/config.json"
fi

# Install script
mkdir -p "$ITERM2_SCRIPTS_DIR"
cp "$SCRIPT_DIR/$PLUGIN_NAME" "$ITERM2_SCRIPTS_DIR/"
echo "[OK] Installed $PLUGIN_NAME"

# Remove old paste_image.py if exists
if [ -f "$ITERM2_SCRIPTS_DIR/paste_image.py" ]; then
    rm -f "$ITERM2_SCRIPTS_DIR/paste_image.py"
    rm -f "$ITERM2_SCRIPTS_DIR/AutoLaunch/paste_image.py"
    echo "[OK] Removed old paste_image.py"
fi

# AutoLaunch
AUTOLAUNCH_DIR="$ITERM2_SCRIPTS_DIR/AutoLaunch"
mkdir -p "$AUTOLAUNCH_DIR"
ln -sf "$ITERM2_SCRIPTS_DIR/$PLUGIN_NAME" "$AUTOLAUNCH_DIR/$PLUGIN_NAME"
echo "[OK] AutoLaunch configured"

# Create image directory
mkdir -p "$HOME/.config/paw/images"

echo
echo "=== Installation Complete ==="
echo
echo "Restart iTerm2 to activate Paw."
echo "Manual start: iTerm2 → Scripts → paw.py"
echo "Logs: $CONFIG_DIR/paw.log"
echo
