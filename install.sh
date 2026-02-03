#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ITERM2_SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
PLUGIN_NAME="paste_image.py"
CONFIG_DIR="$HOME/.config/iterm2-paste-image"

echo "=== iTerm2 Paste Image Installer ==="
echo

# Check for pngpaste (optional but faster)
if ! command -v pngpaste &> /dev/null; then
    echo "[Info] pngpaste not found (optional, will use macOS native tools)"
    echo "For faster image saving: brew install pngpaste"
    echo
fi

# Create iTerm2 Scripts directory if not exists
mkdir -p "$ITERM2_SCRIPTS_DIR"

# Copy the script
cp "$SCRIPT_DIR/$PLUGIN_NAME" "$ITERM2_SCRIPTS_DIR/"
echo "[OK] Installed $PLUGIN_NAME to iTerm2 Scripts"

# Create config directory and example config
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CONFIG_DIR/config.json"
    echo "[OK] Created config file at $CONFIG_DIR/config.json"
else
    echo "[Skip] Config file already exists"
fi

# Create default image save directory
mkdir -p "$HOME/.iterm2-paste-image/images"
echo "[OK] Created image directory at ~/.iterm2-paste-image/images"

echo
echo "=== Installation Complete ==="
echo
echo "Next steps:"
echo "1. Open iTerm2 Preferences → General → Magic"
echo "2. Enable 'Enable Python API'"
echo "3. Restart iTerm2"
echo "4. Go to Scripts menu → paste_image.py to start the plugin"
echo
echo "To auto-start the plugin:"
echo "  - Create folder: ~/Library/Application Support/iTerm2/Scripts/AutoLaunch"
echo "  - Move the script there, or create a symlink"
echo
