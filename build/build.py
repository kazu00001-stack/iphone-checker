"""Build the iPhone転売価格チェッカー application using PyInstaller.

Usage:
    python build/build.py [--skip-chromium-download]

Steps:
    1. Download Chromium into ./pw-browsers (if not already present)
    2. Run PyInstaller with build/iphone_checker.spec
    3. Copy ./pw-browsers into the built bundle (so it ships with the app)

Outputs:
    dist/iPhone転売価格チェッカー/        (Windows / Linux folder build)
    dist/iPhone転売価格チェッカー.app/    (macOS .app bundle)
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PW_BROWSERS = ROOT / "pw-browsers"
DIST = ROOT / "dist"
WORK = ROOT / "build_artifacts"
SPEC = ROOT / "build" / "iphone_checker.spec"
BUNDLE_NAME = "iPhone転売価格チェッカー"


def install_chromium() -> None:
    print(f"▶ Chromium をローカルにダウンロード: {PW_BROWSERS}")
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(PW_BROWSERS)
    subprocess.check_call(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env,
    )


def run_pyinstaller() -> None:
    print(f"▶ PyInstaller 実行: {SPEC}")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(SPEC),
            "--clean",
            "--noconfirm",
            f"--distpath={DIST}",
            f"--workpath={WORK}",
        ],
        cwd=str(ROOT),
    )


def embed_chromium() -> None:
    """Copy pw-browsers into the built bundle, keeping only the headless shell
    (the only browser our app uses), to minimize bundle size."""
    if platform.system() == "Darwin":
        target = DIST / f"{BUNDLE_NAME}.app" / "Contents" / "Resources" / "pw-browsers"
    else:
        target = DIST / BUNDLE_NAME / "pw-browsers"

    if target.exists():
        shutil.rmtree(target)

    print(f"▶ Chromium をバンドルに同梱: {target}")
    shutil.copytree(PW_BROWSERS, target, symlinks=True)

    for child in list(target.iterdir()):
        if child.name.startswith("chromium-") and "headless_shell" not in child.name:
            print(f"  ↳ 不要な {child.name} を削除（headless shellのみで動作）")
            shutil.rmtree(child)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-chromium-download",
        action="store_true",
        help="既存の pw-browsers を再利用",
    )
    args = parser.parse_args()

    if PW_BROWSERS.exists() and any(PW_BROWSERS.iterdir()):
        print(f"▶ {PW_BROWSERS} は既に存在（スキップ）")
    else:
        if args.skip_chromium_download:
            print("⚠️ --skip-chromium-download 指定だがブラウザが無い。ダウンロードします")
        install_chromium()

    if DIST.exists():
        shutil.rmtree(DIST)
    if WORK.exists():
        shutil.rmtree(WORK)

    run_pyinstaller()
    embed_chromium()
    print(f"\n✅ ビルド完了 → {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
