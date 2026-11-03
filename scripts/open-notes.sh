#!/usr/bin/env bash
# Abrir notas en la terminal

NOTES_FILE="$HOME/notes.md"

# Crear el archivo si no existe
if [ ! -f "$NOTES_FILE" ]; then
    echo "# Mis Notas" > "$NOTES_FILE"
    echo "" >> "$NOTES_FILE"
    echo "Creado: $(date)" >> "$NOTES_FILE"
fi

# Abrir con nano (o cambia a vim, emacs, etc.)
alacritty -e nano "$NOTES_FILE"
