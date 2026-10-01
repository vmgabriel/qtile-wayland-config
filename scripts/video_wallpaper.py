#!/usr/bin/env python3
"""
Gestor de Video Wallpapers para Qtile Wayland
Autor: vmgabriel
Entorno: Arch Linux + Qtile Wayland + mpvpaper
"""

from typing import Optional
import os
import random
import subprocess
import sys
from pathlib import Path


class VideoWallpaperManager:
    def __init__(self, video_dir: str = "~/Vídeos/wallpapers"):
        self.video_dir = Path(video_dir).expanduser()
        self.current_wp_file = Path("~/.config/qtile/current_video_wallpaper").expanduser()
        
        # Crear directorio si no existe
        self.video_dir.mkdir(parents=True, exist_ok=True)
        self.current_wp_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_videos(self, category: Optional[str] = None) -> list[Path]:
        """Obtiene lista de videos disponibles, opcionalmente por categoría"""
        search_dir = self.video_dir / category if category else self.video_dir
        
        if not search_dir.exists():
            return []
        
        extensions = ["*.mp4", "*.webm", "*.mkv", "*.avi"]
        videos = []
        for ext in extensions:
            videos.extend(search_dir.glob(ext))
        
        return sorted(videos)
    
    def get_random_video(self, category: Optional[str] = None) -> Optional[Path]:
        """Selecciona un video aleatorio"""
        videos = self.get_videos(category)
        if not videos:
            return None
        return random.choice(videos)
    
    def get_next_video(self, category: Optional[str] = None) -> Optional[Path]:
        """Obtiene el siguiente video en la lista (secuencial)"""
        videos = self.get_videos(category)
        if not videos:
            return None
        
        # Leer video actual
        current = None
        if self.current_wp_file.exists():
            current = Path(self.current_wp_file.read_text().strip())
        
        # Encontrar el siguiente
        if current and current in videos:
            index = videos.index(current)
            next_index = (index + 1) % len(videos)
            return videos[next_index]
        
        return videos[0]
    
    def kill_existing(self):
        """Mata instancias existentes de mpvpaper"""
        subprocess.run(
            ["pkill", "-f", "mpvpaper"],
            capture_output=True
        )
    
    def apply(self, video: Path, options: str = "no-audio loop hwdec=vaapi"):
        """Aplica el video como wallpaper"""
        self.kill_existing()
        
        # Comando optimizado para AMD con vaapi
        cmd = [
            "mpvpaper",
            "-o", options,
            "*",  # Aplica a todos los monitores
            str(video)
        ]
        
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Guardar video actual
        self.current_wp_file.write_text(str(video))
        
        return video.name
    
    def stop(self):
        """Detiene el video wallpaper"""
        self.kill_existing()
        if self.current_wp_file.exists():
            self.current_wp_file.unlink()
        print("✅ Video wallpaper detenido")
    
    def get_current(self) -> Optional[str]:
        """Obtiene el nombre del video actual"""
        if self.current_wp_file.exists():
            video_path = Path(self.current_wp_file.read_text().strip())
            return video_path.name
        return None

def main():
    manager = VideoWallpaperManager()
    
    # Parsear argumentos
    if len(sys.argv) < 2:
        print("Uso: video_wallpaper.py [comando] [categoria]")
        print("\nComandos:")
        print("  random [categoria]  - Video aleatorio")
        print("  next [categoria]    - Siguiente video")
        print("  stop                - Detener video")
        print("  current             - Mostrar video actual")
        print("  list [categoria]    - Listar videos")
        sys.exit(1)
    
    command = sys.argv[1]
    category = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        if command == "random":
            video = manager.get_random_video(category)
            if video:
                name = manager.apply(video)
                print(f"✅ Video aleatorio: {name}")
            else:
                print("❌ No se encontraron videos")
                sys.exit(1)
        
        elif command == "next":
            video = manager.get_next_video(category)
            if video:
                name = manager.apply(video)
                print(f"✅ Siguiente video: {name}")
            else:
                print("❌ No se encontraron videos")
                sys.exit(1)
        
        elif command == "stop":
            manager.stop()
        
        elif command == "current":
            current = manager.get_current()
            if current:
                print(f"📹 Video actual: {current}")
            else:
                print("⚠️  No hay video wallpaper activo")
        
        elif command == "list":
            videos = manager.get_videos(category)
            if videos:
                print(f"📁 Videos disponibles ({len(videos)}):")
                for i, video in enumerate(videos, 1):
                    print(f"  {i}. {video.name}")
            else:
                print("❌ No se encontraron videos")
        
        else:
            print(f"❌ Comando desconocido: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
