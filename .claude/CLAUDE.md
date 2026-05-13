# iPhone転売 価格・利益・マイル チェッカー

## このツールは何？

Apple Store現行販売モデルの**SIMフリー版iPhone**について、複数の買取サイトから**未使用品**の買取相場を集めて、

- Apple定価との差額（**利益**）
- カード決済で取得できる**マイル数**

を一覧化するローカルWebアプリです。Flask + Playwright + Python で動きます。

---

## 初回セットアップガイド（MANDATORY）

**ユーザーが何か指示を出す前に、必ず以下のチェックと案内を行うこと。**

### ステップ1: ユーザーに事前準備を案内

まず以下のメッセージを表示する：

```
📌 iPhone転売価格チェッカーへようこそ。
   このツールを動かすには、以下の3つが必要です。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【1】Python 3.10以上
  ターミナルで `python3 --version` を実行して 3.10 以上であることを確認
  古い場合: https://www.python.org/downloads/ から最新版をインストール

【2】依存パッケージのインストール（初回のみ・約2分）
  このフォルダで以下のいずれかを実行：
    Mac/Linux:  ./setup.sh
    Windows:    setup.bat

【3】Playwright用のChromium（初回のみ・約150MB）
  setup スクリプトが自動でインストールします

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
セットアップが終わったら「起動して」と言ってください。
```

ユーザーが「OK」「できた」「起動して」等の肯定を返すまで待つ。

### ステップ2: 環境の自動確認

ユーザーの肯定後、以下のチェックを行う：

```bash
# 1. Python版数確認
python3 --version

# 2. venv 作成済みか
ls .venv/bin/activate 2>/dev/null && echo "✅ venv OK" || echo "❌ venv未作成 → setup.sh を実行してください"

# 3. Playwright Chromium インストール済みか
ls ~/.cache/ms-playwright/chromium-*/chrome-* 2>/dev/null | head -1 && echo "✅ Chromium OK" || echo "⚠️ Chromium未インストール → setup.sh 内で自動インストール"
```

未セットアップなら `setup.sh` または `setup.bat` の実行を案内する。

### ステップ3: アプリを起動

セットアップ完了後、以下のいずれかでサーバを起動する：

```bash
# Mac/Linux
./start.sh

# Windows
start.bat
```

起動したら以下を表示：

```
✅ サーバが起動しました。ブラウザで以下を開いてください：

   http://127.0.0.1:5000

最初は空のテーブルです。画面右上の「価格を更新」ボタンを押すと、
全買取サイトをスクレイピングして相場データが入ります（30〜60秒）。
```

---

## 使い方

1. 上記の手順でセットアップ → サーバ起動
2. ブラウザで `http://127.0.0.1:5000` を開く
3. 右上の「価格を更新」を押す（数十秒待つ）
4. 表が表示されたら、上部の「マイル還元率（%）」を変えると取得マイル数が再計算される

## ルール

- ユーザーが「価格を更新」と頼んだら、ブラウザ操作は不要。Webアプリのボタンを使うよう案内する
- スクレイピングが失敗するサイトがあっても、ツール全体は動作する。失敗サイトは「-」表示になる
- Apple定価の取得に失敗した場合は `config.yaml` の `fallback_prices` が使われ、UIで「推定」バッジが付く
- 機種・買取サイトを追加したい要望には `config.yaml` を編集する案内をする

## トラブルシュート

| 症状 | 対処 |
|---|---|
| `python3: command not found` | Python 3.10+ をインストール |
| `ModuleNotFoundError` | `source .venv/bin/activate` してから `pip install -r requirements.txt` |
| `Executable doesn't exist at .../chrome` | `python -m playwright install chromium` を実行 |
| Port 5000 使用中 | `.env` の `FLASK_PORT` を 5050 等に変更 |
| すべてのサイトで「-」表示 | サイト構造の変更可能性。`config.yaml` の URL を確認 |

## 言語

- 日本語優先で応対する
- コード変更時のコメントは必要最低限
