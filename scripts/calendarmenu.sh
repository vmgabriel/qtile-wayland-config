#!/usr/bin/env bash
# Calendario rápido para Qtile (rofi)

set -u

header="$(date '+%A, %d de %B de %Y')"
calendar="$(cal -3 2>/dev/null || cal 2>/dev/null || date)"

printf 'Cerrar\n' | rofi -dmenu -i -p "Calendario" -mesg "$header

$calendar"
