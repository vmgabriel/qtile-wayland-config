#!/usr/bin/env python3
"""
Sincroniza el tema de Qtile, rofi y dmenu con pywal.

- Extrae un frame del video wallpaper actual (o usa la imagen de respaldo).
- Genera la paleta con `wal` (pywal16).
- Escribe:
    * ~/.config/qtile/theme_palette.json   (lo lee config.py)
    * ~/.config/rofi/theme.rasi            (tema de rofi)
    * ~/.cache/qtile/dmenu_colors.sh       (colores de dmenu)

Uso:
    theme-sync.py                 # renderiza con los colores actuales
    theme-sync.py --refresh       # vuelve a generar desde el wallpaper
    theme-sync.py --if-needed     # genera solo si cambió el wallpaper
    theme-sync.py --refresh --reload   # además recarga Qtile
"""

from __future__ import annotations

import colorsys
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, Optional

HOME = Path.home()
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", HOME / ".cache"))
WAL_DIR = CACHE_DIR / "wal"
STATE_DIR = CACHE_DIR / "qtile"

QTILE_DIR = CONFIG_DIR / "qtile"
ROFI_DIR = CONFIG_DIR / "rofi"
PALETTE_FILE = QTILE_DIR / "theme_palette.json"
ROFI_THEME_FILE = ROFI_DIR / "theme.rasi"
DMENU_COLORS_FILE = STATE_DIR / "dmenu_colors.sh"
FRAME_FILE = STATE_DIR / "wallpaper-frame.png"

WALLPAPER_STATE = QTILE_DIR / "current_video_wallpaper"
FALLBACK_IMAGE = QTILE_DIR / "screens" / "qtilechameleon1.png"

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".avi", ".mov"}

# Paleta de emergencia (Gruvbox) si pywal no está disponible.
FALLBACK_PALETTE = {
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


# =============================================================================
# Utilidades de color
# =============================================================================

def normalize_hex(value: str) -> str:
    """Devuelve un color #rrggbb (ignora alfa tipo pywal '#rrggbbaa')."""
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    value = value[:7].lower()
    if len(value) == 4:  # #abc -> #aabbcc
        value = "#" + "".join(ch * 2 for ch in value[1:])
    if len(value) != 7:
        raise ValueError(f"Color inválido: {value!r}")
    int(value[1:], 16)
    return value


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = normalize_hex(value)
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def rgb_to_hex(rgb: Iterable[float]) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in rgb)


def mix(color_a: str, color_b: str, amount: float) -> str:
    """Mezcla color_a con color_b. amount=0 -> a, amount=1 -> b."""
    amount = max(0.0, min(1.0, amount))
    a, b = hex_to_rgb(color_a), hex_to_rgb(color_b)
    return rgb_to_hex(a[i] + (b[i] - a[i]) * amount for i in range(3))


def relative_luminance(color: str) -> float:
    def channel(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = hex_to_rgb(color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(color_a: str, color_b: str) -> float:
    a = relative_luminance(color_a)
    b = relative_luminance(color_b)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def ensure_contrast(color: str, background: str, ratio: float) -> str:
    """Aclara u oscurece `color` hasta alcanzar el contraste pedido."""
    if contrast(color, background) >= ratio:
        return color
    target = "#ffffff" if relative_luminance(background) < 0.5 else "#000000"
    for step in range(1, 101):
        candidate = mix(color, target, step / 100)
        if contrast(candidate, background) >= ratio:
            return candidate
    return target


def hsv(color: str) -> tuple[float, float, float]:
    r, g, b = (c / 255.0 for c in hex_to_rgb(color))
    return colorsys.rgb_to_hsv(r, g, b)


def hue_distance(hue_a: float, hue_b: float) -> float:
    delta = abs(hue_a - hue_b) % 1.0
    return min(delta, 1.0 - delta)


def vividness(color: str, background: str) -> float:
    """Puntúa un color para elegirlo como acento."""
    if contrast(color, background) < 2.2:
        return -1.0
    _, saturation, value = hsv(color)
    # Preferimos colores saturados, ni casi negros ni casi blancos.
    return saturation * 0.75 + (1.0 - abs(value - 0.6)) * 0.25


def best_accents(palette: list[str], background: str, count: int = 2) -> list[str]:
    candidates = sorted(
        {c for c in palette if c},
        key=lambda c: vividness(c, background),
        reverse=True,
    )
    chosen: list[str] = []
    for candidate in candidates:
        if vividness(candidate, background) < 0:
            continue
        if any(hue_distance(hsv(candidate)[0], hsv(other)[0]) < 0.08 for other in chosen):
            continue
        chosen.append(ensure_contrast(candidate, background, 3.0))
        if len(chosen) == count:
            break
    while len(chosen) < count:
        fallback = FALLBACK_PALETTE["accent" if not chosen else "accent2"]
        chosen.append(ensure_contrast(fallback, background, 3.0))
    return chosen


def semantic_color(
    palette: list[str],
    background: str,
    target_hue: float,
    fallback: str,
    min_saturation: float = 0.22,
    ratio: float = 3.0,
) -> str:
    """Busca el color más cercano al tono pedido; si no hay, usa el fallback."""
    best: Optional[str] = None
    best_distance = 1.0
    for color in palette:
        try:
            h, s, _ = hsv(color)
        except ValueError:
            continue
        if s < min_saturation:
            continue
        distance = hue_distance(h, target_hue)
        if distance < best_distance and contrast(color, background) >= 2.0:
            best, best_distance = color, distance
    color = best if best is not None and best_distance <= 0.06 else fallback
    return ensure_contrast(color, background, ratio)


def build_palette(
    colors_data: dict,
    image: Optional[Path],
    source: Optional[Path] = None,
) -> dict:
    raw = colors_data.get("colors", {})
    special = colors_data.get("special", {})

    palette_16 = [normalize_hex(raw.get(f"color{i}", FALLBACK_PALETTE["background"])) for i in range(16)]
    background = normalize_hex(special.get("background") or palette_16[0])
    foreground = normalize_hex(special.get("foreground") or palette_16[7])

    foreground = ensure_contrast(foreground, background, 7.0)
    muted = ensure_contrast(mix(foreground, background, 0.45), background, 3.0)
    accent_candidates = palette_16[1:7] + palette_16[9:16]
    accent, accent2 = best_accents(accent_candidates, background)

    surface = mix(background, foreground, 0.055)
    surface_alt = mix(background, foreground, 0.11)
    border = mix(background, accent, 0.45)

    urgent = semantic_color(accent_candidates, background, 0.0, FALLBACK_PALETTE["urgent"])
    success = semantic_color(accent_candidates, background, 0.33, FALLBACK_PALETTE["success"])
    warning = semantic_color(accent_candidates, background, 0.12, FALLBACK_PALETTE["warning"])
    info = semantic_color(accent_candidates, background, 0.55, FALLBACK_PALETTE["info"])

    # Texto sobre el acento (para la fila seleccionada de rofi/dmenu).
    on_accent = "#000000" if relative_luminance(accent) > 0.45 else "#ffffff"
    on_accent = ensure_contrast(on_accent, accent, 4.5)

    return {
        "background": background,
        "surface": surface,
        "surface_alt": surface_alt,
        "foreground": foreground,
        "muted": muted,
        "border": border,
        "accent": accent,
        "accent2": accent2,
        "on_accent": on_accent,
        "urgent": urgent,
        "success": success,
        "warning": warning,
        "info": info,
        "palette": palette_16,
        "wallpaper": str(source or image) if (source or image) else "",
        "image": str(image) if image else "",
        "wallpaper_mtime": (source or image).stat().st_mtime if (source or image) and (source or image).exists() else 0,
        "colors_mtime": (WAL_DIR / "colors.json").stat().st_mtime if (WAL_DIR / "colors.json").exists() else 0,
        "generated_at": int(time.time()),
    }


# =============================================================================
# Generación con pywal
# =============================================================================

def current_wallpaper() -> Optional[Path]:
    if WALLPAPER_STATE.exists():
        try:
            candidate = Path(WALLPAPER_STATE.read_text().strip()).expanduser()
            if candidate.exists():
                return candidate
        except OSError:
            pass
    if FALLBACK_IMAGE.exists():
        return FALLBACK_IMAGE
    return None


def extract_frame(video: Path) -> Optional[Path]:
    if not shutil.which("ffmpeg"):
        return None
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    for position in ("5", "2", "0"):
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-ss", position, "-i", str(video),
                    "-frames:v", "1", "-vf", "scale=640:-1",
                    str(FRAME_FILE),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if FRAME_FILE.exists() and FRAME_FILE.stat().st_size > 0:
            return FRAME_FILE
    return None


def find_wal() -> Optional[str]:
    return shutil.which("wal") or next(
        (str(p) for p in (HOME / ".local/bin/wal", Path("/usr/local/bin/wal")) if p.exists()),
        None,
    )


def run_pywal(image: Path) -> bool:
    wal = find_wal()
    if not wal:
        return False

    colors_json = WAL_DIR / "colors.json"

    # ColorThief no necesita ImageMagick; el backend `wal` sí.
    for backend in ("colorthief", "modern_colorthief", "fast_colorthief", "wal"):
        previous = colors_json.stat().st_mtime_ns if colors_json.exists() else None
        try:
            result = subprocess.run(
                [wal, "-i", str(image), "-n", "-q", "--backend", backend],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        current = colors_json.stat().st_mtime_ns if colors_json.exists() else None
        if result.returncode == 0 and current is not None and current != previous:
            return True

    # Un colors.json antiguo no debe hacer pasar una ejecución fallida por éxito.
    return False


def needs_refresh(palette: dict) -> bool:
    wallpaper = current_wallpaper()
    if wallpaper is None:
        return False
    if not palette or not palette.get("wallpaper"):
        return True
    if Path(palette.get("wallpaper", "")).expanduser() != wallpaper:
        return True
    if int(palette.get("wallpaper_mtime", 0)) != int(wallpaper.stat().st_mtime):
        return True
    colors_json = WAL_DIR / "colors.json"
    if colors_json.exists():
        return abs(colors_json.stat().st_mtime - float(palette.get("colors_mtime", 0))) > 0.5
    return False


# =============================================================================
# Plantillas
# =============================================================================

def rofi_theme(p: dict) -> str:
    return f"""/* Generado por qtile/scripts/theme-sync.py — no editar a mano. */
* {{
    bg:            {p['background']};
    bg-alt:        {p['surface']};
    bg-hover:      {p['surface_alt']};
    fg:            {p['foreground']};
    fg-muted:      {p['muted']};
    accent:        {p['accent']};
    accent-alt:    {p['accent2']};
    on-accent:     {p['on_accent']};
    urgent:        {p['urgent']};
    border:        {p['border']};

    background-color: @bg;
    text-color:       @fg;
    border-color:     @border;
    spacing:          0;
}}

window {{
    width:            42%;
    background-color: @bg;
    border:           2px;
    border-color:     @border;
    border-radius:    12px;
    padding:          12px;
}}

mainbox {{
    background-color: transparent;
    children:         [ inputbar, listview ];
    spacing:          10px;
    padding:          0;
}}

inputbar {{
    background-color: @bg-alt;
    border-radius:    8px;
    padding:          9px 12px;
    spacing:          8px;
    children:         [ prompt, entry ];
}}

prompt {{
    text-color: @accent;
    font:       "JetBrainsMono Nerd Font Bold 11";
}}

entry {{
    text-color:        @fg;
    placeholder:       "Buscar…";
    placeholder-color: @fg-muted;
}}

listview {{
    background-color: transparent;
    columns:          1;
    lines:            8;
    spacing:          4px;
    scrollbar:        true;
    fixed-height:     false;
    padding:          0;
}}

element {{
    background-color: transparent;
    text-color:       @fg;
    padding:          7px 10px;
    border-radius:    7px;
    spacing:          8px;
}}

element selected.normal {{
    background-color: @accent;
    text-color:       @on-accent;
}}

element urgent.normal {{
    background-color: @urgent;
    text-color:       @on-accent;
}}

element-text {{
    background-color: transparent;
    text-color:       inherit;
}}

element-icon {{
    background-color: transparent;
    size:             1.1em;
}}

scrollbar {{
    background-color: @bg-alt;
    handle-color:     @accent;
    width:            4px;
    border-radius:    2px;
}}
"""


def dmenu_colors(p: dict) -> str:
    return f"""# Generado por qtile/scripts/theme-sync.py — no editar a mano.
DMENU_NB='{p['background']}'
DMENU_NF='{p['foreground']}'
DMENU_SB='{p['accent']}'
DMENU_SF='{p['on_accent']}'
DMENU_FONT='JetBrainsMono Nerd Font:size=11'
DMENU_PROMPT='Ejecutar:'
"""


def write_atomic(path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


# =============================================================================
# Principal
# =============================================================================

def read_palette() -> dict:
    try:
        return json.loads(PALETTE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_colors() -> dict:
    try:
        return json.loads((WAL_DIR / "colors.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def reload_qtile() -> None:
    qtile = shutil.which("qtile")
    if not qtile:
        return
    try:
        subprocess.run(
            [qtile, "cmd-obj", "-o", "cmd", "-f", "reload_config"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


def main() -> int:
    refresh = "--refresh" in sys.argv
    if_needed = "--if-needed" in sys.argv
    reload_config = "--reload" in sys.argv

    wallpaper = current_wallpaper()
    palette = read_palette()
    outputs_missing = any(
        not path.is_file()
        for path in (PALETTE_FILE, ROFI_THEME_FILE, DMENU_COLORS_FILE)
    )

    if if_needed and not outputs_missing and not needs_refresh(palette):
        return 0

    if refresh or (wallpaper and needs_refresh(palette)):
        image = wallpaper
        if image and image.suffix.lower() in VIDEO_EXTENSIONS:
            image = extract_frame(image) or image
        if image and image.exists() and run_pywal(image):
            colors_data = read_colors()
            if colors_data:
                palette = build_palette(colors_data, image, wallpaper)

    if not palette:
        colors_data = read_colors()
        if colors_data:
            palette = build_palette(colors_data, wallpaper, wallpaper)
        else:
            palette = dict(FALLBACK_PALETTE)
            palette.update({"wallpaper": "", "wallpaper_mtime": 0, "generated_at": int(time.time())})

    write_atomic(PALETTE_FILE, json.dumps(palette, indent=2, ensure_ascii=False) + "\n")
    write_atomic(ROFI_THEME_FILE, rofi_theme(palette))
    write_atomic(DMENU_COLORS_FILE, dmenu_colors(palette))

    if reload_config:
        reload_qtile()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
