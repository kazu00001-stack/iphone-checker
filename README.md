# iPhone転売 価格・利益・マイル チェッカー

Apple Storeで現行販売中の**SIMフリー版iPhone**について、

- mobile-mix.jp
- k-tai-iosys.com
- 1-chome.com

の3買取サイトから**未使用品**の買取相場を取得し、Apple定価との差額（**利益額**）と取得**マイル数**を一覧表示するローカルWebアプリです。

---

## 🎁 配布物（エンドユーザー向け）

| 種類 | 対象 | URL/ファイル |
|---|---|---|
| **Web版（公開URL）** | だれでも・スマホPC問わず | GitHub Pages（後述で公開手順） |
| Mac版アプリ | オフラインで使いたい人 | `iPhone転売価格チェッカー-mac.zip`（約133MB） |
| Windows版アプリ | 〃 | `iPhone転売価格チェッカー-windows.zip`（CIで生成） |

Web版は **読み取り専用**（誰でも閲覧可、データは1日2回 12時 / 19時 JST に自動更新）。
ローカルアプリ版は ZIP を解凍してダブルクリックするだけ（Python / Chromium のインストール不要）。

---

## 🌐 Webサイトの公開（GitHub Pages）

### 1. GitHubに新規リポジトリ作成

このフォルダの中身を public リポジトリにpushします。
```bash
cd "1000.ツール/iPhone転売価格チェッカー"
git init -b main
git add -A
git commit -m "Initial commit"
git remote add origin https://github.com/<あなたのID>/iphone-checker.git
git push -u origin main
```

### 2. GitHub Pages を有効化

リポジトリページで **Settings → Pages**：
- **Source**: GitHub Actions（Branch ではなく "GitHub Actions" を選択）

### 3. ワークフロー初回実行

リポジトリの **Actions** タブを開く → 「Scrape and publish to Pages」 → **Run workflow**

10〜15分後、`https://<あなたのID>.github.io/iphone-checker/` でアクセス可能になります。

### 4. 自動更新

以後、毎日 12:00 JST と 19:00 JST に GitHub Actions が走り、
最新の買取価格を自動取得・コミット・Pagesに反映します。

> Web版は **読み取り専用** です。閲覧者が「更新」ボタンを押せる仕組みは入れていません（買取サイトに過負荷をかけないため）。

---

> **Windows版アプリのビルド**は本READMEの末尾「Windows版のビルド」を参照。

---

## 開発者向け（このソースフォルダ）

### Mac版を再ビルド

```bash
# 1. 仮想環境作成 + 依存導入
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r build-requirements.txt

# 2. Chromiumをローカルに（初回のみ・約500MB）
PLAYWRIGHT_BROWSERS_PATH="$(pwd)/pw-browsers" python -m playwright install chromium

# 3. ビルド（約2分）
python build/build.py --skip-chromium-download

# 4. 結果: dist/iPhone転売価格チェッカー.app
```

### 配布用ZIPを作成（Mac）
```bash
mkdir -p /tmp/stage/iPhone転売価格チェッカー
cp -R dist/iPhone転売価格チェッカー.app /tmp/stage/iPhone転売価格チェッカー/
cp 配布用-README-Mac.txt /tmp/stage/iPhone転売価格チェッカー/お読みください.txt
cd /tmp/stage && zip -ryq /path/to/output-mac.zip iPhone転売価格チェッカー
```

### 開発時の起動（ビルドせず Pythonで直接）
```bash
source .venv/bin/activate
python app.py   # → http://127.0.0.1:5000
```

---

## ファイル構成

```
iPhone転売価格チェッカー/
├── app.py                  Flaskエントリ（ローカル/.app用）
├── config.yaml             機種マスタ・URL・既定還元率
├── requirements.txt        ランタイム依存
├── build-requirements.txt  ビルド依存 (pyinstaller)
├── build/                  PyInstaller設定とビルドスクリプト
├── docs/                   ★ GitHub Pages 公開用（静的サイト）
│   ├── index.html
│   ├── app.js              data.json をfetchしてDataTablesで描画
│   ├── style.css
│   └── data.json           CIが定期更新する価格データ
├── scripts/
│   └── scrape_to_json.py   docs/data.json を生成するCLI（CIから呼ばれる）
├── .github/workflows/
│   ├── build.yml           Mac/Windowsバイナリ配布用CI
│   └── scheduled-scrape.yml ★ Web版の定期スクレイピング+Pagesデプロイ
├── core/                   models / normalize / compare
├── scrapers/               apple / iosys / mobile_mix / ichome
├── templates/index.html    ローカルFlask版のテンプレート
├── static/style.css
├── output/                 ローカル実行時のlatest.json置き場
├── 配布用-README-Mac.txt   Mac版ZIP同梱のエンドユーザー向け説明
└── .claude/CLAUDE.md       Claude Code向けセットアップガイド
```

ビルド成果物（gitignore済み）:
- `pw-browsers/` — Playwrightローカルブラウザ
- `dist/` — PyInstaller出力（.app または exe フォルダ）
- `build_artifacts/` — PyInstaller中間ファイル

---

## Windows版のビルド

Mac から Windows .exe を**クロスビルドすることはできません**。以下のいずれかが必要です：

### 方法A: GitHub Actions（推奨・無料）

1. このフォルダを GitHub リポジトリにPush
2. リポジトリ画面の「Actions」タブを開く
3. 「Build cross-platform binaries」ワークフローを **Run workflow**
4. 完了後（10〜15分）、Artifacts セクションから `iPhone-checker-windows.zip` をダウンロード

`.github/workflows/build.yml` は Mac と Windows の両方をビルドするよう設定済み。タグPush（`git tag v1.0.0 && git push --tags`）でGitHubリリースに自動添付もされます。

### 方法B: Windowsマシンで直接

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r build-requirements.txt
set PLAYWRIGHT_BROWSERS_PATH=%cd%\pw-browsers
python -m playwright install chromium
python build\build.py --skip-chromium-download
```

成果物: `dist\iPhone転売価格チェッカー\`

---

## 注意事項

- 表示価格は買取サイト掲載額（送料・査定減額は含まれません）
- スクレイピング対象サイトの構造変更により取得失敗することあり
- 各買取サイトに過度な負荷をかけないでください（連続更新は控える）
- Mac版は未署名のため初回起動時に Gatekeeper の警告が出ます（同梱の `お読みください.txt` 参照）
