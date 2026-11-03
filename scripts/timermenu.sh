#!/usr/bin/env bash
# Temporizador rápido con notificación para Qtile

set -u

minutes=$(printf '' | rofi -dmenu -p "Minutos")

# Solo aceptamos números positivos.
if ! [[ "${minutes:-}" =~ ^[0-9]+$ ]] || [ "$minutes" -le 0 ]; then
    exit 0
fi

seconds=$((minutes * 60))
notify-send "Temporizador" "Iniciado: ${minutes} minuto(s)" 2>/dev/null || true

(
    sleep "$seconds"
    notify-send -u critical "Temporizador" "¡Tiempo cumplido! (${minutes} minuto(s))" 2>/dev/null || true
    if command -v paplay >/dev/null 2>&1; then
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || true
    fi
) >/dev/null 2>&1 &
