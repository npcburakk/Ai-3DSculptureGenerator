# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Text to 3D masaüstü uygulaması (macOS .app)

Build:
    pyinstaller text3d.spec

Çıktı: dist/Text to 3D.app

Önemli: torch/shap-e/transformers gibi ağır ML paketleri (bu ortamda
geliştirme amaçlı kurulu olsa bile) bilinçli olarak excludes içinde —
üretim akışı sadece bulut API'leri (Meshy/OpenAI) kullanıyor, bu
paketler yalnızca opsiyonel/yerel Shap-E backend'i için ve build'i
gigabaytlarca büyütüp kırılganlaştırırlardı.
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

app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon="build_assets/AppIcon.icns",
    bundle_identifier="com.text3d.desktop",
    info_plist={
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "LSApplicationCategoryType": "public.app-category.graphics-design",
    },
)
