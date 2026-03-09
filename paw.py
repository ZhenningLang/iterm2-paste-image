#!/usr/bin/env python3
"""
Paw - Terminal Text Enhancement for iTerm2
Features:
- Clipboard image pasting (Cmd+V with image detection)
- Chinese word segmentation jumping (Option+Arrow)
- Chinese word segmentation deletion (Option+Delete)
"""

import iterm2
import subprocess
import os
import json
import logging
import unicodedata
from datetime import datetime
from pathlib import Path

LOG_DIR = os.path.expanduser("~/.config/paw")
LOG_FILE = os.path.join(LOG_DIR, "paw.log")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE)],
)
logger = logging.getLogger("paw")

DEFAULT_CONFIG = {
    "features": {
        "paste_image": True,
        "word_jump": True,
        "word_delete": True,
    },
    "paste_image": {
        "save_directory": "~/.config/paw/images",
        "filename_format": "%Y%m%d_%H%M%S",
        "output_format": "{path}",
    },
}


def load_config():
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    for p in [Path.home() / ".config" / "paw" / "config.json"]:
        if p.exists():
            try:
                with open(p) as f:
                    user = json.load(f)
                deep_merge(config, user)
                logger.info(f"Loaded config from {p}")
            except Exception as e:
                logger.error(f"Config load error: {e}")
            break
    return config


def deep_merge(base, override):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            deep_merge(base[k], v)
        else:
            base[k] = v


# ── Text utilities ──────────────────────────────────────────────────

def is_wide_char(ch):
    return unicodedata.east_asian_width(ch) in ("F", "W")


def column_to_char_index(text, column):
    col = 0
    for i, ch in enumerate(text):
        w = 2 if is_wide_char(ch) else 1
        if col + w > column:
            return i
        col += w
    return len(text)


_jieba_available = False

def init_segmenter():
    global _jieba_available
    try:
        import jieba
        jieba.initialize()
        _jieba_available = True
        logger.info("jieba initialized")
    except ImportError:
        logger.warning("jieba not installed, using fallback segmenter")


def _char_class(ch):
    if ch.isspace():
        return "space"
    cp = ord(ch)
    if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
            or 0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF):
        return "cjk"
    cat = unicodedata.category(ch)
    if cat[0] in ("P", "S"):
        return "punct"
    if ch.isalnum():
        return "alnum"
    return "other"


def get_word_boundaries(text):
    """Return list of (start, end) character index pairs for each word."""
    if not text:
        return []

    if _jieba_available:
        import jieba
        return [(s, e) for _, s, e in jieba.tokenize(text)]

    # Fallback: character-class based
    boundaries = []
    start = 0
    prev = _char_class(text[0])
    for i in range(1, len(text)):
        cur = _char_class(text[i])
        if cur != prev:
            boundaries.append((start, i))
            start = i
            prev = cur
    boundaries.append((start, len(text)))
    return boundaries


def next_word_boundary(text, char_idx):
    for _, end in get_word_boundaries(text):
        if end > char_idx:
            return end
    return len(text)


def prev_word_boundary(text, char_idx):
    for start, _ in reversed(get_word_boundaries(text)):
        if start < char_idx:
            return start
    return 0


# ── Image paste ─────────────────────────────────────────────────────

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

    # Try pngpaste first
    try:
        r = subprocess.run(["pngpaste", filepath], capture_output=True, timeout=10)
        if r.returncode == 0 and os.path.exists(filepath):
            return filepath
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"pngpaste error: {e}")

    # Fallback: osascript → TIFF → sips convert
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
        logger.error(f"Fallback save error: {e}")
    return None


def format_image_output(config, filepath):
    fmt = config.get("paste_image", {}).get("output_format", "{path}")
    return fmt.format(
        path=filepath,
        filename=os.path.basename(filepath),
        dir=os.path.dirname(filepath),
    )


# ── Key handlers ────────────────────────────────────────────────────

async def handle_paste(session, config):
    if has_clipboard_image():
        filepath = save_clipboard_image(config)
        if filepath:
            output = format_image_output(config, filepath)
            logger.info(f"Pasted image: {output}")
            await session.async_send_text(output)
            return
    # No image — normal text paste
    try:
        r = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
        if r.stdout:
            await session.async_send_text(r.stdout)
    except Exception as e:
        logger.error(f"Text paste error: {e}")


async def get_cursor_line(session):
    """Get current line text and character index of cursor."""
    contents = await session.async_get_screen_contents()
    cx = contents.cursor_coord.x
    cy = contents.cursor_coord.y
    line = contents.line(cy)
    text = line.string.rstrip("\x00")
    # Strip trailing spaces (terminal pads to width) but keep meaningful ones
    text = text.rstrip(" ")
    char_idx = column_to_char_index(text, cx)
    return text, char_idx


async def handle_word_jump(session, forward):
    try:
        text, char_idx = await get_cursor_line(session)
        if not text:
            # Empty line, send default
            await session.async_send_text("\x1bf" if forward else "\x1bb")
            return

        if forward:
            target = next_word_boundary(text, char_idx)
            n = target - char_idx
            if n > 0:
                await session.async_send_text("\x1b[C" * n)
        else:
            target = prev_word_boundary(text, char_idx)
            n = char_idx - target
            if n > 0:
                await session.async_send_text("\x1b[D" * n)
    except Exception as e:
        logger.error(f"Word jump error: {e}", exc_info=True)
        await session.async_send_text("\x1bf" if forward else "\x1bb")


async def handle_word_delete(session):
    try:
        text, char_idx = await get_cursor_line(session)
        if not text or char_idx == 0:
            await session.async_send_text("\x1b\x7f")
            return

        target = prev_word_boundary(text, char_idx)
        n = char_idx - target
        if n > 0:
            await session.async_send_text("\x7f" * n)
    except Exception as e:
        logger.error(f"Word delete error: {e}", exc_info=True)
        await session.async_send_text("\x1b\x7f")


# ── Main ────────────────────────────────────────────────────────────

async def main(connection):
    logger.info("=" * 50)
    logger.info("Paw starting...")

    config = load_config()
    init_segmenter()

    features = config.get("features", {})
    patterns = []

    if features.get("paste_image", True):
        p = iterm2.KeystrokePattern()
        p.required_modifiers = [iterm2.Modifier.COMMAND]
        p.keycodes = [iterm2.Keycode.ANSI_V]
        patterns.append(p)

    if features.get("word_jump", True):
        for kc in (iterm2.Keycode.RIGHT_ARROW, iterm2.Keycode.LEFT_ARROW):
            p = iterm2.KeystrokePattern()
            p.required_modifiers = [iterm2.Modifier.OPTION]
            p.keycodes = [kc]
            patterns.append(p)

    if features.get("word_delete", True):
        p = iterm2.KeystrokePattern()
        p.required_modifiers = [iterm2.Modifier.OPTION]
        p.keycodes = [iterm2.Keycode.DELETE]
        patterns.append(p)

    if not patterns:
        logger.warning("No features enabled, exiting")
        return

    async def on_keystroke(keystroke, session):
        kc = keystroke.keycode
        mods = keystroke.modifiers
        logger.info(f"Keystroke: keycode={kc} modifiers={mods}")

        if iterm2.Modifier.COMMAND in mods and kc == iterm2.Keycode.ANSI_V:
            logger.info("→ handle_paste")
            await handle_paste(session, config)
        elif iterm2.Modifier.OPTION in mods and kc == iterm2.Keycode.RIGHT_ARROW:
            logger.info("→ handle_word_jump(forward)")
            await handle_word_jump(session, forward=True)
        elif iterm2.Modifier.OPTION in mods and kc == iterm2.Keycode.LEFT_ARROW:
            logger.info("→ handle_word_jump(backward)")
            await handle_word_jump(session, forward=False)
        elif iterm2.Modifier.OPTION in mods and kc == iterm2.Keycode.DELETE:
            logger.info("→ handle_word_delete")
            await handle_word_delete(session)
        else:
            logger.debug(f"Unhandled keystroke: {kc} {mods}")

    try:
        async with iterm2.KeystrokeFilter(connection, patterns):
            async with iterm2.KeystrokeMonitor(connection) as monitor:
                logger.info("Paw ready! Monitoring keystrokes...")
                while True:
                    keystroke = await monitor.async_get()
                    app = await iterm2.async_get_app(connection)
                    window = app.current_terminal_window
                    if not window:
                        continue
                    session = window.current_tab.current_session
                    if not session:
                        continue
                    await on_keystroke(keystroke, session)
    except Exception as e:
        logger.error(f"Plugin error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    iterm2.run_forever(main)
