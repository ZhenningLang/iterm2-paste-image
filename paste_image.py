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
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_FILE = os.path.expanduser("~/.iterm2-paste-image/debug.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

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
                logger.info(f"Loaded config from {config_path}")
                break
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
    
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
        logger.debug(f"PNG check result: {result.stdout.strip()}")
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
        logger.debug(f"TIFF check result: {result.stdout.strip()}")
        return "yes" in result.stdout
    except Exception as e:
        logger.error(f"Error checking clipboard: {e}")
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
    except Exception as e:
        logger.error(f"Error getting text from clipboard: {e}")
        return ""


def save_clipboard_image(config):
    """Save clipboard image to file and return the path."""
    save_dir = config["save_directory"]
    os.makedirs(save_dir, exist_ok=True)
    
    filename = datetime.now().strftime(config["filename_format"]) + ".png"
    filepath = os.path.join(save_dir, filename)
    logger.info(f"Attempting to save image to: {filepath}")
    
    # Try pngpaste first (faster and more reliable)
    try:
        result = subprocess.run(
            ["pngpaste", filepath],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0 and os.path.exists(filepath):
            logger.info(f"Saved image using pngpaste: {filepath}")
            return filepath
        else:
            logger.warning(f"pngpaste failed: {result.stderr}")
    except FileNotFoundError:
        logger.info("pngpaste not installed, using fallback")
    except Exception as e:
        logger.error(f"pngpaste error: {e}")
    
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
        on error errMsg
            return "error: " & errMsg
        end try
        '''
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10
        )
        logger.debug(f"osascript result: {result.stdout.strip()}")
        
        if "success" in result.stdout:
            subprocess.run(
                ["sips", "-s", "format", "png", tiff_path, "--out", filepath],
                capture_output=True,
                timeout=10
            )
            if os.path.exists(tiff_path):
                os.remove(tiff_path)
            if os.path.exists(filepath):
                logger.info(f"Saved image using osascript fallback: {filepath}")
                return filepath
    except Exception as e:
        logger.error(f"Fallback save error: {e}")
    
    logger.error("Failed to save image")
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
    logger.info("=" * 50)
    logger.info("iTerm2 Paste Image Plugin starting...")
    logger.info(f"Log file: {LOG_FILE}")
    
    config = load_config()
    logger.info(f"Config: {config}")
    
    # Create pattern for Cmd+V
    pattern = iterm2.KeystrokePattern()
    pattern.required_modifiers = [iterm2.Modifier.COMMAND]
    pattern.keycodes = [iterm2.Keycode.ANSI_V]
    logger.info("Created keystroke pattern for Cmd+V")
    
    async def handle_keystroke(keystroke):
        """Handle the intercepted Cmd+V keystroke."""
        logger.info(f"Handling keystroke: keycode={keystroke.keycode}, modifiers={keystroke.modifiers}")
        
        app = await iterm2.async_get_app(connection)
        window = app.current_terminal_window
        if not window:
            logger.warning("No current terminal window")
            return
        
        session = window.current_tab.current_session
        if not session:
            logger.warning("No current session")
            return
        
        # Check if clipboard has image
        has_image = has_image_in_clipboard()
        logger.info(f"Clipboard has image: {has_image}")
        
        if has_image:
            filepath = save_clipboard_image(config)
            if filepath:
                output = format_output(config, filepath)
                logger.info(f"Sending path to terminal: {output}")
                await session.async_send_text(output)
                return
        
        # No image - paste text normally
        text = get_text_from_clipboard()
        logger.info(f"Pasting text (length={len(text)})")
        if text:
            await session.async_send_text(text)
    
    logger.info("Setting up KeystrokeFilter and KeystrokeMonitor...")
    
    try:
        # Use KeystrokeFilter to intercept Cmd+V and KeystrokeMonitor to handle it
        async with iterm2.KeystrokeFilter(connection, [pattern]) as _filter:
            logger.info("KeystrokeFilter active")
            async with iterm2.KeystrokeMonitor(connection) as monitor:
                logger.info("KeystrokeMonitor active - plugin ready!")
                logger.info("Waiting for keystrokes...")
                while True:
                    keystroke = await monitor.async_get()
                    logger.debug(f"Received keystroke: keycode={keystroke.keycode}, modifiers={keystroke.modifiers}")
                    # Check if this is Cmd+V
                    if (keystroke.keycode == iterm2.Keycode.ANSI_V and 
                        iterm2.Modifier.COMMAND in keystroke.modifiers):
                        logger.info("Detected Cmd+V!")
                        await handle_keystroke(keystroke)
    except Exception as e:
        logger.error(f"Plugin error: {e}", exc_info=True)
        raise


iterm2.run_forever(main)
