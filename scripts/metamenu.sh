#!/usr/bin/env bash
# Menú de acciones de Qtile

set -u

SCRIPTS="$HOME/.config/qtile/scripts"

choice=$(printf '%s\n' \
    "Lanzador (rofi)" \
    "Lanzador (dmenu)" \
    "Calendario" \
    "Temporizador" \
    "Audio / salidas" \
    "Captura de área" \
    "Captura de pantalla completa" \
    "Siguiente video wallpaper" \
    "Guía de atajos" \
    "Recargar Qtile" \
    "Bloquear pantalla" \
    | rofi -dmenu -i -p "Qtile")

[ -z "${choice:-}" ] && exit 0

case "$choice" in
    "Lanzador (rofi)")
        rofi -show drun -show-icons
        ;;
    "Lanzador (dmenu)")
        dmenu_run -i -p "Ejecutar:"
        ;;
    "Calendario")
        exec "$SCRIPTS/calendarmenu.sh"
        ;;
    "Temporizador")
        exec "$SCRIPTS/timermenu.sh"
        ;;
    "Audio / salidas")
        exec "$SCRIPTS/outputmenu.sh"
        ;;
    "Captura de área")
        exec "$SCRIPTS/screenshot-area.sh"
        ;;
    "Captura de pantalla completa")
        exec "$SCRIPTS/screenshot-full.sh"
        ;;
    "Siguiente video wallpaper")
        exec "$SCRIPTS/video_wallpaper.py" next
        ;;
    "Guía de atajos")
        exec "$SCRIPTS/show-hotkeys.sh"
        ;;
    "Recargar Qtile")
        qtile cmd-obj -o cmd -f reload_config
        ;;
    "Bloquear pantalla")
        exec "$SCRIPTS/screen-lock.py"
        ;;
esac
