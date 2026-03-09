#!/usr/bin/env python3
"""
Paw - iTerm2 Clipboard Image Paste Plugin
Detects image in clipboard on Cmd+V, saves to file, pastes the path.
Word segmentation features are handled by paw.zsh (zsh widget layer).
"""

import iterm2
import subprocess
import os
import json
import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = os.path.expanduser("~/.config/paw")
LOG_FILE = os.path.join(LOG_DIR, "paw.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE)],
)
logger = logging.getLogger("paw")

DEFAULT_CONFIG = {
    "paste_image": {
        "save_directory": "~/.config/paw/images",
        "filename_format": "%Y%m%d_%H%M%S",
        "output_format": "{path}",
    },
}


def load_config():
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    p = Path.home() / ".config" / "paw" / "config.json"
    if p.exists():
        try:
            with open(p) as f:
                user = json.load(f)
            for k, v in user.items():
                if k in config and isinstance(config[k], dict) and isinstance(v, dict):
                    config[k].update(v)
                else:
                    config[k] = v
        except Exception as e:
            logger.error(f"Config load error: {e}")
    return config


def has_clipboard_image():
    for fmt in ("PNGf", "TIFF"):
        try:
            r = subprocess.run(
                ["osascript", "-e",
                 f'try\nclipboard info for «class {fmt}»\nreturn "yes"\n'
                 f'on error\nreturn "no"\nend try'],
                capture_output=True, text=True, timeout=2,
            )
            if "yes" in r.stdout:
                return True
        except Exception:
            pass
    return False


def save_clipboard_image(config):
    cfg = config.get("paste_image", {})
    save_dir = os.path.expanduser(cfg.get("save_directory", "~/.config/paw/images"))
    os.makedirs(save_dir, exist_ok=True)

    filename = datetime.now().strftime(cfg.get("filename_format", "%Y%m%d_%H%M%S")) + ".png"
    filepath = os.path.join(save_dir, filename)

    try:
        r = subprocess.run(["pngpaste", filepath], capture_output=True, timeout=10)
        if r.returncode == 0 and os.path.exists(filepath):
            return filepath
    except FileNotFoundError:
        pass

    try:
        tiff_path = filepath.replace(".png", ".tiff")
        script = (
            f'set theFile to POSIX file "{tiff_path}"\n'
            f'try\n'
            f'set theData to the clipboard as «class TIFF»\n'
            f'set fileRef to open for access theFile with write permission\n'
            f'write theData to fileRef\n'
            f'close access fileRef\n'
            f'return "ok"\n'
            f'on error errMsg\nreturn "err: " & errMsg\nend try'
        )
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        if "ok" in r.stdout:
            subprocess.run(["sips", "-s", "format", "png", tiff_path, "--out", filepath],
                           capture_output=True, timeout=10)
            if os.path.exists(tiff_path):
                os.remove(tiff_path)
            if os.path.exists(filepath):
                return filepath
    except Exception as e:
        logger.error(f"Save error: {e}")
    return None


async def handle_paste(session, config):
    if has_clipboard_image():
        filepath = save_clipboard_image(config)
        if filepath:
            fmt = config.get("paste_image", {}).get("output_format", "{path}")
            output = fmt.format(
                path=filepath,
                filename=os.path.basename(filepath),
                dir=os.path.dirname(filepath),
            )
            logger.info(f"Pasted image: {output}")
            await session.async_send_text(output)
            return
    try:
        r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
        if r.stdout:
            await session.async_send_text(r.stdout)
    except Exception as e:
        logger.error(f"Text paste error: {e}")


async def main(connection):
    logger.info("Paw image paste plugin starting...")
    config = load_config()

    pattern = iterm2.KeystrokePattern()
    pattern.required_modifiers = [iterm2.Modifier.COMMAND]
    pattern.keycodes = [iterm2.Keycode.ANSI_V]

    try:
        async with iterm2.KeystrokeFilter(connection, [pattern]):
            async with iterm2.KeystrokeMonitor(connection) as monitor:
                logger.info("Ready. Listening for Cmd+V...")
                while True:
                    keystroke = await monitor.async_get()
                    if (keystroke.keycode == iterm2.Keycode.ANSI_V
                            and iterm2.Modifier.COMMAND in keystroke.modifiers):
                        app = await iterm2.async_get_app(connection)
                        window = app.current_terminal_window
                        if not window:
                            continue
                        session = window.current_tab.current_session
                        if session:
                            await handle_paste(session, config)
    except Exception as e:
        logger.error(f"Plugin error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    iterm2.run_forever(main)
