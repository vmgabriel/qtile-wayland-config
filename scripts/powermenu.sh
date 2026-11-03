#!/usr/bin/env bash
# Menú de energía para Qtile Wayland (rofi)

set -u

ROFI=(rofi -dmenu -i -p "Sistema")

choice=$(printf '%s\n' \
    "Bloquear pantalla" \
    "Suspender" \
    "Cerrar sesión" \
    "Reiniciar" \
    "Apagar" \
    | "${ROFI[@]}")

[ -z "${choice:-}" ] && exit 0

case "$choice" in
    "Bloquear pantalla")
        exec "$HOME/.config/qtile/scripts/screen-lock.py"
        ;;
    "Suspender")
        systemctl suspend
        ;;
    "Cerrar sesión")
        if command -v loginctl >/dev/null 2>&1 && [ -n "${XDG_SESSION_ID:-}" ]; then
            loginctl terminate-session "$XDG_SESSION_ID"
        else
            qtile cmd-obj -o cmd -f shutdown
        fi
        ;;
    "Reiniciar")
        systemctl reboot
        ;;
    "Apagar")
        systemctl poweroff
        ;;
esac
