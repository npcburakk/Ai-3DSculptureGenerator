"""
Settings Schemas — kullanıcı API key'leri

Key değerleri hiçbir response'ta geri döndürülmez, sadece "ayarlı mı
değil mi" bilgisi (boolean) döner.
"""

from typing import Optional
from pydantic import BaseModel


class ApiKeysUpdateRequest(BaseModel):
    meshy_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None


class ApiKeysStatusResponse(BaseModel):
    meshy_api_key_set: bool
    openai_api_key_set: bool
