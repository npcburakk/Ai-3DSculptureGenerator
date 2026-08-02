# 🧊 Text-to-3D Generator

Metin promptundan veya fotoğraftan (büst) 3D model (OBJ / PLY / GLB / STL)
üreten, kullanıcı hesaplı bir uygulama. FastAPI backend, tek sayfalık bir
frontend ve masaüstü paketleme (macOS `.app`, Windows `.exe`) içerir.

Üretim backend'i olarak **Meshy** (bulut API) kullanılır; prompt
iyileştirme için opsiyonel olarak **OpenAI**. Yerel/GPU gerektiren
**Shap-E** ve **Point-E** entegrasyonları da mevcut ama varsayılan
kurulumda devre dışıdır (bkz. [Yerel/GPU Backend'leri](#-yerelgpu-backendleri-opsiyonel)).

---

## 📁 Proje Yapısı

```
.
├── app/
│   ├── main.py                # FastAPI app; API + frontend/ statik mount
│   ├── api/
│   │   └── routes.py          # Tüm API endpoint'leri
│   ├── auth/                  # JWT (python-jose) + bcrypt tabanlı auth
│   │   ├── auth_bearer.py
│   │   ├── auth_handler.py
│   │   └── user_service.py
│   ├── core/
│   │   ├── config.py          # Settings (pydantic-settings + .env)
│   │   ├── paths.py           # Dev / PyInstaller (frozen) yol çözümleme
│   │   └── user_config.py     # ~/.text3d/config.json (kullanıcı API key'leri)
│   ├── database/              # SQLAlchemy models + session (SQLite)
│   ├── schemas/                # Pydantic request/response modelleri
│   ├── services/
│   │   ├── job_service.py     # Job CRUD + arka plan görev çalıştırıcı
│   │   ├── pipeline_service.py# Meshy / Shap-E / Point-E pipeline'ları
│   │   ├── mesh_service.py    # Mesh son işleme (temizleme, decimate, ölçekleme)
│   │   └── status_service.py  # Job durum takibi
│   ├── storage/                # In-memory yardımcı store
│   └── utils/
├── frontend/                   # index.html + static/ (favicon, görseller, videolar)
├── outputs/                    # Üretilen 3D dosyaları (dev modda)
├── uploads/                    # Yüklenen fotoğraflar (dev modda)
├── launcher.py                 # Masaüstü giriş noktası (uvicorn + pywebview)
├── text3d.spec                 # PyInstaller spec — macOS .app
├── text3d_windows.spec         # PyInstaller spec — Windows .exe
├── requirements.txt            # Sunucu/geliştirme bağımlılıkları
├── requirements-desktop.txt    # + masaüstü paketleme için gereken tüm bağımlılıklar
├── .github/workflows/
│   └── build-windows.yml       # windows-latest runner'da otomatik .exe build
├── start.sh / stop.sh           # Backend'i (tek FastAPI süreci) başlat/durdur
└── text3d.db                    # SQLite veritabanı (dev modda proje kökünde)
```

---

## 🚀 Hızlı Başlangıç (geliştirme / web modu)

### 1. Sanal ortam oluştur

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. `.env` yapılandır

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `DEFAULT_BACKEND` | `meshy` | `meshy` \| `shap_e` \| `point_e` |
| `MESHY_API_KEY` | — | Meshy backend'i için gerekli |
| `OPENAI_API_KEY` | — | Prompt iyileştirme için opsiyonel |
| `SECRET_KEY` | — | JWT imzalama anahtarı — production'da mutlaka değiştirin |
| `OUTPUT_DIR` / `UPLOAD_DIR` | `outputs` / `uploads` | Üretilen dosyaların/yüklemelerin konumu |

Kullanıcılar ayrıca kendi Meshy/OpenAI key'lerini uygulama içindeki
**Ayarlar** ekranından da girebilir (`~/.text3d/config.json`'a yazılır ve
`.env`'deki değerlerin üzerine geçer).

### 3. Sunucuyu çalıştır

```bash
./start.sh
# veya
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**http://localhost:8000** hem frontend'i hem `/docs` altında Swagger
UI'ı sunar (API ve arayüz aynı FastAPI sürecinden, aynı porttan servis
edilir — ayrı bir frontend sunucusu yoktur).

---

## 🖥️ Masaüstü Uygulaması (macOS / Windows)

`launcher.py`, uvicorn'u arka plan thread'inde başlatıp bir `pywebview`
penceresi açar (kullanılamazsa varsayılan tarayıcıya düşer). Paketlenmiş
haldeyken (`app/core/paths.py` → `is_frozen()`) veritabanı/outputs/uploads
proje klasörüne değil, kullanıcının OS'e özgü veri dizinine yazılır:

- macOS: `~/Library/Application Support/Text3D`
- Windows: `%LOCALAPPDATA%\Text3D`
- Linux: `~/.local/share/Text3D`

Böylece `.app`/`.exe` güncellenirken veya silinirken kullanıcı verisi
kaybolmaz.

### macOS `.app` build etme

```bash
pip install -r requirements-desktop.txt
pyinstaller text3d.spec
open "dist/Text to 3D.app"
```

### Windows `.exe` build etme

PyInstaller cross-compile yapamadığı için Windows `.exe`'si yalnızca bir
Windows makinede native olarak derlenebilir. Bunun için
`.github/workflows/build-windows.yml`, `main`'e push edildiğinde (veya
`v*` tag'i / manuel tetikleme ile) `windows-latest` runner'ında otomatik
build alır ve sonucu workflow artifact'ı olarak, `v*` tag'lerinde ise
GitHub Release'e ekli olarak sunar. Yerel bir Windows makinede manuel
build için:

```powershell
pip install -r requirements-desktop.txt
pyinstaller text3d_windows.spec
```

Çıktı: `dist/Text to 3D/Text to 3D.exe` (+ yanındaki `_internal/`).

Her iki spec dosyası da ağır ML paketlerini (`torch`, `shap_e`,
`transformers` vb.) bilinçli olarak dışarıda bırakır — üretim akışı
sadece bulut API'lerini (Meshy/OpenAI) kullanır.

---

## 🔌 API Referansı

Tüm endpoint'ler `/api/v1` altında (aksi belirtilmedikçe `Authorization:
Bearer <token>` gerektirir).

### Auth

| Method | Path | Açıklama |
|---|---|---|
| `POST` | `/auth/register` | Yeni kullanıcı kaydı |
| `POST` | `/auth/login` | Giriş, JWT token döner |
| `GET` | `/auth/me` | Giriş yapmış kullanıcının profili |

### Jobs (üretim)

| Method | Path | Açıklama |
|---|---|---|
| `POST` | `/jobs` | Metinden 3D model üretimi başlat |
| `POST` | `/jobs/image` | Fotoğraftan büst üretimi başlat (multipart upload) |
| `GET` | `/jobs` | Job'ları listele (sayfalı) |
| `GET` | `/jobs/{id}` | Job detayı |
| `GET` | `/jobs/{id}/status` | Hafif durum/ilerleme sorgusu |
| `POST` | `/jobs/{id}/retry` | Başarısız job'ı yeniden dene |
| `PATCH` | `/jobs/{id}/favorite` | Favori işaretle/kaldır |
| `DELETE` | `/jobs/{id}` | Job'ı sil |
| `GET` | `/jobs/{id}/download` | Çıktı dosyasını indir |
| `GET` | `/jobs/{id}/download-all` | Tüm çıktı dosyalarını ZIP olarak indir |

### Diğer

| Method | Path | Açıklama |
|---|---|---|
| `POST` | `/prompt/enhance` | OpenAI ile prompt iyileştirme |
| `GET` | `/models` | Kullanılabilir backend'leri listele |
| `GET` | `/stats` | Toplam/istatistik özet |
| `GET` | `/settings/keys` | Kullanıcının kayıtlı API key'lerinin durumu |
| `POST` | `/settings/keys` | Meshy/OpenAI API key'lerini kaydet |
| `GET` | `/health` | Health check (auth gerektirmez, `/api/v1` dışında) |

---

## 🧠 Yerel/GPU Backend'leri (opsiyonel)

Varsayılan `meshy` backend'i bulut API kullanır, GPU gerektirmez. Yerel
üretim için Shap-E/Point-E de desteklenir ama `requirements.txt`'te
yorum satırı olarak bırakılmıştır (paketlenmiş masaüstü uygulamasını
gigabaytlarca büyütüp kırılganlaştırdıkları için):

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install git+https://github.com/openai/shap-e.git   # veya point-e
```

`.env`'de: `DEFAULT_BACKEND=shap_e` (veya `point_e`).

---

## 🧪 Testler

```bash
pytest -v
```

---

## 📝 Notlar

- Veritabanı SQLite (`text3d.db`); geliştirmede proje kökünde, paketlenmiş
  haldeyken kullanıcının veri dizininde.
- Üretilen dosyalar `/outputs/<job_id>.<format>` altında statik servis edilir.
- Eşzamanlı job limiti `.env`'deki `MAX_CONCURRENT_JOBS` ile ayarlanır.
- 3D viewer (Three.js) CDN üzerinden yüklenir — masaüstü uygulaması bu
  yüzden tam offline çalışmaz, internet bağlantısı gerektirir.
