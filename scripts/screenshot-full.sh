#!/usr/bin/env bash
# Captura de pantalla completa con Swappy

TMP_DIR="/tmp/screenshots"
mkdir -p "$TMP_DIR"
TMP_FILE="$TMP_DIR/screenshot-$(date +%Y%m%d-%H%M%S).png"

# Tomar captura de toda la pantalla
grim "$TMP_FILE"

if [ -f "$TMP_FILE" ]; then
    swappy -f "$TMP_FILE"
    find "$TMP_DIR" -type f -mtime +7 -delete 2>/dev/null
fi
