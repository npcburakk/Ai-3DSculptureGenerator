"""
Text-to-3D Generator — Masaüstü Uygulaması Girişi

Bu dosya PyInstaller ile paketlenen .app'in çalıştırdığı giriş noktasıdır
(bkz. text3d.spec). Uvicorn sunucusunu arka planda bir thread'de başlatır,
hazır olmasını bekler, ardından bir pywebview penceresi açar. pywebview
bir sebeple kullanılamazsa varsayılan tarayıcıya düşer.

`python launcher.py` ile geliştirme ortamında da (paketlemeden) çalıştırılabilir.
"""

import logging
import socket
import sys
import threading
import time
import urllib.request
import webbrowser

import uvicorn

HOST = "127.0.0.1"
PREFERRED_PORT = 8000
WINDOW_TITLE = "Text to 3D"


def _find_free_port(preferred: int) -> int:
    """Tercih edilen port doluysa boş bir port bulur (ör. geliştirme
    sunucusu zaten çalışıyorsa .app ile çakışmasın)."""
    for port in (preferred, 8001, 8002, 8010, 0):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((HOST, port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("Uygun bir port bulunamadı")


def _wait_until_ready(url: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.2)
    return False


def main() -> None:
    # Konsol penceresi olmayan paketlenmiş bir uygulamada logging stdout'a
    # değil bir dosyaya gitmeli; aksi halde bazı ortamlarda sessizce çöker.
    from app.core.paths import get_user_data_dir, is_frozen

    if is_frozen():
        log_dir = get_user_data_dir()
        logging.basicConfig(
            filename=str(log_dir / "app.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )

    from app.main import app  # noqa: E402 — logging kurulumundan sonra import edilir

    port = _find_free_port(PREFERRED_PORT)
    url = f"http://{HOST}:{port}"

    config = uvicorn.Config(app, host=HOST, port=port, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    if not _wait_until_ready(f"{url}/health"):
        logging.error("Sunucu %s içinde hazır olmadı", "20 saniye")

    try:
        import webview

        window = webview.create_window(
            WINDOW_TITLE, url, width=1320, height=880, min_size=(960, 640)
        )
        webview.start()
    except Exception as e:
        logging.warning("pywebview kullanılamadı (%s), varsayılan tarayıcı açılıyor.", e)
        webbrowser.open(url)
        # Tarayıcı modunda ana thread canlı kalmalı ki arka plandaki
        # (daemon) sunucu thread'i process ile birlikte ölmesin.
        try:
            server_thread.join()
        except KeyboardInterrupt:
            pass

    server.should_exit = True


if __name__ == "__main__":
    main()
