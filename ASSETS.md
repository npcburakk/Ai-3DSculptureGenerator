# Görsel Asset Spec — Text to 3D Frontend

Bu doküman `index.html` içindeki tüm görsel/logo/ikon/arka plan alanlarını
listeler. Şu an bu alanların büyük çoğunluğu emoji (📷 ✨ 👁 🗑 ▸ vb.) veya
düz metin ile dolduruluyor — hiçbir yerde gerçek bir imaj dosyası
kullanılmıyor. Aşağıdaki tablo, her alan için gerçek bir görsel eklenecekse
kullanılması gereken **tam dosya adını, klasör konumunu ve boyutu** tanımlar.

> **Durum notu (güncel):** Wiring tamamlandı — `index.html` artık aşağıdaki
> tüm path'lere referans veriyor, asset'ler `static/images/` altında yerinde.
> Bundan sonra bu tablodaki isim/klasörle birebir eşleşen bir dosyayı
> değiştirip yerine koymak (örn. daha iyi bir `logo-mark.png`) **tek başına
> yeterli**, ekstra kod değişikliği gerekmiyor.
>
> **Format notu:** İlk teslimatta 7 ikon/illüstrasyon `.svg` uzantısıyla
> geldi ama içerik olarak gerçek SVG değil, 1024x1024 PNG raster'dı (AI
> görsel üretim aracının çıktısı); wiring bunları gerçek içeriğe uygun
> şekilde **`.png`** olarak bağladı. Aynı şekilde `generating-loader` ve
> `viewer-loading` `.gif` değil, MP4 video (H.264+AAC) olarak geldi;
> bunlar **`<video autoplay loop muted playsinline>`** ile ve
> `python -m http.server`'ın HTTP Range desteklememesi nedeniyle
> `fetch()` + `blob:` URL üzerinden bağlandı (bkz. `ensureVideoBlobSrc()`
> fonksiyonu, `index.html`). Aşağıdaki tablodaki "Format" sütunları bu
> yüzden orijinal plandan (SVG/GIF) farklı olarak fiilen kullanılan
> formatı (PNG/MP4) yansıtacak şekilde güncellenmiştir.
>
> **Bilinen sınırlama:** Video oynatımı, bu ortamda kullanılan otomatik
> tarayıcı (sandboxed/headless Chrome) hiçbir video codec'ini
> decode edemediği için görsel olarak doğrulanamadı — hem bizim asset'ler
> hem de bilinen çalışan bir public test MP4 aynı şekilde takıldı. Kod
> yapısal olarak doğru (geçerli H.264/AAC MP4, doğru blob wiring, decode
> hatası/timeout'ta zarifçe kayboluyor); normal bir kullanıcı tarayıcısında
> test edip onaylamanız önerilir.

## Genel kurallar

- **Kök klasör:** Frontend `index.html`, proje kök dizininden düz bir HTTP
  sunucusuyla (`start.sh` → `python -m http.server 3000`) serve ediliyor.
  Bu yüzden tüm asset'ler proje köküne göre `/static/images/...` yoluyla
  referans verilecek (backend'in `/outputs` mount'uyla karışmaz).
- **Klasör:** Tüm asset'ler `static/images/` altında toplanır; alt klasör
  ayrımı yok, tek düz klasör (proje küçük olduğu için).
- **Retina/2x:** PNG raster asset'lerde `@2x` varyantı **opsiyonel** —
  isteğe bağlı olarak `logo-mark@2x.png` gibi bırakılabilir, kod `srcset`
  ile otomatik kullanır (wiring adımında eklenecek). SVG kullanılan
  yerlerde 2x'e gerek yok.
- **Dark mode:** Site `prefers-color-scheme: dark` destekliyor
  (bkz. `index.html` satır 18-27). Arka planı transparan olmayan (koyu
  zeminde görünmesi gereken) PNG/SVG asset'ler için tabloda ayrıca not
  düşülmüştür; gerekiyorsa `-dark` sonekli ikinci bir dosya kabul edilir
  (örn. `logo-mark.svg` + `logo-mark-dark.svg`).
- **Dosya adları:** Küçük harf, kebab-case, boşluksuz.

---

## 1. Favicon (tarayıcı sekme ikonu)

| Alan | Değer |
|---|---|
| Ne için | Tarayıcı sekmesinde, yer imlerinde görünen ikon |
| Dosya adı | `favicon.ico` (çok boyutlu: 16, 32, 48 px içerecek şekilde) + `favicon-192.png` (PWA/Android için) |
| Klasör | proje kökü `/favicon.ico`, `static/images/favicon-192.png` |
| Piksel boyutu | `favicon.ico` içinde 16x16, 32x32, 48x48; `favicon-192.png` 192x192 |
| Format | ICO (çok boyutlu) + PNG (şeffaf arka plan) |
| Kullanım bağlamı | `<head>` içinde `<link rel="icon">` |

**Kod referansı (wiring adımında `<head>` içine eklenecek):**
```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/static/images/favicon-192.png" type="image/png">
```

---

## 2. Ana logo (nav bar)

| Alan | Değer |
|---|---|
| Ne için | Üst nav barda "Text to 3D" yazısının solunda görünecek marka ikonu |
| Dosya adı | `logo-mark.svg` |
| Klasör | `static/images/logo-mark.svg` |
| Piksel boyutu | 28x28 (SVG olduğu için ölçeklenir, viewBox 0 0 28 28 önerilir) |
| Format | SVG (tercih edilen — tek renkli, `currentColor` ile dark mode'a otomatik uyar); SVG mümkün değilse `logo-mark.png` 56x56 (şeffaf arka plan, @2x karşılığı) |
| Kullanım bağlamı | Header/nav, sol üstte metnin hemen solunda, 28x28 sabit boyutta |

**Kod referansı** — `index.html` satır 151, `.nav-logo` div'i:
```html
<div class="nav-logo">
  <img src="/static/images/logo-mark.svg" alt="" class="nav-logo-icon">
  Text to 3D
</div>
```
```css
.nav-logo { display:flex; align-items:center; gap:8px; }
.nav-logo-icon { width:28px; height:28px; }
```

---

## 3. Giriş/Kayıt sayfası hero görseli

| Alan | Değer |
|---|---|
| Ne için | `#authPage` ekranında `<h1>Text to 3D</h1>` başlığının üstünde/yanında dekoratif illüstrasyon (soyut 3D obje/bust render'ı gibi) |
| Dosya adı | `auth-hero.svg` |
| Klasör | `static/images/auth-hero.svg` |
| Piksel boyutu | 240x240 (kare, ortalanacak) |
| Format | SVG tercih edilir; PNG kullanılacaksa `auth-hero.png` 480x480 (şeffaf arka plan, @2x) |
| Kullanım bağlamı | `.auth-box` içinde başlığın hemen üstünde, ortalanmış |

**Kod referansı** — `index.html` satır 159-161, `.auth-box` içine:
```html
<div class="auth-box">
  <img src="/static/images/auth-hero.svg" alt="" class="auth-hero" onerror="this.style.display='none'">
  <h1>Text to 3D</h1>
  ...
```
```css
.auth-hero { width:120px; height:120px; display:block; margin:0 auto 1rem; }
```
> `onerror` ile dosya henüz yoksa görsel sessizce gizlenir, layout bozulmaz —
> asset eklenene kadar mevcut görünüm (görselsiz) korunur.

---

## 4. Boş geçmiş durumu illüstrasyonu

| Alan | Değer |
|---|---|
| Ne için | Geçmiş panelinde hiç iş yokken gösterilen "Henüz üretim yok." mesajının üstündeki illüstrasyon |
| Dosya adı | `empty-history.svg` |
| Klasör | `static/images/empty-history.svg` |
| Piksel boyutu | 96x96 |
| Format | SVG (tek renk, `currentColor` / `var(--text3)` uyumlu tercih edilir) |
| Kullanım bağlamı | `.history-empty` div'inin içinde, metnin üstünde |

**Kod referansı** — `index.html` satır 347 ve `renderHistory()` (satır ~675):
```html
<div class="history-empty">
  <img src="/static/images/empty-history.svg" alt="" class="empty-icon" onerror="this.style.display='none'">
  Henüz üretim yok.
</div>
```
```css
.empty-icon { width:48px; height:48px; display:block; margin:0 auto 8px; opacity:.5; }
```

---

## 5. Üretim/yükleniyor animasyon görseli

| Alan | Değer |
|---|---|
| Ne için | `#progressWrap` kartında, aşama listesinin üstünde gösterilecek animasyonlu "işleniyor" görseli (dönen 3D wireframe, spinner vb.) |
| Dosya adı | `generating-loader.gif` (basit çözüm) veya `generating-loader.svg` (CSS/SMIL animasyonlu, tercih edilen — dosya boyutu küçük) |
| Klasör | `static/images/generating-loader.gif` (veya `.svg`) |
| Piksel boyutu | 120x120 |
| Format | Animasyon gerektiği için **GIF** ya da **animasyonlu SVG**; PNG/JPG uygun değil (statik kalır) |
| Kullanım bağlamı | `.stage-label`'ın üstünde, progress kartının başında |

**Kod referansı** — `index.html` satır 315, `.progress-wrap .card` içine:
```html
<div class="card">
  <img src="/static/images/generating-loader.gif" alt="" class="progress-loader" onerror="this.style.display='none'">
  <div class="stage-label">...
```
```css
.progress-loader { width:80px; height:80px; display:block; margin:0 auto 12px; }
```

---

## 6. 3D viewer yükleniyor placeholder'ı

| Alan | Değer |
|---|---|
| Ne için | `#viewerLoading` overlay'inde "Model yükleniyor..." yazısının üstünde gösterilecek yükleniyor animasyonu (model indirilip parse edilirken) |
| Dosya adı | `viewer-loading.gif` |
| Klasör | `static/images/viewer-loading.gif` |
| Piksel boyutu | 64x64 |
| Format | GIF (animasyonlu) — koyu viewer arka planında (`#111`) net görünmesi için açık renk/beyaz tonlarda tasarlanmalı |
| Kullanım bağlamı | `#viewerLoading` içinde, metnin üstünde, viewer'ın koyu arka planı üzerinde |

**Kod referansı** — `index.html` satır 355:
```html
<div id="viewerLoading">
  <img src="/static/images/viewer-loading.gif" alt="" onerror="this.style.display='none'">
  <div>Model yükleniyor...</div>
</div>
```
```css
#viewerLoading { flex-direction:column; gap:10px; }
#viewerLoading img { width:48px; height:48px; }
```

---

## 7. İş tipi ikonları (geçmiş listesi)

| Alan | Değer |
|---|---|
| Ne için | Geçmiş listesinde her satırın solundaki ikon; şu an `📷` (foto→büst) ve `✨` (metin→3D) emojileriyle dolduruluyor, bunların yerine geçecek |
| Dosya adı | `icon-job-text.svg` (metinden üretim), `icon-job-photo.svg` (fotoğraftan büst) |
| Klasör | `static/images/icon-job-text.svg`, `static/images/icon-job-photo.svg` |
| Piksel boyutu | 20x20 |
| Format | SVG, tek renkli (`currentColor` ile dark/light otomatik uyum) |
| Kullanım bağlamı | `.history-icon` kutusunun içinde, 36x36'lık dairesel arka plan üzerinde ortalı |

**Kod referansı** — `index.html` satır 679, `renderHistory()`:
```js
const iconSrc = job.metadata?.job_type === 'image_bust'
  ? '/static/images/icon-job-photo.svg'
  : '/static/images/icon-job-text.svg';
// ...
`<div class="history-icon"><img src="${iconSrc}" alt="" width="20" height="20"
   onerror="this.replaceWith(document.createTextNode('${job.metadata?.job_type === 'image_bust' ? '📷' : '✨'}'))"></div>`
```
> `onerror` fallback'i: dosya henüz yoksa mevcut emoji davranışına geri döner
> — geçiş sırasında hiçbir şey bozulmaz.

---

## 8. Fotoğraf yükleme (dropzone) ikonu

| Alan | Değer |
|---|---|
| Ne için | `#dropzone` boşken (henüz foto sürüklenmemişken) ortada gösterilecek "yükle" ikonu |
| Dosya adı | `icon-upload.svg` |
| Klasör | `static/images/icon-upload.svg` |
| Piksel boyutu | 32x32 |
| Format | SVG, tek renkli |
| Kullanım bağlamı | `.dropzone-text`'in üstünde, ortalanmış |

**Kod referansı** — `index.html` satır 193-196:
```html
<div class="dropzone" id="dropzone">
  <img src="/static/images/icon-upload.svg" alt="" class="dropzone-icon" onerror="this.style.display='none'">
  <div class="dropzone-text">Fotoğrafları buraya sürükleyin veya <span class="dropzone-browse">gözat</span> (1-4 foto)</div>
  ...
```
```css
.dropzone-icon { width:32px; height:32px; display:block; margin:0 auto 8px; opacity:.6; }
```

---

## 9. Model yüklenemedi hata görseli

| Alan | Değer |
|---|---|
| Ne için | 3D viewer'da model indirme/parse başarısız olduğunda (bkz. `openViewer` catch bloğu) gösterilecek hata ikonu |
| Dosya adı | `icon-model-error.svg` |
| Klasör | `static/images/icon-model-error.svg` |
| Piksel boyutu | 40x40 |
| Format | SVG, tek renkli (kırmızımsı ton önerilir, örn. `--danger-text` ile uyumlu) |
| Kullanım bağlamı | `#viewerLoading` içinde, hata mesajının üstünde (sadece hata durumunda, başarılı yüklemede görünmez) |

**Kod referansı** — `index.html`, `openViewer()` catch bloğu (satır ~878):
```js
} catch(e) {
  console.error('[viewer] Model yüklenemedi:', e);
  modelCache.delete(url);
  document.getElementById('viewerLoading').innerHTML =
    `<img src="/static/images/icon-model-error.svg" alt="" width="40" height="40" onerror="this.remove()">
     <div>Model yüklenemedi: ${e && e.message ? e.message : 'bilinmeyen hata'}</div>`;
}
```

---

## 10. Sosyal paylaşım önizleme görseli (OG image)

| Alan | Değer |
|---|---|
| Ne için | Link paylaşıldığında (Slack, WhatsApp, Twitter/X vb.) gösterilecek önizleme kartı görseli |
| Dosya adı | `og-image.png` |
| Klasör | `static/images/og-image.png` |
| Piksel boyutu | 1200x630 (standart OG oranı) |
| Format | PNG veya JPG (şeffaflık gerekmez, arka plan dolu olmalı) |
| Kullanım bağlamı | `<head>` içinde `og:image` / `twitter:image` meta etiketleri |

**Kod referansı** — `index.html` `<head>` içine (şu an hiç OG meta yok):
```html
<meta property="og:title" content="Text to 3D Generator">
<meta property="og:description" content="AI ile metinden 3D model üret.">
<meta property="og:image" content="/static/images/og-image.png">
<meta name="twitter:card" content="summary_large_image">
```

---

## 11. Apple touch icon (iOS ana ekrana ekleme)

| Alan | Değer |
|---|---|
| Ne için | Site iOS'ta "Ana Ekrana Ekle" ile eklendiğinde kullanılacak ikon |
| Dosya adı | `apple-touch-icon.png` |
| Klasör | proje kökü `/apple-touch-icon.png` (iOS bu path'i kök dizinde arar) |
| Piksel boyutu | 180x180 |
| Format | PNG, şeffaf **olmayan** arka plan (iOS şeffaflığı siyaha çevirir) |
| Kullanım bağlamı | `<head>` içinde `<link rel="apple-touch-icon">` |

**Kod referansı:**
```html
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
```

---

## Özet tablo

| # | Element | Dosya adı (fiili) | Klasör | Boyut (fiili) | Format (fiili) | Durum |
|---|---|---|---|---|---|---|
| 1 | Favicon | `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `favicon-192.png` | `/`, `/`, `/`, `static/images/` | 16/32/48, 16x16, 32x32, 192x192 | ICO, PNG | ✅ bağlandı |
| 2 | Nav logo | `logo-mark.png` | `static/images/` | 1024x1024 (24x24 gösterim) | PNG | ✅ bağlandı |
| 3 | Auth hero | `auth-hero.png` | `static/images/` | 1024x1024 (96x96 gösterim) | PNG | ✅ bağlandı |
| 4 | Boş geçmiş | `empty-history.png` | `static/images/` | 1024x1024 (48x48 gösterim) | PNG | ✅ bağlandı |
| 5 | Üretim animasyonu | `generating-loader.mp4` | `static/images/` | ~10sn video | MP4 (H.264+AAC) | ✅ bağlandı, ⚠️ oynatım doğrulanamadı |
| 6 | Viewer yükleniyor | `viewer-loading.mp4` | `static/images/` | ~10sn video | MP4 (H.264+AAC) | ✅ bağlandı, ⚠️ oynatım doğrulanamadı |
| 7 | İş tipi ikonları | `icon-job-text.png`, `icon-job-photo.png` | `static/images/` | 1024x1024 (20x20 gösterim) | PNG | ✅ bağlandı |
| 8 | Dropzone ikonu | `icon-upload.png` | `static/images/` | 1024x1024 (32x32 gösterim) | PNG | ✅ bağlandı |
| 9 | Model hata ikonu | `icon-model-error.png` | `static/images/` | 1024x1024 (40x40 gösterim) | PNG | ✅ bağlandı, tarayıcıda test edildi |
| 10 | OG preview | `og-image.png` | `static/images/` | 1730x909 | PNG | ✅ bağlandı |
| 11 | Apple touch icon | `apple-touch-icon.png` | `/` | 1254x1254 (957 KB) | PNG | ✅ bağlandı, ⚠️ boyut fazla büyük |

## Wiring sonrası notlar / açık işler

1. **Video oynatımı doğrulanamadı.** Bu oturumdaki otomatik tarayıcı hiçbir
   videoyu decode edemiyor (bilinen çalışan bir public test MP4 dahil), bu
   yüzden `generating-loader.mp4` ve `viewer-loading.mp4`'ün gerçekten oynup
   oynamadığı görsel olarak teyit edilemedi. Kod tarafı sağlam (geçerli
   H.264/AAC dosyalar, `fetch`+`blob:` ile Range-desteksiz sunucu sorunu
   aşıldı, decode hatası/6sn timeout'ta öğe zarifçe kayboluyor). Lütfen
   normal Chrome'da `3D Model Üret` butonuna basıp progress kartının
   üstünde animasyon dönüp dönmediğini kontrol edin.
2. **`apple-touch-icon.png` 1254x1254, 957 KB** — spec 180x180 öngörmüştü.
   Fonksiyonel olarak çalışır (iOS otomatik ölçekler) ama her "ana ekrana
   ekle" işleminde gereksiz yere büyük bir dosya indirilir. İsterseniz
   180x180'e küçültülmüş bir sürümünü isteyin, tek satırlık bir değişiklik.
3. **`og-image.png` 1730x909**, spec'teki 1200x630 ile aynı orana yakın
   (1.90 vs 1.905) — sorun teşkil etmez, çoğu platform otomatik kırpar.
4. **PNG ikonlar `currentColor` ile dark/light mode'a otomatik uyum
   sağlamıyor** (raster oldukları için) — `icon-model-error.png` gibi
   renkli üretilen görseller her iki temada da aynı görünecek. Gerçek tek
   renkli SVG'lere geçilirse bu otomatik hale gelir.

Tüm PNG ikon/illüstrasyonlar ve favicon/OG görseli tarayıcıda görsel olarak
doğrulandı (bkz. ekran görüntüleri); model-hata ikonu canlı hata
senaryosuyla test edildi.
