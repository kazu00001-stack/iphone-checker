@echo off
setlocal
cd /d "%~dp0"

echo === Python バージョン確認 ===
where python >nul 2>&1
if errorlevel 1 (
  echo Python が見つかりません。https://www.python.org/downloads/ からインストールしてください。
  exit /b 1
)
python --version

echo === 仮想環境を作成 (.venv) ===
if not exist ".venv" (
  python -m venv .venv
)

call .venv\Scripts\activate.bat

echo === pip を更新 ===
python -m pip install --upgrade pip >nul

echo === 依存パッケージをインストール ===
pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo === Playwright 用 Chromium をインストール（初回のみ約150MB） ===
python -m playwright install chromium
if errorlevel 1 exit /b 1

if not exist ".env" (
  copy /Y .env.example .env >nul
  echo === .env を .env.example から作成しました ===
)

echo.
echo === セットアップ完了 ===
echo    起動: start.bat   または  python app.py
endlocal
