#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "❌ .venv が見つかりません。先に ./setup.sh を実行してください。"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "▶ サーバ起動: http://127.0.0.1:${FLASK_PORT:-5000}"
echo "  停止: Ctrl + C"
python app.py
