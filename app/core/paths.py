"""
Path Resolution — geliştirme ortamı ile PyInstaller paketi arasındaki
dosya konumu farkını soyutlar.

Geliştirmede kaynaklar (frontend/, vb.) proje kökünde bulunur. PyInstaller
ile paketlendiğinde ("frozen") bunlar .app paketinin içine gömülür ve
çalışma anında farklı bir taban dizinden okunur.
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_bundle_dir() -> Path:
    """PyInstaller'ın bundle ettiği kaynakların (datas) kök dizini.

    onefile modda PyInstaller çalışma anında geçici bir dizine açar ve
    yolunu sys._MEIPASS'e yazar; onedir modda (bu projenin kullandığı
    mod) sys._MEIPASS yine bundle'ın kendi dizinini gösterir — ekstra
    açma/kopyalama olmaz.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]


def get_frontend_dir() -> Path:
    """index.html + static/ dosyalarının bulunduğu dizin."""
    return get_bundle_dir() / "frontend"


def get_user_data_dir() -> Path:
    """DB, çıktı dosyaları ve yüklemeler gibi yazılabilir verinin
    tutulduğu dizin. Paketlenmiş halde .app/.exe salt-okunur olabileceği
    (ve güncellemede/silinmede içeriği kaybolacağı) için işletim
    sistemine göre kullanıcının kendi veri dizini kullanılır;
    geliştirmede proje kökü."""
    if not is_frozen():
        return Path(__file__).resolve().parents[2]

    if sys.platform == "darwin":
        d = Path.home() / "Library" / "Application Support" / "Text3D"
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        d = Path(base) / "Text3D"
    else:
        d = Path.home() / ".local" / "share" / "Text3D"

    d.mkdir(parents=True, exist_ok=True)
    return d
