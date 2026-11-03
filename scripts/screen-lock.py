#!/usr/bin/env python3
"""
Gestor de bloqueo de pantalla para Qtile Wayland.
Dependencia: swaylock (paquete swaylock)
Opcional:    grim (para usar una captura como fondo)
"""

import shutil
import subprocess
import sys
from pathlib import Path

SCREENSHOT = Path("/tmp/qtile-lock.png")


class ScreenLocker:
    def lock(self) -> None:
        """Ejecuta swaylock con un tema Gruvbox compatible con swaylock estándar."""
        if shutil.which("swaylock") is None:
            print("❌ Error: 'swaylock' no está instalado.")
            print("   Instala con: sudo pacman -S swaylock")
            sys.exit(1)

        args = [
            "swaylock",
            # Colores Gruvbox
            "--color", "282828cc",
            "--inside-color", "28282888",
            "--ring-color", "458588",
            "--key-hl-color", "98971a",
            "--line-color", "00000000",
            "--separator-color", "00000000",
            "--text-color", "a89984",
            # Indicador
            "--indicator-radius", "100",
            "--indicator-thickness", "7",
            # Tipografía
            "--font", "Noto Sans",
            "--font-size", "24",
            # Seguridad
            "--ignore-empty-password",
            "--show-failed-attempts",
        ]

        # Si grim está disponible, usamos una captura como fondo.
        if shutil.which("grim"):
            try:
                result = subprocess.run(
                    ["grim", str(SCREENSHOT)],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0 and SCREENSHOT.exists():
                    args.extend(["--image", str(SCREENSHOT), "--scaling", "fill"])
            except (OSError, subprocess.SubprocessError):
                pass

        print("🔒 Bloqueando pantalla...")
        try:
            subprocess.run(args, check=True)
            print("✅ Pantalla desbloqueada.")
        except subprocess.CalledProcessError as exc:
            print(f"❌ Error al ejecutar swaylock (código {exc.returncode})")
        except KeyboardInterrupt:
            print("\n⚠️  Bloqueo cancelado por el usuario.")


def main() -> None:
    ScreenLocker().lock()


if __name__ == "__main__":
    main()
