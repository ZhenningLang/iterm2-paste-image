#!/usr/bin/env python3
"""
iTerm2 Paste Image Plugin
Automatically detects image in clipboard when pressing Cmd+V,
saves it to a configured directory, and pastes the file path.
"""

import iterm2
import subprocess
import os
import json
from datetime import datetime
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "save_directory": "~/.iterm2-paste-image/images",
    "filename_format": "%Y%m%d_%H%M%S",  # strftime format
    "output_format": "{path}",  # Can include {path}, {filename}, {dir}
}


def load_config():
    """Load configuration from config file or use defaults."""
    config_paths = [
        Path.home() / ".config" / "iterm2-paste-image" / "config.json",
        Path.home() / ".iterm2-paste-image" / "config.json",
    ]
    
    config = DEFAULT_CONFIG.copy()
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                    config.update(user_config)
                break
            except (json.JSONDecodeError, IOError):
                pass
    
    # Expand ~ in save_directory
    config["save_directory"] = os.path.expanduser(config["save_directory"])
    return config


def has_image_in_clipboard():
    """Check if clipboard contains an image using macOS pasteboard."""
    try:
        result = subprocess.run(
            ["osascript", "-e", 
             'tell application "System Events" to return (clipboard info for «class PNGf») is not {}'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "true" in result.stdout.lower():
            return True
        
        # Also check for TIFF (common for screenshots)
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to return (clipboard info for «class TIFF») is not {}'],
            capture_output=True,
            text=True,
            timeout=2
        )
        return "true" in result.stdout.lower()
    except Exception:
        return False


def save_clipboard_image(config):
    """Save clipboard image to file and return the path."""
    save_dir = config["save_directory"]
    os.makedirs(save_dir, exist_ok=True)
    
    filename = datetime.now().strftime(config["filename_format"]) + ".png"
    filepath = os.path.join(save_dir, filename)
    
    # Use pngpaste if available, otherwise fall back to osascript
    try:
        result = subprocess.run(
            ["which", "pngpaste"],
            capture_output=True,
            timeout=2
        )
        has_pngpaste = result.returncode == 0
    except Exception:
        has_pngpaste = False
    
    if has_pngpaste:
        result = subprocess.run(
            ["pngpaste", filepath],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            return filepath
    
    # Fallback: use osascript + sips
    try:
        # Save TIFF from clipboard
        tiff_path = filepath.replace(".png", ".tiff")
        script = f'''
        set theFile to POSIX file "{tiff_path}"
        try
            set theData to the clipboard as «class TIFF»
            set fileRef to open for access theFile with write permission
            write theData to fileRef
            close access fileRef
            return "success"
        on error
            return "error"
        end try
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if "success" in result.stdout:
            # Convert TIFF to PNG using sips
            subprocess.run(
                ["sips", "-s", "format", "png", tiff_path, "--out", filepath],
                capture_output=True,
                timeout=10
            )
            os.remove(tiff_path)
            if os.path.exists(filepath):
                return filepath
    except Exception:
        pass
    
    return None


def format_output(config, filepath):
    """Format the output string based on configuration."""
    output_format = config.get("output_format", "{path}")
    return output_format.format(
        path=filepath,
        filename=os.path.basename(filepath),
        dir=os.path.dirname(filepath)
    )


async def main(connection):
    """Main entry point for iTerm2 Python API."""
    config = load_config()
    
    async def keystroke_handler(keystroke):
        """Handle keystroke events."""
        # Check for Cmd+V (paste)
        if keystroke.keycode == 9 and keystroke.modifiers == [iterm2.Modifier.COMMAND]:
            # Check if clipboard has image
            if has_image_in_clipboard():
                # Save image and get path
                filepath = save_clipboard_image(config)
                if filepath:
                    # Get the current session and send the path
                    app = await iterm2.async_get_app(connection)
                    session = app.current_terminal_window.current_tab.current_session
                    output = format_output(config, filepath)
                    await session.async_send_text(output)
                    return True  # Consume the keystroke
        return False  # Let iTerm2 handle it normally
    
    # Monitor keystrokes
    async with iterm2.KeystrokeMonitor(connection) as monitor:
        while True:
            keystroke = await monitor.async_get()
            await keystroke_handler(keystroke)


iterm2.run_forever(main)
