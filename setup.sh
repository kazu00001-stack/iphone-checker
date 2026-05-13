#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "▶ Python バージョン確認"
PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" --version

echo "▶ 仮想環境を作成 (.venv)"
if [ ! -d ".venv" ]; then
  "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "▶ pip を更新"
python -m pip install --upgrade pip >/dev/null

echo "▶ 依存パッケージをインストール"
pip install -r requirements.txt

echo "▶ Playwright 用 Chromium をインストール（初回のみ約150MB）"
python -m playwright install chromium

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "▶ .env を .env.example から作成しました"
fi

echo ""
echo "✅ セットアップ完了"
echo "   起動: ./start.sh   または  python app.py"
