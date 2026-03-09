#!/usr/bin/env python3
"""
Paw Segmenter Daemon
Listens on a Unix socket for segmentation requests.
Protocol: send "text\\tposition\\taction\\n", receive "new_position\\n"
Actions: next_word, prev_word, delete_word (returns "start,end")
"""

import os
import sys
import socket
import signal
import json

SOCKET_PATH = os.path.expanduser("~/.config/paw/paw.sock")
PID_FILE = os.path.expanduser("~/.config/paw/paw.pid")

def init_jieba():
    try:
        import jieba
        jieba.initialize()
        return jieba
    except ImportError:
        return None

_jieba = None

def get_word_boundaries(text):
    if _jieba:
        return [(s, e) for _, s, e in _jieba.tokenize(text)]
    # Fallback: character class segmentation
    import unicodedata
    if not text:
        return []
    def cls(ch):
        if ch.isspace(): return "s"
        cp = ord(ch)
        if 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF: return "c"
        cat = unicodedata.category(ch)
        if cat[0] in ("P", "S"): return "p"
        if ch.isalnum(): return "a"
        return "o"
    bounds, start, prev = [], 0, cls(text[0])
    for i in range(1, len(text)):
        c = cls(text[i])
        if c != prev:
            bounds.append((start, i))
            start, prev = i, c
    bounds.append((start, len(text)))
    return bounds

def next_word(text, pos):
    for _, end in get_word_boundaries(text):
        if end > pos:
            return end
    return len(text)

def prev_word(text, pos):
    for start, _ in reversed(get_word_boundaries(text)):
        if start < pos:
            return start
    return 0

def handle_request(data):
    try:
        parts = data.strip().split("\t")
        if len(parts) != 3:
            return "error: expected text\\tposition\\taction"
        text, pos_str, action = parts
        pos = int(pos_str)
        if action == "next_word":
            return str(next_word(text, pos))
        elif action == "prev_word":
            return str(prev_word(text, pos))
        elif action == "delete_word":
            target = prev_word(text, pos)
            return f"{target},{pos}"
        else:
            return f"error: unknown action {action}"
    except Exception as e:
        return f"error: {e}"

def cleanup(*_):
    for f in (SOCKET_PATH, PID_FILE):
        try: os.unlink(f)
        except: pass
    sys.exit(0)

def main():
    global _jieba
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)

    # Check existing instance
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"Already running (pid {old_pid})")
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            pass

    # Clean up old socket
    try: os.unlink(SOCKET_PATH)
    except FileNotFoundError: pass

    _jieba = init_jieba()
    print(f"jieba: {'loaded' if _jieba else 'fallback mode'}")

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(SOCKET_PATH)
    sock.listen(5)
    print(f"Listening on {SOCKET_PATH}")

    try:
        while True:
            conn, _ = sock.accept()
            try:
                data = conn.recv(65536).decode("utf-8")
                if data:
                    result = handle_request(data)
                    conn.sendall((result + "\n").encode("utf-8"))
            except Exception as e:
                try: conn.sendall(f"error: {e}\n".encode("utf-8"))
                except: pass
            finally:
                conn.close()
    finally:
        cleanup()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        if os.path.exists(PID_FILE):
            with open(PID_FILE) as f:
                os.kill(int(f.read().strip()), signal.SIGTERM)
            print("Stopped")
        else:
            print("Not running")
    else:
        main()
