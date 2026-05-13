# -*- mode: python ; coding: utf-8 -*-
import platform
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

ROOT = Path(SPECPATH).parent

pw_datas, pw_binaries, pw_hidden = collect_all("playwright")

datas = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "static"), "static"),
    (str(ROOT / "config.yaml"), "."),
]

datas += pw_datas

hiddenimports = [
    "playwright",
    "playwright.async_api",
    "playwright.sync_api",
    "playwright._impl._driver",
    *pw_hidden,
]


a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=pw_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="iPhone転売価格チェッカー",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    name="iPhone転売価格チェッカー",
)

if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name="iPhone転売価格チェッカー.app",
        icon=None,
        bundle_identifier="com.masuda.iphone-resale-checker",
        info_plist={
            "CFBundleDisplayName": "iPhone転売価格チェッカー",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
