#!/usr/bin/env bash
# Generar guía de atajos desde config.py

cat << 'EOF' | rofi -dmenu -i -p "Atajos de Qtile" -mesg "Presiona Esc para cerrar"
Super+j : Mover foco abajo
Super+k : Mover foco arriba
Super+h : Mover foco izquierda
Super+l : Mover foco derecha
Super+Shift+j : Mover ventana abajo
Super+Shift+k : Mover ventana arriba
Super+Shift+h : Mover ventana izquierda
Super+Shift+l : Mover ventana derecha
Super+Ctrl+h : Expandir izquierda
Super+Ctrl+l : Expandir derecha
Super+Ctrl+j : Expandir abajo
Super+Ctrl+k : Expandir arriba
Super+Space : Siguiente ventana
Super+Right : Siguiente layout
Super+Left : Layout anterior
Super+x : Cerrar ventana
Super+Return : Abrir terminal
Super+d : Menú rápido
Super+Delete : Bloquear pantalla
Super+Ctrl+r : Recargar configuración
Super+Shift+w : Video wallpaper aleatorio
Super+Ctrl+w : Siguiente video wallpaper
Super+Shift+s : Capturar y editar área
Super+Shift+p : Capturar pantalla completa
Super+e : Emacs
Super+r : Liferea
Super+t : Terminal
Super+Shift+m : Thunderbird
Super+v : VLC
Super+f : Archivos (Nautilus)
Super+o : Control de audio
Super+1-5 : Ir a workspace 1-5
Super+Shift+1-5 : Mover ventana a workspace
Super+` : Terminal desplegable
Super+c : Calculadora desplegable
Super+n : Notas desplegables
Super+minus : Bajar volumen
Super+plus : Subir volumen
Super+0 : Silenciar
Super+, : Pista anterior
Super+. : Pista siguiente
Super+' : Play/Pausa
EOF
