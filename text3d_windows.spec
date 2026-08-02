# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Text to 3D masaüstü uygulaması (Windows .exe)

text3d.spec (macOS .app) ile aynı yaklaşım; farklar sadece platforma özgü
paketleme adımlarında (BUNDLE yok, .app yerine "Text to 3D/" klasörü +
Text to 3D.exe, ikon .ico). Bu dosya native olarak yalnızca Windows
üzerinde derlenebilir (bkz. .github/workflows/build-windows.yml).

Build (Windows):
    pyinstaller text3d_windows.spec

Çıktı: dist/Text to 3D/Text to 3D.exe (+ yanındaki _internal/ klasörü)
"""

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

APP_NAME = "Text to 3D"

# frontend/ altındaki her şeyi (index.html, static/, favicon'lar) olduğu
# gibi paketle — app/main.py bunu çalışma anında get_frontend_dir() ile bulur.
datas = [("frontend", "frontend")]

hiddenimports = (
    [
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "jose",
        "jose.backends",
        "jose.backends.cryptography_backend",
        "bcrypt",
        "sqlalchemy.dialects.sqlite",
        "multipart",
        "email_validator",
        # pywebview'ın Windows arka ucu (Edge WebView2) — collect_submodules
        # ile webview.platforms.* zaten toplanıyor, clr_loader'ın kendisi de
        # gerekiyor çünkü pythonnet üzerinden dinamik yükleniyor.
        "clr_loader",
    ]
    + collect_submodules("trimesh")
    + collect_submodules("openai")
    + collect_submodules("webview")
)

# Ağır/opsiyonel ML yığını — bilinçli olarak dışarıda bırakılıyor (bkz. üst not).
excludes = [
    "torch",
    "torchvision",
    "shap_e",
    "point_e",
    "transformers",
    "clip",
    "matplotlib",
    "scipy",
    "ipywidgets",
    "ipykernel",
    "IPython",
    "jupyter",
    "jupyterlab_widgets",
    "notebook",
    "pytest",
    "pytest_asyncio",
]

a = Analysis(
    ["launcher.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="frontend/favicon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
