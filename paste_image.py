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

DEFAULT_CONFIG = {
    "save_directory": "~/.iterm2-paste-image/images",
    "filename_format": "%Y%m%d_%H%M%S",
    "output_format": "{path}",
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
    
    config["save_directory"] = os.path.expanduser(config["save_directory"])
    return config


def has_image_in_clipboard():
    """Check if clipboard contains an image."""
    try:
        # Check for PNG
        result = subprocess.run(
            ["osascript", "-e", 
             'try\nclipboard info for «class PNGf»\nreturn "yes"\non error\nreturn "no"\nend try'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if "yes" in result.stdout:
            return True
        
        # Check for TIFF (screenshots)
        result = subprocess.run(
            ["osascript", "-e",
             'try\nclipboard info for «class TIFF»\nreturn "yes"\non error\nreturn "no"\nend try'],
            capture_output=True,
            text=True,
            timeout=2
        )
        return "yes" in result.stdout
    except Exception:
        return False


def get_text_from_clipboard():
    """Get text content from clipboard."""
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout
    except Exception:
        return ""


def save_clipboard_image(config):
    """Save clipboard image to file and return the path."""
    save_dir = config["save_directory"]
    os.makedirs(save_dir, exist_ok=True)
    
    filename = datetime.now().strftime(config["filename_format"]) + ".png"
    filepath = os.path.join(save_dir, filename)
    
    # Try pngpaste first (faster and more reliable)
    try:
        result = subprocess.run(
            ["pngpaste", filepath],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0 and os.path.exists(filepath):
            return filepath
    except FileNotFoundError:
        pass  # pngpaste not installed
    except Exception:
        pass
    
    # Fallback: use osascript
    try:
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
            subprocess.run(
                ["sips", "-s", "format", "png", tiff_path, "--out", filepath],
                capture_output=True,
                timeout=10
            )
            if os.path.exists(tiff_path):
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
    
    # Create pattern for Cmd+V
    pattern = iterm2.KeystrokePattern()
    pattern.required_modifiers = [iterm2.Modifier.COMMAND]
    pattern.keycodes = [iterm2.Keycode.ANSI_V]
    
    async def handle_keystroke(keystroke):
        """Handle the intercepted Cmd+V keystroke."""
        app = await iterm2.async_get_app(connection)
        window = app.current_terminal_window
        if not window:
            return
        
        session = window.current_tab.current_session
        if not session:
            return
        
        # Check if clipboard has image
        if has_image_in_clipboard():
            filepath = save_clipboard_image(config)
            if filepath:
                output = format_output(config, filepath)
                await session.async_send_text(output)
                return
        
        # No image - paste text normally
        text = get_text_from_clipboard()
        if text:
            await session.async_send_text(text)
    
    # Use KeystrokeFilter to intercept Cmd+V and KeystrokeMonitor to handle it
    async with iterm2.KeystrokeFilter(connection, [pattern]) as _filter:
        async with iterm2.KeystrokeMonitor(connection) as monitor:
            while True:
                keystroke = await monitor.async_get()
                # Check if this is Cmd+V
                if (keystroke.keycode == iterm2.Keycode.ANSI_V and 
                    iterm2.Modifier.COMMAND in keystroke.modifiers):
                    await handle_keystroke(keystroke)


iterm2.run_forever(main)
