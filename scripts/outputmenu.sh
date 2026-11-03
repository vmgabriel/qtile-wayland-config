#!/usr/bin/env bash
# Selector de salida de audio (PipeWire/PulseAudio) para Qtile

set -u

if ! command -v pactl >/dev/null 2>&1; then
    notify-send "Audio" "Falta pactl (paquete libpulse)" 2>/dev/null || true
    exit 1
fi

default_sink=$(pactl get-default-sink 2>/dev/null || true)

# Formato: id<TAB>nombre<TAB>descripción
mapfile -t sinks < <(
    pactl list short sinks 2>/dev/null | awk -F'\t' -v def="$default_sink" '
        {
            marker = ($2 == def) ? "* " : "  "
            printf "%s%s\t%s\n", marker, $2, $1
        }
    '
)

if [ "${#sinks[@]}" -eq 0 ]; then
    notify-send "Audio" "No se encontraron salidas de audio" 2>/dev/null || true
    exit 1
fi

choice=$(printf '%s\n' "${sinks[@]}" | rofi -dmenu -i -p "Salida de audio")
[ -z "${choice:-}" ] && exit 0

sink_id=$(printf '%s\n' "$choice" | awk -F'\t' '{print $2}')

if [ -n "$sink_id" ]; then
    pactl set-default-sink "$sink_id"
    pactl set-sink-mute "$sink_id" 0
    notify-send "Audio" "Salida cambiada a: $(printf '%s\n' "$choice" | awk -F'\t' '{print $1}' | sed 's/^[* ]*//')" 2>/dev/null || true
fi
