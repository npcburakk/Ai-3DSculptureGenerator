"""
Kullanıcı API Key Config

Kullanıcının kendi Meshy/OpenAI API key'lerini proje dizini dışında,
kullanıcının ana dizininde (~/.text3d/config.json) saklar. Böylece proje
klasörü silinse/güncellense bile key'ler kaybolmaz.

Bu dosyanın içeriği (key değerleri dahil) hiçbir koşulda loglanmaz.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

USER_CONFIG_DIR = Path.home() / ".text3d"
USER_CONFIG_PATH = USER_CONFIG_DIR / "config.json"


def load_user_config() -> dict:
    """~/.text3d/config.json içeriğini okur. Yoksa/bozuksa boş dict döner."""
    if not USER_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(USER_CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        logger.warning("Kullanıcı config dosyası okunamadı, yok sayılıyor: %s", USER_CONFIG_PATH)
        return {}


def save_user_api_keys(
    meshy_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
) -> None:
    """
    Verilen key'leri ~/.text3d/config.json'a yazar (mevcut diğer alanları
    korur). None geçilen alan değiştirilmez; boş string "" geçilirse key
    silinmiş sayılır.
    """
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = load_user_config()
    if meshy_api_key is not None:
        data["meshy_api_key"] = meshy_api_key
    if openai_api_key is not None:
        data["openai_api_key"] = openai_api_key
    USER_CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(USER_CONFIG_PATH, 0o600)  # sadece sahibi okuyup yazabilsin
    except OSError:
        pass
