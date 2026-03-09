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

def _is_cjk(ch):
    cp = ord(ch)
    return 0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF

def _is_break_char(t):
    """标点和空格做天然分界"""
    if not t.strip():
        return True
    if len(t) == 1:
        c = ord(t)
        if 0x21 <= c <= 0x2F or 0x3A <= c <= 0x40 or 0x5B <= c <= 0x60 or 0x7B <= c <= 0x7E:
            return True
        if 0x3000 <= c <= 0x303F or 0xFF01 <= c <= 0xFF0F or 0xFF1A <= c <= 0xFF20:
            return True
    return False

def _is_cjk_single(t):
    """单个 CJK 字符（非标点）"""
    return len(t) == 1 and _is_cjk(t[0])

def _merge_jieba_tokens(tokens):
    """将 jieba 的碎片单字词合并到相邻多字词，标点/空格处断开。
    规则：
    - 标点/空格处一定断开
    - 多字词之间正常断开
    - 1~2 个连续单字词吸附到紧跟其后的多字词（前缀吸附）
    - 尾部的单字词吸附到前一个多字词（后缀吸附）
    - 3 个以上连续单字词独立成组
    """
    if not tokens:
        return []

    # 先按标点/空格切成段，段内再合并
    segments = []
    cur_seg = [tokens[0]]
    for i in range(1, len(tokens)):
        t = tokens[i][0]
        prev_t = tokens[i - 1][0]
        if _is_break_char(t) or _is_break_char(prev_t):
            segments.append(cur_seg)
            cur_seg = [tokens[i]]
        else:
            cur_seg.append(tokens[i])
    segments.append(cur_seg)

    groups = []
    for seg in segments:
        if len(seg) == 1:
            groups.append((seg[0][1], seg[0][2]))
            continue

        # 段内：先标记每个 token 是否为单字
        is_single = [_is_cjk_single(t) for t, _, _ in seg]

        # 向前看：连续单字 + 后面紧跟的多字词合为一组
        i = 0
        while i < len(seg):
            if not is_single[i]:
                # 多字词，看前面有没有刚积攒的单字要吸附
                groups.append((seg[i][1], seg[i][2]))
                i += 1
            else:
                # 数连续单字
                j = i
                while j < len(seg) and is_single[j]:
                    j += 1
                n_singles = j - i
                if j < len(seg) and n_singles <= 2:
                    # 1~2 个单字 + 后面的多字词合并
                    groups.append((seg[i][1], seg[j][2]))
                    i = j + 1
                elif n_singles <= 2 and groups:
                    # 尾部 1~2 个单字，吸附到前一个组
                    prev_start, _ = groups[-1]
                    groups[-1] = (prev_start, seg[j - 1][2])
                    i = j
                else:
                    # 3+ 连续单字，独立成组
                    groups.append((seg[i][1], seg[j - 1][2]))
                    i = j
    return groups

def _fallback_boundaries(text):
    """无 jieba 时按字符类型分组"""
    import unicodedata
    if not text:
        return []
    def cls(ch):
        if ch.isspace(): return "s"
        if _is_cjk(ch): return "c"
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

def get_word_boundaries(text):
    if not text:
        return []
    if _jieba:
        tokens = [(t, s, e) for t, s, e in _jieba.tokenize(text)]
        return _merge_jieba_tokens(tokens)
    return _fallback_boundaries(text)

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
