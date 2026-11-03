# -*- coding: utf-8 -*-
"""
Configuración Qtile para Wayland - Versión Final con Swappy
Autor: vmgabriel
Entorno: Arch Linux + Wayland
Fecha: 2026-09-19
"""

import os
import subprocess
import json
import re
from typing import List

from libqtile import bar, layout, widget, hook, qtile
from libqtile.config import Click, Drag, Group, Key, KeyChord, Match, Screen, ScratchPad, DropDown
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal

# =============================================================================
# 🔧 CONFIGURACIÓN BÁSICA
# =============================================================================

mod = "mod4"
terminal = "alacritty"
city_weather_code = "3688689"

# =============================================================================
# 🎨 COLORES (Gruvbox con fallback)
# =============================================================================

default_colors = {
    "color0": "#282828",  # fondo
    "color1": "#cc241d",  # rojo
    "color2": "#98971a",  # verde
    "color3": "#d79921",  # amarillo
    "color4": "#458588",  # azul
    "color5": "#b16286",  # morado
    "color6": "#689d6a",  # cian
    "color7": "#a89984",  # texto
    "color8": "#928374",  # gris
    "color9": "#fb4934",  # rojo claro
}

try:
    colors_path = os.path.expanduser("~/.cache/wal/colors.json")
    with open(colors_path) as f:
        colordict = json.load(f)
    ColorZ = colordict["colors"]["color0"]
    ColorA = colordict["colors"]["color1"]
    ColorB = colordict["colors"]["color2"]
    ColorC = colordict["colors"]["color3"]
    ColorD = colordict["colors"]["color4"]
    ColorE = colordict["colors"]["color5"]
    ColorF = colordict["colors"]["color6"]
    ColorG = colordict["colors"]["color7"]
    ColorH = colordict["colors"]["color8"]
    ColorI = colordict["colors"]["color9"]
except (FileNotFoundError, KeyError, json.JSONDecodeError):
    ColorZ = default_colors["color0"]
    ColorA = default_colors["color1"]
    ColorB = default_colors["color2"]
    ColorC = default_colors["color3"]
    ColorD = default_colors["color4"]
    ColorE = default_colors["color5"]
    ColorF = default_colors["color6"]
    ColorG = default_colors["color7"]
    ColorH = default_colors["color8"]
    ColorI = default_colors["color9"]

# =============================================================================
# 🚀 FUNCIONES AUXILIARES
# =============================================================================

def run(cmd: str):
    """Ejecuta un comando en segundo plano."""
    return lazy.spawn(cmd)

# Funciones para video wallpapers
script_video_wallpaper = "~/.config/qtile/scripts/video_wallpaper.py"

def video_wallpaper_random() -> None:
    qtile.spawn(os.path.expanduser(script_video_wallpaper + " random"))

def video_wallpaper_next() -> None:
    qtile.spawn(os.path.expanduser(script_video_wallpaper + " next"))

def video_wallpaper_stop() -> None:
    qtile.spawn(os.path.expanduser(script_video_wallpaper + " stop"))

# Funciones para el bloqueo de pantalla
script_screen_lock = "~/.config/qtile/scripts/screen-lock.py"

def lock_screen():
    """Bloquea la pantalla usando el script de Python"""
    qtile.spawn(os.path.expanduser(script_screen_lock))

def execute_daemon_lock_screen() -> None:
    lock_time_min = 5
    turn_off_display_min = 10
    
    subprocess.Popen([
        "swayidle", "-w",
        "timeout", str(lock_time_min * 60), os.path.expanduser(script_screen_lock),
        "timeout", str(turn_off_display_min * 60), "swaymsg 'output * dpms off'",
        "resume", "swaymsg 'output * dpms on'",
        "before-sleep", os.path.expanduser(script_screen_lock),
        "lock", os.path.expanduser(script_screen_lock)
    ])
    
# Atajos personalizados
htop = run(f"{terminal} -e htop")
powermenu = run("powermenu")
sound = run("outputmenu")
calendar = run(f"{terminal} -e khal interactive")
timer = run("timermenu")
launcher = run("rofi -show drun -show-icons")
metamenu = run("metamenu")

# =============================================================================
# ⚙️ HOOKS
# =============================================================================

@hook.subscribe.startup_once
def autostart() -> None:
    """Inicio de Session"""
    video_wallpaper_random()
    execute_daemon_lock_screen()

# =============================================================================
# ⌨️ ATAJOS DE TECLADO
# =============================================================================

keys = [
    # --- Navegación ---
    Key([mod], "j", lazy.layout.down(), desc="Mover foco abajo"),
    Key([mod], "k", lazy.layout.up(), desc="Mover foco arriba"),
    Key([mod], "h", lazy.layout.left(), desc="Mover foco izquierda"),
    Key([mod], "l", lazy.layout.right(), desc="Mover foco derecha"),

    # --- Movimiento de ventanas ---
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Mover ventana abajo"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Mover ventana arriba"),
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Mover ventana izquierda"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Mover ventana derecha"),
    Key([mod, "mod1"], "n", lazy.layout.normalize(), desc="Normalizar tamaños"),

    # --- Redimensionar ---
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Expandir izquierda"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Expandir derecha"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Expandir abajo"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Expandir arriba"),

    # --- Video Wallpapers ---
    Key([mod, "shift"], "w", 
        lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/video_wallpaper.py random")),
        desc="Video wallpaper aleatorio"),
    Key([mod, "control"], "w",
        lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/video_wallpaper.py next")),
        desc="Siguiente video wallpaper"),
    Key([mod, "control", "shift"], "w",
        lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/video_wallpaper.py stop")),
        desc="Detener video wallpaper"),

    # --- Capturas de Pantalla con Swappy (Atajos rápidos) ---
    Key([mod, "shift"], "s", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/screenshot-area.sh")), desc="Capturar y editar área"),
    Key([mod, "shift"], "p", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/screenshot-full.sh")), desc="Capturar y editar pantalla completa"),

    # --- Bloqueo de Pantalla ---
    Key([mod], "Delete", lazy.function(lock_screen), desc="Bloquear pantalla"),

    # --- Layouts ---
    Key([mod], "space", lazy.layout.next(), desc="Siguiente ventana"),
    Key([mod], "Right", lazy.next_layout(), desc="Siguiente layout"),
    Key([mod], "Left", lazy.prev_layout(), desc="Layout anterior"),

    # --- Ventanas ---
    Key([], "F11", lazy.window.toggle_fullscreen(), desc="Pantalla completa"),
    Key([], "F10", lazy.window.toggle_floating(), desc="Modo flotante"),
    Key([mod], "x", lazy.window.kill(), desc="Cerrar ventana"),

    # --- Sistema ---
    Key([mod], "d", lazy.spawn("dmen"), desc="Cargas Menu Rapido"),
    Key([mod], "Return", lazy.spawn(terminal), desc="Abrir terminal"),
    Key([mod], "F12", lazy.group["scratchpad"].dropdown_toggle("term"), desc="Terminal desplegable"),
    Key([mod], "c", lazy.group["scratchpad"].dropdown_toggle("calc"), desc="Calculadora"),
    Key([mod], "n", lazy.group["scratchpad"].dropdown_toggle("notes"), desc="Notas"),

    # --- Recargar/Reiniciar ---
    Key([mod, "control"], "r", lazy.reload_config(), desc="Recargar configuración"),

    # --- Menús ---
    KeyChord([mod], "q", [
        Key([], "r", lazy.restart(), desc="Reiniciar Qtile"),
        Key([], "q", lazy.shutdown(), desc="Cerrar sesión"),
        Key([], "c", lazy.spawn("clipmenu"), desc="Portapapeles"),
    ]),
    KeyChord([mod], "a", [
        Key([], "w", lazy.spawn("zen-browser"), desc="Zen Browser"),
        Key([], "p", lazy.spawn("bitwarden-desktop"), desc="Bitwarden"),
        Key([], "c", lazy.spawn("gcolor3"), desc="Selector de color"),
    ]),
    KeyChord([mod], "m", [
        Key([], "space", launcher, desc="Lanzador"),
        Key([], "h", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/show-hotkeys.sh")), desc="Guía de atajos"),
        # ✅ Integración con Swappy para editar antes de guardar/copiar
        Key([], "s", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/screenshot-area.sh")), desc="Capturar y editar área"),
        Key([], "p", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/screenshot-full.sh")), desc="Capturar y editar pantalla completa"),
        Key([], "c", lazy.spawn("calendarmenu"), desc="Calendario"),
        Key([], "t", lazy.spawn("timermenu"), desc="Temporizador"),
    ]),

    # --- Volumen (PipeWire) ---
    Key([mod], "minus", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 3%-"), desc="Bajar volumen"),
    Key([mod], "plus", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 3%+"), desc="Subir volumen"),
    Key([mod], "0", lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), desc="Silenciar"),

    # --- Teclas multimedia de volumen ---
    Key([], "XF86AudioRaiseVolume", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+"), desc="Volumen +"),
    Key([], "XF86AudioLowerVolume", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), desc="Volumen -"),
    Key([], "XF86AudioMute", lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), desc="Silenciar"),
    Key([], "XF86AudioPlay", lazy.spawn("playerctl play-pause"), desc="Play/Pausa"),
    Key([], "XF86AudioNext", lazy.spawn("playerctl next"), desc="Siguiente"),
    Key([], "XF86AudioPrev", lazy.spawn("playerctl previous"), desc="Anterior"),

    # --- Brillo de pantalla ---
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set +5%"), desc="Brillo +"),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-"), desc="Brillo -"),

    # --- Multimedia (playerctl) ---
    Key([mod], "comma", lazy.spawn("playerctl previous"), desc="Anterior"),
    Key([mod], "period", lazy.spawn("playerctl next"), desc="Siguiente"),
    Key([mod], "apostrophe", lazy.spawn("playerctl play-pause"), desc="Play/Pausa"),

    # --- Aplicaciones ---
    Key([mod], "e", lazy.spawn("emacsclient -c -a ''"), desc="Emacs"),
    Key([mod], "r", lazy.spawn("liferea"), desc="Liferea"),
    Key([mod], "t", lazy.spawn(terminal), desc="Terminal"),
    Key([mod, "shift"], "m", lazy.spawn("thunderbird"), desc="Thunderbird"),
    Key([mod], "v", lazy.spawn("vlc"), desc="VLC"),
    Key([mod], "f", lazy.spawn("nautilus"), desc="Archivos"),
    Key([mod], "o", lazy.spawn("pwvucontrol"), desc="Audio avanzado"),
]

# --- Grupos (workspaces) ---
groups = [
    ScratchPad("scratchpad", [
        DropDown("term", terminal, opacity=0.95),
        DropDown("calc", "qalculate-gtk", opacity=0.95),
        DropDown("notes", f"{terminal} -e emacs -nw ~/notes.md", opacity=0.95),
    ]),
    Group("I", layout="monadtall", matches=[Match(wm_class=re.compile(r"^(qutebrowser|Thunderbird|liferea)$"))]),
    Group("II", layout="monadtall", matches=[Match(wm_class=re.compile(r"^(vlc|gpodder)$"))]),
    Group("III", layout="bsp", matches=[Match(wm_class=re.compile(r"^(Steam|Lutris|RetroArch|dosbox)$"))]),
    Group("IV", layout="max", matches=[Match(wm_class=re.compile(r"^(VirtualBox\ Machine|virt-manager|VirtualBox\ Manager|VirtualBoxVM)$"))]),
    Group("V", layout="max", matches=[Match(wm_class=re.compile(r"^(gimp|Inkscape|krita|darktable|shotwell|scribus|Blender)$"))]),
]

for i, group in enumerate(groups[1:], 1):
    keys.extend([
        Key([mod], str(i), lazy.group[group.name].toscreen(), desc=f"Ir a {group.name}"),
        Key([mod, "shift"], str(i), lazy.window.togroup(group.name), desc=f"Mover a {group.name}"),
    ])

# =============================================================================
# 🖼️ LAYOUTS Y PANTALLAS
# =============================================================================

layouts = [
    layout.MonadTall(
        margin=8,
        border_focus=ColorE,
        border_normal=ColorA,
        border_width=2,
        ratio=0.6,
    ),
    layout.Bsp(
        margin=8,
        border_focus=ColorE,
        border_normal=ColorA,
        border_width=2,
    ),
    layout.Max(),
]

widget_defaults = dict(
    font="Noto Sans",
    fontsize=13,
    padding=5,
    foreground=ColorG,
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        top=bar.Bar(
            [
                widget.GroupBox(
                    highlight_method="line",
                    urgent_border=ColorF,
                    active=ColorG,
                    inactive=ColorB,
                    this_current_screen_border=ColorC,
                ),
                widget.Spacer(),
                widget.Clock(
                    format="%a %b %d",
                    font="Noto Sans Bold",
                    mouse_callbacks={"Button1": calendar}
                ),
                widget.Clock(
                    format="%I:%M %p",
                    font="Noto Sans Bold",
                    mouse_callbacks={"Button1": timer}
                ),
                widget.Spacer(),
                widget.TextBox(text="🔊", mouse_callbacks={"Button1": sound}),
                widget.Volume(),
                widget.TextBox(text="⏻", mouse_callbacks={"Button1": powermenu}),
            ],
            size=22,
            background="#282828",
        ),
        bottom=bar.Bar(
            [
                widget.TextBox(text="⚡", foreground=ColorB, mouse_callbacks={"Button1": launcher}),
                widget.WindowName(font="Noto Sans Bold"),
                widget.GenPollText(
                    func=lambda: subprocess.getoutput("playerctl metadata --format '🎵{{ artist }} - {{ title }}🎵' 2>/dev/null || echo '⏹'"),
                    update_interval=5,
                    foreground=ColorG,
                    max_chars=50,
                ),
                widget.CPU(mouse_callbacks={"Button1": htop}),
                widget.Memory(format="MEM {MemUsed:.0f}{mm}", mouse_callbacks={"Button1": htop}),
                widget.StatusNotifier(),
                widget.CurrentLayout(),
                widget.TextBox(text="☰", mouse_callbacks={"Button1": metamenu}),
            ],
            size=22,
            background="#282828",
        ),
        # Gaps alrededor de la pantalla
        left=bar.Gap(8),
        right=bar.Gap(8),
    )
]

# =============================================================================
# 🖱️ MOUSE Y COMPORTAMIENTO
# =============================================================================

mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

floating_layout = layout.Floating(
    border_focus=ColorE,
    border_normal=ColorA,
    float_rules=[
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),
        Match(wm_class="makebranch"),
        Match(wm_class="maketag"),
        Match(wm_class="ssh-askpass"),
        Match(title="branchdialog"),
        Match(title="pinentry"),
        Match(title="khal"),
        Match(wm_class="confirm"),
        Match(wm_class="dialog"),
        Match(wm_class="download"),
        Match(wm_class="error"),
        Match(wm_class="file_progress"),
        Match(wm_class="notification"),
        Match(wm_class="splash"),
        Match(wm_class="toolbar"),
        Match(wm_class="gcolor3"),
        Match(wm_class="qalculate-gtk"),
        Match(wm_class="qt5ct"),
        Match(func=lambda c: bool(c.name and c.name.startswith("Picture-in-Picture"))),
    ]
)

# =============================================================================
# ⚙️ OPCIONES GENERALES
# =============================================================================

follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = False
auto_minimize = False
wmname = "LG3D"

# =============================================================================
# ⌨️ CONFIGURACIÓN DE TECLADO (WAYLAND)
# =============================================================================

keyboard_layout = "latam"

wl_input_rules = {
    "type:keyboard": {
        "xkb_layout": "latam",
        "xkb_variant": "",
        "xkb_options": "terminate:ctrl_alt_bksp"
    }
}

wl_xcursor_theme = "Adwaita"
wl_xcursor_size = 24
