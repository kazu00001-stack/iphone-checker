@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv" (
  echo .venv が見つかりません。先に setup.bat を実行してください。
  exit /b 1
)

call .venv\Scripts\activate.bat

echo === サーバ起動: http://127.0.0.1:%FLASK_PORT% (未設定なら 5000) ===
echo    停止: Ctrl + C
python app.py
endlocal
