# Paw - Terminal Text Enhancement
# Add this to your ~/.zshrc: source /path/to/paw.zsh

PAW_SOCK="${HOME}/.config/paw/paw.sock"
PAW_SEGMENTER="${HOME}/.config/paw/paw_segmenter.py"
PAW_PYTHON="${HOME}/.config/paw/venv/bin/python3"

# Start segmenter daemon if not running
paw-ensure-daemon() {
    local pidfile="${HOME}/.config/paw/paw.pid"
    if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        return 0
    fi
    "$PAW_PYTHON" "$PAW_SEGMENTER" &>/dev/null &
    disown
    sleep 0.5
}

# Query segmenter daemon
paw-query() {
    local text="$1" pos="$2" action="$3"
    [[ -z "$text" ]] && echo "$pos" && return
    printf '%s\t%s\t%s\n' "$text" "$pos" "$action" | nc -U "$PAW_SOCK" 2>/dev/null
}

# Forward word jump
paw-forward-word() {
    paw-ensure-daemon
    local result
    result=$(paw-query "$BUFFER" "$CURSOR" "next_word")
    if [[ "$result" =~ ^[0-9]+$ ]]; then
        CURSOR=$result
    else
        # Fallback: default zsh behavior
        zle forward-word
    fi
}
zle -N paw-forward-word

# Backward word jump
paw-backward-word() {
    paw-ensure-daemon
    local result
    result=$(paw-query "$BUFFER" "$CURSOR" "prev_word")
    if [[ "$result" =~ ^[0-9]+$ ]]; then
        CURSOR=$result
    else
        zle backward-word
    fi
}
zle -N paw-backward-word

# Backward delete word
paw-backward-delete-word() {
    paw-ensure-daemon
    local result start end
    result=$(paw-query "$BUFFER" "$CURSOR" "delete_word")
    if [[ "$result" =~ ^([0-9]+),([0-9]+)$ ]]; then
        start=${match[1]}
        end=${match[2]}
        BUFFER="${BUFFER[1,$start]}${BUFFER[$((end+1)),-1]}"
        CURSOR=$start
    else
        zle backward-delete-word
    fi
}
zle -N paw-backward-delete-word

# Bind keys (Option+Right, Option+Left, Option+Delete)
# These are the escape sequences sent when Option is set to Esc+
bindkey '\e[1;3C' paw-forward-word      # Option+Right (Esc+)
bindkey '\ef'     paw-forward-word      # Alt+F (some terminals)
bindkey '\e[1;3D' paw-backward-word     # Option+Left (Esc+)
bindkey '\eb'     paw-backward-word     # Alt+B (some terminals)
bindkey '\e\x7f'  paw-backward-delete-word  # Option+Delete
