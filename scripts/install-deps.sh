#!/usr/bin/env bash
# Instala las dependencias que usan esta configuración de Qtile.
# Ejecutar con: ~/.config/qtile/scripts/install-deps.sh

set -euo pipefail

# Dependencias del entorno Wayland, widgets y menús.
CORE=(
    python-dbus-fast   # StatusNotifier + notificaciones de Qtile
    wlopm              # apagar/encender la pantalla con swayidle
    cliphist           # historial del portapapeles
    xorg-xwayland      # dmenu y aplicaciones X11
    dmenu
    rofi
    swayidle
    swaylock
    grim
    slurp
    swappy
    wl-clipboard
    mpvpaper
    swaybg
    ffmpeg
    playerctl
    brightnessctl
    pavucontrol
    libpulse
    libnotify
    mako
    pipewire
    wireplumber
)

# Aplicaciones que se abren desde atajos del config.py
APPS=(
    alacritty
    emacs
    vlc
    liferea
    thunderbird
    nautilus
    qalculate-gtk
    gcolor3
    bitwarden
)

echo "==> Instalando dependencias base..."
sudo pacman -S --needed "${CORE[@]}"

echo "==> Instalando aplicaciones de los atajos..."
sudo pacman -S --needed "${APPS[@]}"

echo
echo "==> Instalando pywal16 para el tema dinámico (sin sudo)..."
if ! command -v wal >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/wal" ]; then
    if command -v uv >/dev/null 2>&1; then
        uv tool install pywal16
        uv pip install --python "$HOME/.local/share/uv/tools/pywal16/bin/python" colorthief
    else
        echo "  Aviso: instala 'uv' y ejecuta: uv tool install pywal16"
    fi
fi

echo
echo "==> Comprobando dependencias..."
"$(dirname "$0")/check-deps.sh"
