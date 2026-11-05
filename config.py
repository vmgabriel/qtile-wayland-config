# -*- coding: utf-8 -*-
"""
Configuración Qtile para Wayland - Versión Final con Swappy
Autor: vmgabriel
Entorno: Arch Linux + Wayland
Fecha: 2026-09-19

Soporta portátil y escritorio mediante la flag MACHINE_TYPE
("portatil" / "escritorio" / "auto") definida más abajo.
"""

import os
import subprocess
import json
import re
import shutil
import sys
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
# 💻 TIPO DE EQUIPO (flag portátil / escritorio)
# =============================================================================
# Cambia esta flag según el equipo donde se ejecute Qtile:
#   "portatil"   -> laptop: widget de batería, brillo del panel integrado,
#                   bloqueo/suspensión agresivos, una sola pantalla.
#   "escritorio" -> PC de escritorio: sin batería, brillo por DDC/CI (ddcutil),
#                   tiempos de bloqueo más largos, soporte multimonitor con
#                   hot-plug (reconfigure_screens).
#   "auto"       -> autodetecta según la presencia de una batería real.
MACHINE_TYPE = "escritorio"

# Número de monitores esperados en modo escritorio (en portátil se ignora).
# Si conectas/desconectas monitores, Qtile se reconfigura solo gracias a
# reconfigure_screens = True.
DESKTOP_MONITORS = 1

def detect_is_laptop() -> bool:
    """Detecta si el equipo tiene batería real (portátil)."""
    power_supply_dir = "/sys/class/power_supply"
    if not os.path.isdir(power_supply_dir):
        return False
    for entry in os.listdir(power_supply_dir):
        type_file = os.path.join(power_supply_dir, entry, "type")
        try:
            with open(type_file, encoding="utf-8") as fh:
                if fh.read().strip().lower() == "battery":
                    return True
        except OSError:
            continue
    return False

if MACHINE_TYPE == "auto":
    IS_LAPTOP = detect_is_laptop()
else:
    IS_LAPTOP = MACHINE_TYPE == "portatil"

# =============================================================================
# 🎨 COLORES (pywal dinámico con fallback Gruvbox)
# =============================================================================
# theme-sync.py escribe theme_palette.json a partir del wallpaper actual.
# Si el archivo no existe (o pywal falla) se usa esta paleta de respaldo.

fallback_palette = {
    "background": "#1d2021",
    "surface": "#282828",
    "surface_alt": "#32302f",
    "foreground": "#ebdbb2",
    "muted": "#a89984",
    "border": "#504945",
    "accent": "#d79921",
    "accent2": "#458588",
    "on_accent": "#1d2021",
    "urgent": "#fb4934",
    "success": "#b8bb26",
    "warning": "#fabd2f",
    "info": "#83a598",
}

palette = fallback_palette.copy()
palette_path = os.path.expanduser("~/.config/qtile/theme_palette.json")

try:
    with open(palette_path, encoding="utf-8") as fh:
        loaded_palette = json.load(fh)
    # Solo sobrescribimos claves de color; ignoramos metadatos (rutas, timestamps).
    palette.update(
        {key: value for key, value in loaded_palette.items() if isinstance(value, str)}
    )
except (FileNotFoundError, OSError, json.JSONDecodeError):
    pass

ColorZ = palette["background"]        # fondo de la barra
ColorSurface = palette["surface"]     # fondo de widgets destacados
ColorG = palette["foreground"]        # texto principal
ColorH = palette["muted"]             # texto secundario
ColorBorder = palette["border"]       # bordes y separadores
ColorE = palette["accent"]            # acento principal
ColorF = palette["accent2"]           # acento secundario
ColorOnAccent = palette["on_accent"]  # texto sobre el acento
ColorA = palette["urgent"]            # rojo / urgencias
ColorI = palette["urgent"]            # rojo / batería baja
ColorB = palette["success"]           # verde / batería cargando
ColorC = palette["warning"]           # amarillo / avisos
ColorD = palette["info"]              # azul / información

# =============================================================================
# 🚀 FUNCIONES AUXILIARES
# =============================================================================

def run(cmd: str):
    """Ejecuta un comando en segundo plano."""
    return lazy.spawn(cmd)

def script(name: str) -> str:
    """Ruta absoluta a un script de la configuración."""
    return os.path.expanduser(f"~/.config/qtile/scripts/{name}")

script_theme_sync = "~/.config/qtile/scripts/theme-sync.py"

def theme_sync(*args: str) -> None:
    """Regenera la paleta (pywal), el tema de rofi y los colores de dmenu."""
    path = os.path.expanduser(script_theme_sync)
    if not os.path.exists(path):
        return
    subprocess.Popen(
        [sys.executable, path, *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

def module_available(name: str) -> bool:
    """Comprueba si un módulo de Python está instalado."""
    try:
        __import__(name)
        return True
    except ImportError:
        return False

# dbus-fast es opcional: sin él, StatusNotifier no se puede usar.
HAS_DBUS_FAST = module_available("dbus_fast")

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
    """Bloqueo por inactividad y apagado de pantalla con swayidle."""
    if IS_LAPTOP:
        # Portátil: bloqueo y apagado de pantalla más agresivos para ahorrar batería.
        lock_time_min = 5
        turn_off_display_min = 10
    else:
        # Escritorio: tiempos más relajados (no hay batería que cuidar).
        lock_time_min = 15
        turn_off_display_min = 30
    lock_cmd = os.path.expanduser(script_screen_lock)

    if not shutil.which("swayidle"):
        return

    args = [
        "swayidle", "-w",
        "timeout", str(lock_time_min * 60), lock_cmd,
    ]

    # wlopm es la alternativa Wayland a `swaymsg output * dpms off`.
    if shutil.which("wlopm"):
        args.extend([
            "timeout", str(turn_off_display_min * 60), "wlopm --off '*'",
            "resume", "wlopm --on '*'",
        ])

    args.extend([
        "before-sleep", lock_cmd,
        "lock", lock_cmd,
    ])

    try:
        subprocess.Popen(args)
    except FileNotFoundError:
        pass

def apply_fallback_wallpaper() -> None:
    """Usa una imagen fija si todavía no hay videos de wallpaper."""
    image = os.path.expanduser("~/.config/qtile/screens/qtilechameleon1.png")
    if shutil.which("swaybg") and os.path.exists(image):
        subprocess.Popen(
            ["swaybg", "-i", image, "-m", "fill"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

def has_video_wallpapers() -> bool:
    video_dir = os.path.expanduser("~/Vídeos/wallpapers")
    if not os.path.isdir(video_dir):
        return False
    extensions = (".mp4", ".webm", ".mkv", ".avi")
    return any(name.lower().endswith(extensions) for name in os.listdir(video_dir))

def start_clipboard_history() -> None:
    """Guarda el historial del portapapeles para clipmenu.sh."""
    if not (shutil.which("cliphist") and shutil.which("wl-paste")):
        return

    for mime_type in ("text", "image"):
        subprocess.Popen(
            ["wl-paste", "--type", mime_type, "--watch", "cliphist", "store"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

def start_notification_daemon() -> None:
    """Inicia mako si no hay un servidor de notificaciones activo."""
    if not shutil.which("mako"):
        return

    running = subprocess.run(
        ["pgrep", "-x", "mako"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if running.returncode == 0:
        return

    subprocess.Popen(
        ["mako"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

# Atajos personalizados
htop = run(f"{terminal} -e htop")
powermenu = run(script("powermenu.sh"))
sound = run(script("outputmenu.sh"))
calendar = run(script("calendarmenu.sh"))
timer = run(script("timermenu.sh"))
clipmenu = run(script("clipmenu.sh"))
launcher = run("rofi -show drun -show-icons")
metamenu = run(script("metamenu.sh"))

# Brillo de pantalla según el tipo de equipo:
#   - Portátil: retroiluminación integrada con brightnessctl.
#   - Escritorio: monitores externos vía DDC/CI con ddcutil (si está instalado).
if IS_LAPTOP:
    brightness_up_cmd = "brightnessctl set +5%"
    brightness_down_cmd = "brightnessctl set 5%-"
elif shutil.which("ddcutil"):
    brightness_up_cmd = "ddcutil setvcp 10 + 10"
    brightness_down_cmd = "ddcutil setvcp 10 - 10"
else:
    brightness_up_cmd = ""
    brightness_down_cmd = ""

# =============================================================================
# ⚙️ HOOKS
# =============================================================================

@hook.subscribe.startup_once
def autostart() -> None:
    """Inicio de Session"""
    if has_video_wallpapers():
        # video_wallpaper.py regenera el tema al aplicar el video.
        video_wallpaper_random()
    else:
        apply_fallback_wallpaper()
        # Sincroniza pywal/rofi/dmenu con la imagen de respaldo.
        theme_sync("--if-needed", "--reload")

    execute_daemon_lock_screen()
    start_clipboard_history()
    start_notification_daemon()

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
    Key([mod], "d", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/dmenu-run-themed")), desc="Lanzador dmenu"),
    Key([mod, "control"], "y", lazy.spawn(f"{sys.executable} {os.path.expanduser(script_theme_sync)} --refresh --reload"), desc="Regenerar tema desde el wallpaper"),
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
        Key([], "c", clipmenu, desc="Portapapeles"),
    ]),
    KeyChord([mod], "a", [
        Key([], "w", lazy.spawn("zen-browser"), desc="Zen Browser"),
        Key([], "p", lazy.spawn("bitwarden"), desc="Bitwarden"),
        Key([], "c", lazy.spawn("gcolor3"), desc="Selector de color"),
    ]),
    KeyChord([mod], "m", [
        Key([], "space", launcher, desc="Lanzador"),
        Key([], "h", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/show-hotkeys.sh")), desc="Guía de atajos"),
        # ✅ Integración con Swappy para editar antes de guardar/copiar
        Key([], "s", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/screenshot-area.sh")), desc="Capturar y editar área"),
        Key([], "p", lazy.spawn(os.path.expanduser("~/.config/qtile/scripts/screenshot-full.sh")), desc="Capturar y editar pantalla completa"),
        Key([], "c", calendar, desc="Calendario"),
        Key([], "t", timer, desc="Temporizador"),
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
    Key([mod], "o", lazy.spawn("pavucontrol"), desc="Audio avanzado"),
]

# --- Brillo de pantalla (solo si el equipo tiene comando válido) ---
# En escritorio sin ddcutil instalado estas teclas simplemente no se registran.
if brightness_up_cmd:
    keys.append(Key([], "XF86MonBrightnessUp", lazy.spawn(brightness_up_cmd), desc="Brillo +"))
if brightness_down_cmd:
    keys.append(Key([], "XF86MonBrightnessDown", lazy.spawn(brightness_down_cmd), desc="Brillo -"))

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
        border_normal=ColorH,
        border_width=2,
        ratio=0.6,
    ),
    layout.Bsp(
        margin=8,
        border_focus=ColorE,
        border_normal=ColorH,
        border_width=2,
    ),
    layout.Max(),
]

widget_defaults = dict(
    font="JetBrainsMono Nerd Font",
    fontsize=11,
    padding=6,
    foreground=ColorG,
)
extension_defaults = widget_defaults.copy()

def build_bottom_widgets() -> list:
    """Widgets de la barra inferior (instancias nuevas por pantalla)."""
    widgets = [
        widget.TextBox(text="⚡", foreground=ColorE, mouse_callbacks={"Button1": launcher}),
        widget.Sep(linewidth=1, padding=8, foreground=ColorBorder),
        widget.WindowName(
            font="JetBrainsMono Nerd Font Bold",
            foreground=ColorG,
            max_chars=70,
        ),
        widget.GenPollText(
            func=lambda: subprocess.getoutput("playerctl metadata --format '🎵{{ artist }} - {{ title }}🎵' 2>/dev/null || echo '⏹'"),
            update_interval=5,
            foreground=ColorF,
            max_chars=50,
        ),
        widget.Sep(linewidth=1, padding=8, foreground=ColorBorder),
        widget.CPU(format="CPU {load_percent:2.0f}%", foreground=ColorD, mouse_callbacks={"Button1": htop}),
        widget.Memory(format="MEM {MemUsed:.0f}{mm}", foreground=ColorD, mouse_callbacks={"Button1": htop}),
    ]

    # StatusNotifier necesita python-dbus-fast. Si no está instalado se omite
    # para que Qtile no registre errores al iniciar.
    if HAS_DBUS_FAST:
        widgets.append(widget.StatusNotifier())

    widgets.extend([
        widget.Spacer(),
        widget.Sep(linewidth=1, padding=8, foreground=ColorBorder),
        widget.CurrentLayout(foreground=ColorH),
        widget.TextBox(text="☰", foreground=ColorE, mouse_callbacks={"Button1": metamenu}),
    ])
    return widgets

def build_top_widgets() -> list:
    """Widgets de la barra superior (instancias nuevas por pantalla)."""
    widgets = [
        widget.GroupBox(
            highlight_method="line",
            line_width=2,
            borderwidth=2,
            urgent_border=ColorA,
            urgent_text=ColorA,
            active=ColorG,
            inactive=ColorH,
            this_current_screen_border=ColorE,
            this_screen_border=ColorH,
            other_current_screen_border=ColorF,
            other_screen_border=ColorBorder,
            padding_x=8,
            padding_y=4,
            margin_x=2,
            disable_drag=True,
        ),
        widget.Sep(linewidth=1, padding=8, foreground=ColorBorder),
        widget.Spacer(),
        widget.Clock(
            format="%a %b %d",
            font="JetBrainsMono Nerd Font Bold",
            foreground=ColorH,
            mouse_callbacks={"Button1": calendar}
        ),
        widget.Sep(linewidth=1, padding=8, foreground=ColorBorder),
        widget.Clock(
            format="%I:%M %p",
            font="JetBrainsMono Nerd Font Bold",
            foreground=ColorG,
            mouse_callbacks={"Button1": timer}
        ),
        widget.Spacer(),
        widget.TextBox(text="🔊", foreground=ColorE, mouse_callbacks={"Button1": sound}),
        widget.Volume(
            foreground=ColorG,
            get_volume_command="wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null | awk '{printf \"%d%%\", $2*100}'",
            check_mute_command="wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null",
            check_mute_string="MUTED",
            volume_up_command="wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%+",
            volume_down_command="wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-",
            mute_command="wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle",
            volume_app="pavucontrol",
        ),
        widget.Sep(linewidth=1, padding=8, foreground=ColorBorder),
    ]

    # El widget de batería solo tiene sentido en un portátil.
    if IS_LAPTOP:
        widgets.append(widget.Battery(
            format="{char} {percent:2.0%}",
            charge_char="⚡",
            discharge_char="🔋",
            full_char="🔋",
            empty_char="🪫",
            not_charging_char="🔌",
            unknown_char="?",
            low_percentage=0.20,
            low_foreground=ColorI,
            charging_foreground=ColorB,
            foreground=ColorG,
            show_short_text=False,
            update_interval=30,
            mouse_callbacks={"Button1": powermenu},
        ))

    widgets.append(
        widget.TextBox(text="⏻", foreground=ColorE, mouse_callbacks={"Button1": powermenu})
    )
    return widgets

def build_screen() -> Screen:
    """Crea una pantalla con sus barras (se reutiliza para multimonitor)."""
    return Screen(
        top=bar.Bar(
            build_top_widgets(),
            size=26,
            background=ColorZ,
            opacity=0.94,
            margin=[6, 6, 0, 6],
            border_width=1,
            border_color=ColorBorder,
        ),
        bottom=bar.Bar(
            build_bottom_widgets(),
            size=24,
            background=ColorZ,
            opacity=0.94,
            margin=[0, 6, 6, 6],
            border_width=1,
            border_color=ColorBorder,
        ),
        # Gaps alrededor de la pantalla
        left=bar.Gap(8),
        right=bar.Gap(8),
    )

# En escritorio se declaran varias pantallas para multimonitor; los monitores
# sobrantes se asignan/desasignan solos gracias a reconfigure_screens = True.
num_screens = 1 if IS_LAPTOP else DESKTOP_MONITORS
screens = [build_screen() for _ in range(num_screens)]

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
    border_normal=ColorH,
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
# En escritorio, True permite reaccionar al conectar/desconectar monitores.
reconfigure_screens = not IS_LAPTOP
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
