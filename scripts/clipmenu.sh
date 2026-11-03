#!/usr/bin/env bash
# Historial del portapapeles para Qtile Wayland

set -u

if command -v cliphist >/dev/null 2>&1; then
    selection=$(cliphist list | rofi -dmenu -i -p "Portapapeles")
    [ -z "${selection:-}" ] && exit 0
    printf '%s' "$selection" | cliphist decode | wl-copy
else
    # Sin cliphist solo se puede mostrar el contenido actual.
    content=$(wl-paste --no-newline 2>/dev/null || true)
    [ -z "$content" ] && exit 0
    printf '%s' "$content" | rofi -dmenu -i -p "Portapapeles actual" >/dev/null
fi
