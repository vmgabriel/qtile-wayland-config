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
echo "==> Comprobando dependencias..."
"$(dirname "$0")/check-deps.sh"
