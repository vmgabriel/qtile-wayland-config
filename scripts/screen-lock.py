#!/usr/bin/env python3
"""
Gestor de Bloqueo de Pantalla para Qtile Wayland
Autor: vmgabriel
Dependencia: swaylock-effects (recomendado)
"""

import os
import subprocess
import sys
from pathlib import Path


class ScreenLocker:
    def __init__(self) -> None:
        # Verificar si swaylock está instalado
        if not self._check_command("swaylock"):
            print("❌ Error: 'swaylock' no está instalado.")
            print("   Instala con: sudo pacman -S swaylock-effects")
            sys.exit(1)

    def _check_command(self, cmd: str) -> bool:
        """Verifica si un comando existe en el PATH"""
        try:
            subprocess.run(["which", cmd], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def lock(self) -> None:
        """Ejecuta swaylock con tema Gruvbox y efectos"""
        # Argumentos corregidos: --timestr y --datestr (no --time-format/--date-format)
        args = [
            "swaylock",
            # Efectos visuales (requiere swaylock-effects)
            "--effect-blur", "10x5",          # Desenfoque del fondo
            "--effect-vignette", "0.5:0.5",   # Viñeta oscura en bordes
            
            # Indicador
            "--indicator",                     # Mostrar indicador siempre
            "--indicator-radius", "100",
            "--indicator-thickness", "7",
            
            # Colores Gruvbox
            "--ring-color", "458588",         # Azul (anillo normal)
            "--key-hl-color", "98971a",       # Verde (al escribir)
            "--line-color", "00000000",       # Transparente
            "--inside-color", "28282888",     # Fondo oscuro semi-transparente
            "--separator-color", "00000000",  # Transparente
            "--text-color", "a89984",         # Texto claro
            
            # Tipografía
            "--font", "Noto Sans",
            "--font-size", "24",
            
            # Reloj y fecha (argumentos CORREGIDOS)
            "--clock",                         # Mostrar reloj
            "--timestr", "%H:%M",             # ✅ Formato de hora
            "--datestr", "%a, %d %b",         # ✅ Formato de fecha
            
            # Seguridad
            "--ignore-empty-password",        # No validar contraseña vacía
            "--show-failed-attempts"          # Mostrar intentos fallidos
        ]

        print("🔒 Bloqueando pantalla...")
        try:
            subprocess.run(args, check=True)
            print("✅ Pantalla desbloqueada.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error al ejecutar swaylock (código {e.returncode})")
        except KeyboardInterrupt:
            print("\n⚠️  Bloqueo cancelado por el usuario.")


def main() -> None:
    locker = ScreenLocker()
    locker.lock()

    
if __name__ == "__main__":
    main()

