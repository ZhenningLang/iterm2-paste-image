#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ITERM2_SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
PLUGIN_NAME="paste_image.py"
CONFIG_DIR="$HOME/.config/iterm2-paste-image"

echo "=== iTerm2 Paste Image Installer ==="
echo

# Check for iTerm2
if [ ! -d "/Applications/iTerm.app" ]; then
    echo "[Error] iTerm2 not found in /Applications"
    echo "Please install iTerm2 first: https://iterm2.com/downloads.html"
    exit 1
fi

# Check if Python API is enabled
PYTHON_API_ENABLED=$(defaults read com.googlecode.iterm2 EnableAPIServer 2>/dev/null || echo "0")
if [ "$PYTHON_API_ENABLED" != "1" ]; then
    echo "⚠️  [Warning] iTerm2 Python API is NOT enabled!"
    echo ""
    echo "To enable it:"
    echo "  1. Open iTerm2 → Settings (Cmd+,)"
    echo "  2. Go to: General → Magic"
    echo "  3. Check: 'Enable Python API'"
    echo "     - 'Require Automation permission': Keep checked (more secure)"
    echo "     - 'Allow all apps to connect': Leave unchecked (not needed)"
    echo "     - 'Custom Python API Scripts Folder': Leave unchecked (use default)"
    echo "  4. Restart iTerm2"
    echo ""
    read -p "Continue installation anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
    echo
fi

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

# Re-check Python API status
PYTHON_API_ENABLED=$(defaults read com.googlecode.iterm2 EnableAPIServer 2>/dev/null || echo "0")
if [ "$PYTHON_API_ENABLED" != "1" ]; then
    echo "⚠️  IMPORTANT: Enable Python API (REQUIRED)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. Open iTerm2 → Settings (Cmd+,)"
    echo "2. Go to: General → Magic"
    echo "3. Check: 'Enable Python API'"
    echo "   - 'Require Automation permission': Keep checked (more secure)"
    echo "   - 'Allow all apps to connect': Leave unchecked"
    echo "   - 'Custom Python API Scripts Folder': Leave unchecked"
    echo "4. Restart iTerm2"
    echo ""
    echo "Without Python API enabled, the plugin will NOT work!"
    echo ""
fi

echo "Start the plugin:"
echo "━━━━━━━━━━━━━━━━━"
echo "  iTerm2 menu → Scripts → paste_image.py"
echo ""
echo "Auto-start (optional):"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "  mkdir -p ~/Library/Application\\ Support/iTerm2/Scripts/AutoLaunch"
echo "  ln -sf ~/Library/Application\\ Support/iTerm2/Scripts/paste_image.py \\"
echo "         ~/Library/Application\\ Support/iTerm2/Scripts/AutoLaunch/"
echo
