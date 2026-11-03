#!/usr/bin/env bash
# Captura de área con Swappy

# Crear directorio temporal para la captura
TMP_DIR="/tmp/screenshots"
mkdir -p "$TMP_DIR"
TMP_FILE="$TMP_DIR/screenshot-$(date +%Y%m%d-%H%M%S).png"

# Tomar captura del área seleccionada
grim -g "$(slurp)" "$TMP_FILE"

# Verificar que se creó el archivo (el usuario no canceló)
if [ -f "$TMP_FILE" ]; then
    # Abrir en Swappy para editar
    swappy -f "$TMP_FILE"
    
    # Opcional: limpiar archivos temporales antiguos (más de 7 días)
    find "$TMP_DIR" -type f -mtime +7 -delete 2>/dev/null
fi
