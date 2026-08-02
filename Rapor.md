# Text-to-3D Generator — Teknik Rapor

**Tarih:** 2026-08-02
**Revizyon aralığı:** `413fa20` → (bu commit dahil)
**Branch:** `main` (origin/main ile senkron)

---

## 1. Yönetici Özeti

Uygulama işlevsel ve bu oturumda masaüstü paketlemesi (macOS + Windows) tamamlandı; canlı testte bulunan iki gerçek çalışma-zamanı hatası düzeltildi. Kod tabanı incelemesi ayrıca yetkilendirme ve konfigürasyon katmanında, prod'a çıkmadan önce kapatılması gereken birkaç ciddi açık ortaya çıkardı.

| Metrik | Değer |
|---|---|
| Bu oturumdaki commit | 5 |
| Bulunup düzeltilen bug | 2 |
| Kritik güvenlik bulgusu | 2 |
| Otomatik test | 0 |

---

## 2. Sistem Mimarisi

Tek FastAPI süreci hem API'yi hem statik frontend'i aynı porttan servis eder; ayrı bir frontend sunucusu yoktur. Masaüstünde bu süreç `launcher.py` tarafından arka planda başlatılıp bir pywebview penceresinde gösterilir.

```
İstemci (tarayıcı / pywebview)
        │
        ▼
FastAPI :8000+  ── /api/v1 (API)  +  frontend/ (statik mount)
        │
        ├──► SQLite (users, jobs)
        │
        └──► pipeline_service ── BackgroundTasks, aynı event loop'ta
                    │
                    ▼
             Meshy API — 5sn aralıkla, 120 tekrara kadar polling (600sn tavan)
                    │
                    ▼
             outputs/*.obj|.glb|.stl  →  /download, /download-all (zip)
```

### Ortam ayrımı (`app/core/paths.py`)

Paketlenmiş halde (`is_frozen()`) veritabanı, çıktılar ve yüklemeler proje klasörü yerine kullanıcının OS'e özgü veri dizinine yazılır — `.app`/`.exe` güncellenirken veri kaybolmasın diye:

| Platform | Veri dizini |
|---|---|
| macOS | `~/Library/Application Support/Text3D` |
| Windows | `%LOCALAPPDATA%\Text3D` |
| Linux | `~/.local/share/Text3D` |

Sonuç olarak her ortam (dev, paketli-mac, paketli-win) kendi izole veritabanını kullanır — bir ortamda oluşturulan kullanıcı/job diğerinde görünmez. Bu oturumda "admin ile giriş yapamıyorum" şikâyeti bu izolasyondan kaynaklanıyordu; bug değil, tasarım gereği.

---

## 3. Veri Modeli

SQLAlchemy ORM, SQLite üzerinde. Alembic yok — şema değişiklikleri `base.py` içinde elle yazılmış `ALTER TABLE` ifadeleriyle uygulanıyor.

**`users`**
- `id` — PK, UUID string
- `username`, `email` — unique + index
- `hashed_password` — bcrypt
- `is_active` — default true
- `created_at`, `updated_at` (onupdate)
- İlişki: `users` → `jobs`, `cascade="all, delete-orphan"` (kullanıcı silinirse job'ları da silinir)

**`jobs`**
- `id`, `user_id` (→ `users.id`, FK, **nullable** — anonim job'a izin var)
- `prompt`, `enhanced_prompt`, `style`
- `backend`, `output_format`, `num_steps`, `guidance_scale`, `mesh_resolution`
- `status` (indexli), `progress`, `current_stage`, `is_favorite`
- `output_path`, `output_url`, `error_message`
- `job_metadata` (JSON), `created_at` (indexli), `updated_at`, `completed_at`, `duration_seconds`

---

## 4. API Yüzeyi

Tüm uçlar `/api/v1` altında. Auth modeli beklenenden gevşek — bkz. [Bulgular](#6-bulgular).

| Method | Path | Açıklama | Auth |
|---|---|---|---|
| POST | `/auth/register` | Kayıt | — |
| POST | `/auth/login` | JWT (HS256, 7 gün) döner | — |
| GET | `/auth/me` | Profil | **zorunlu** |
| POST | `/jobs` | Metinden üretim | opsiyonel |
| POST | `/jobs/image` | Fotoğraftan büst | opsiyonel |
| GET | `/jobs`, `/jobs/{id}`, `/jobs/{id}/status` | Listele / detay / ilerleme | opsiyonel |
| PATCH · DELETE | `/jobs/{id}/favorite`, `/jobs/{id}` | Favori · sil | **yok** |
| GET | `/jobs/{id}/download(-all)` | Dosya / zip indir | **yok** |
| POST | `/settings/keys` | Meshy/OpenAI key kaydet | **yok** |
| GET | `/health` | Health check | — |

---

## 5. Bu Oturumdaki Değişiklikler

| Commit | Değişiklik |
|---|---|
| `413fa20` | Frontend varlıklarını (`index.html`, favicon'lar, `static/images`) `frontend/` altına taşı — PyInstaller'ın tek `datas` kökü olarak paketleyebilmesi için. |
| `63c3219` | macOS (`.app`) + Windows (`.exe`) paketleme: `launcher.py`, `app/core/paths.py`, `text3d.spec` / `text3d_windows.spec`, `requirements-desktop.txt`, `.github/workflows/build-windows.yml`. Ağır ML paketleri (torch, shap_e, transformers) bilinçli olarak dışlandı. |
| `1135bf3` | **İki bug düzeltmesi:** (1) `index.html`'deki `API = 'http://localhost:8000/...'` sabit kodlaması, launcher 8000 dolu olduğunda 8001'e düştüğünde paketli app'i yanlış sunucuya bağlıyordu → `window.location.origin` bazlı yapıldı. (2) pywebview'ın `ALLOW_DOWNLOADS` ayarı varsayılan kapalı olduğu için indirme linkleri backend sağlıklı olmasına rağmen sessizce çalışmıyordu → pencere açılmadan önce `True` yapıldı. |
| `e58d769` | README güncel mimariye yeniden yazıldı (eski hali auth'suz, frontend'siz, sadece-GPU bir backend tarif ediyordu). |
| _(bu rapor sonrası)_ | Uygulama ikonu `frontend/static/images/auth-hero.png`'den üretildi. |

---

## 5.1 Uygulama İkonu

`.app`/`.exe` ikonu, önceden tanımsız olan (`icon=None`) varsayılan PyInstaller ikonu yerine, projenin kendi görselinden — `frontend/static/images/auth-hero.png` (1024×1024, alfa kanallı, wireframe büst) — üretildi:

- **macOS:** `sips` ile 16→1024px arası tüm boyutlar (@1x/@2x dahil) üretilip `iconutil` ile `build_assets/AppIcon.icns`'e paketlendi; `text3d.spec`'in `BUNDLE(...)` adımında `icon="build_assets/AppIcon.icns"` olarak bağlandı. Yeniden build edilip `Info.plist`'te `CFBundleIconFile = AppIcon.icns` olarak doğrulandı; Dock'ta görsel olarak da teyit edildi.
- **Windows:** aynı görselden Pillow ile çok boyutlu (16/32/48/64/128/256px) `build_assets/AppIcon.ico` üretildi; `text3d_windows.spec`'te `EXE(...)`'in `icon` parametresi `frontend/favicon.ico`'dan `build_assets/AppIcon.ico`'ya çevrildi. Bu makinede native Windows build alınamadığı için sonuç yalnızca GitHub Actions'taki (`build-windows.yml`) sıradaki çalıştırmada doğrulanabilir.

`build_assets/AppIcon.icns` ve `build_assets/AppIcon.ico` iki spec dosyasının da girdisi olduğu için repoya commit edildi (build çıktısı değil, kaynak varlık).

---

## 6. Bulgular

Kod incelemesinden çıkan, henüz düzeltilmemiş açık noktalar — önem sırasına göre.

### 🔴 Kritik

**Job uçlarında sahiplik kontrolü yok** — `app/api/routes.py:153–202`
UUID'sini bilen herhangi biri — kendi hesabı olsun olmasın — başka bir kullanıcının job'ını silebilir, favoriye alabilir, indirebilir. `favorite`, `DELETE /jobs/{id}`, `/download`, `/download-all` hiçbir auth dependency'si almıyor.

**`/settings/keys` tamamen açık ve paylaşılan tek dosyaya yazıyor** — `app/api/routes.py:226`, `app/core/user_config.py`
Auth gerekmiyor; kullanıcı bazlı değil, `~/.text3d/config.json` adında tek/süreç-genelinde bir dosyaya yazıyor. Yetkisiz herhangi bir çağıran, tüm kullanıcılar için sunucunun Meshy/OpenAI key'lerini değiştirebilir.

### 🟠 Yüksek

**`SECRET_KEY` varsayılanı sahte bir placeholder** — `app/core/config.py:50`
`.env`'de override edilmezse JWT imzalama anahtarı repo'da açıkça görünen sabit bir string — token'lar tahmin edilebilir/sahtelenebilir.

**`CORS_ORIGINS = ["*"]`** — `app/core/config.py:27`
Herhangi bir origin'den istek kabul ediliyor; auth token'ları JWT (cookie değil) olduğu için CSRF riski düşük ama kimlik doğrulamalı bir API için gereksiz geniş.

### 🔵 Orta

**`MAX_CONCURRENT_JOBS` tanımlı ama hiç kullanılmıyor** — `app/core/config.py:59`
Job'lar `BackgroundTasks.add_task` ile aynı event loop'ta, herhangi bir kuyruk/limit olmadan çalıştırılıyor — ayar sadece süs, gerçek bir eşzamanlılık tavanı yok.

**Tüm bağımlılıklar sürüm pin'i olmadan** — `requirements.txt`, `requirements-desktop.txt`
fastapi, sqlalchemy, python-jose, pyinstaller dahil hiçbir pakette `==` yok. Bugün alınan bir build ile altı ay sonra alınan build farklı (kırık veya güvenlik açığı olan) sürümler çekebilir.

**Otomatik test yok** — `tests/` dizini mevcut değil
`pytest`/`pytest-asyncio` bağımlılık olarak listeli ama hiçbir `test_*.py` dosyası yok — hiçbir şey çalıştırılmıyor.

### ⚪ Bilgi

- Şifre politikası minimal: sadece `min_length=6`, karmaşıklık kuralı yok. Login/register/job-create uçlarında rate limit yok.
- Masaüstü uygulaması tam offline çalışmıyor: 3D viewer (Three.js) CDN'den yükleniyor.
- macOS `.app` ad-hoc imzalı, notarization yok — sadece yerel test için yeterli.

---

## 7. Öncelik Sırasına Göre Öneriler

1. **Job uçlarına sahiplik kontrolü ekle** — her job mutasyon/indirme uç noktasına `require_current_user` + `job.user_id == current_user.id` kontrolü. Bu ikisi olmadan sistem paylaşımlı bir dosya sunucusu gibi davranıyor.
2. **`/settings/keys`'i kullanıcı bazlı ve auth'lu yap** — tek paylaşılan config dosyası yerine key'leri `users` tablosuna (şifrelenmiş) bağla; uç noktayı `require_current_user` arkasına al.
3. **`SECRET_KEY`'i zorunlu kıl** — placeholder varsayılan yerine, `.env`'de tanımlı değilse uygulama başlangıçta patlasın (fail-fast).
4. **`CORS`'u daraltıp bağımlılıkları pin'le** — `CORS_ORIGINS`'ı bilinen origin'lere indir; `requirements*.txt`'e en azından majör sürüm sınırı (`~=`) ekle.
5. **Kritik akışlar için minimum test seti** — auth (kayıt/giriş/yetkisiz erişim) ve job sahiplik kontrolü için birkaç `pytest` testi.
