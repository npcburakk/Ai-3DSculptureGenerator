"""
Kullanıcıya gösterilecek hata mesajlarını üretir.

Teknik hata detayları (stack trace, bağlantı hataları, dış servis
mesajları vb.) kullanıcıya asla ham haliyle gösterilmez; bunun yerine
burada tanımlı genel/anlaşılır mesajlardan biri döndürülür. Teknik
detay, çağıran taraf içinde logger ile (exc_info=True) ayrıca kaydedilir.
"""

import httpx

GENERIC_ERROR = "İşlem şu an tamamlanamadı, lütfen tekrar deneyin."
CONNECTION_ERROR = "Sunucuya bağlanılamadı, lütfen tekrar deneyin."
TIMEOUT_ERROR = "İşlem zaman aşımına uğradı, lütfen tekrar deneyin."
INVALID_INPUT_ERROR = "Girdiğiniz bilgileri kontrol edin."
SERVICE_UNAVAILABLE_ERROR = "Üretim servisi şu anda kullanılamıyor, lütfen daha sonra tekrar deneyin."
MISSING_MESHY_KEY_ERROR = "Lütfen önce Ayarlar'dan Meshy API key'inizi girin."


class MissingApiKeyError(RuntimeError):
    """Gerekli bir API key ayarlanmamışken üretim tetiklendiğinde fırlatılır.

    Mesajı zaten kullanıcıya gösterilmeye uygun, teknik detay içermiyor —
    to_user_message() bu durumda ham mesajı olduğu gibi kullanıcıya döner.
    """


def to_user_message(exc: Exception) -> str:
    """Bir exception'ı kullanıcıya gösterilebilecek sade bir mesaja çevirir."""
    if isinstance(exc, MissingApiKeyError):
        return str(exc)
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, ConnectionError)):
        return CONNECTION_ERROR
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return TIMEOUT_ERROR
    if isinstance(exc, httpx.HTTPStatusError):
        return SERVICE_UNAVAILABLE_ERROR
    if isinstance(exc, (ValueError, KeyError)):
        return INVALID_INPUT_ERROR
    return GENERIC_ERROR
