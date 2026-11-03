#!/usr/bin/env bash
# Comprueba las dependencias de la configuración de Qtile.
# Uso: ~/.config/qtile/scripts/check-deps.sh

set -u

missing=0

check_cmd() {
    local cmd="$1"
    local pkg="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        printf '  OK    %-22s (%s)\n' "$cmd" "$pkg"
    else
        printf '  FALTA %-22s (sudo pacman -S %s)\n' "$cmd" "$pkg"
        missing=1
    fi
}

check_module() {
    local module="$1"
    local pkg="$2"
    if python3 -c "import $module" >/dev/null 2>&1; then
        printf '  OK    %-22s (python-%s)\n' "$module" "$pkg"
    else
        printf '  FALTA %-22s (sudo pacman -S python-%s)\n' "$module" "$pkg"
        missing=1
    fi
}

echo "Entorno y ventanas:"
check_cmd qtile qtile
check_cmd alacritty alacritty
check_cmd dmenu_run dmenu
check_cmd rofi rofi
check_cmd Xwayland xorg-xwayland

echo
echo "Widgets y barra:"
check_cmd wpctl wireplumber
check_cmd pactl libpulse
check_cmd pavucontrol pavucontrol
check_cmd playerctl playerctl
check_cmd brightnessctl brightnessctl
check_cmd notify-send libnotify
check_cmd mako mako
check_module dbus_fast dbus-fast

echo
echo "Bloqueo y energía:"
check_cmd swayidle swayidle
check_cmd swaylock swaylock
check_cmd wlopm wlopm

echo
echo "Capturas y wallpapers:"
check_cmd grim grim
check_cmd slurp slurp
check_cmd swappy swappy
check_cmd mpvpaper mpvpaper
check_cmd swaybg swaybg

echo
echo "Portapapeles:"
check_cmd wl-copy wl-clipboard
check_cmd wl-paste wl-clipboard
check_cmd cliphist cliphist

echo
echo "Aplicaciones de los atajos:"
check_cmd emacsclient emacs
check_cmd vlc vlc
check_cmd liferea liferea
check_cmd thunderbird thunderbird
check_cmd nautilus nautilus
check_cmd qalculate-gtk qalculate-gtk
check_cmd gcolor3 gcolor3
check_cmd bitwarden bitwarden
check_cmd zen-browser zen-browser-bin

echo
if [ "$missing" -ne 0 ]; then
    echo "Hay dependencias faltantes. Ejecuta:"
    echo "  ~/.config/qtile/scripts/install-deps.sh"
    exit 1
fi

echo "Todas las dependencias están instaladas."
