# セットアップガイド - eBay Research Edge

本ドキュメントは、eBay Research Edge の詳細なセットアップ手順をまとめています。

**対応環境**：Windows 10/11、macOS、Linux

---

## 前提条件

### 必須

- **Python 3.10 以上**
  - Windows：https://www.python.org/downloads/
  - macOS：\rew install python@3.10\
  - Linux：\pt-get install python3.10\

- **Git**（リポジトリクローン用）
  - https://git-scm.com/

- **ブラウザ**：Chrome / Chromium（Playwright で自動ダウンロード）

### API キー取得（必須）

1. **OpenAI API キー**
   - アカウント作成：https://platform.openai.com/account/api-keys
   - モデル：\gpt-4-vision\ または \gpt-4o\
   - 料金：従量課金（画像判定 1 回あたり数円程度）

2. **Google Workspace アカウント**（Sheets 連携用）
   - Google アカウント：https://myaccount.google.com/
   - Google Drive アクセス権限が必要

### API キー取得（オプション）

3. **eBay Developer キー**（公式 API 使用時）
   - デベロッパー登録：https://developer.ebay.com/
   - App ID、Cert ID、Dev ID を取得

---

## ステップ 1：リポジトリのクローン

### Windows（PowerShell）

\\\powershell
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge
\\\

### macOS / Linux（Terminal）

\\\ash
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge
\\\

**確認**：
\\\ash
ls -la
# 出力例：
# README.md
# CHANGELOG.md
# generate_research_report.py
# requirements.txt
# .env.example
# docs/
# templates/
\\\

---

## ステップ 2：Python 仮想環境の作成

### Windows（PowerShell）

\\\powershell
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
\\\

### macOS / Linux（Terminal）

\\\ash
python3 -m venv venv
source venv/bin/activate
\\\

**確認**：プロンプトが \(venv)\ で始まる

\\\
(venv) PS D:\\AI_スクリプト成果物\\ebay-research-edge>
\\\

---

## ステップ 3：依存ライブラリのインストール

### 1. requirements.txt を確認

\\\ash
cat requirements.txt
\\\

**内容例**：
\\\
flask==2.3.0
flask-cors==4.0.0
playwright==1.40.0
requests==2.31.0
python-dotenv==1.0.0
openai==1.0.0
\\\

### 2. インストール実行

\\\ash
pip install -r requirements.txt
\\\

**インストール時間**：3～5 分

**確認**：
\\\ash
pip list | grep -E "flask|playwright|openai"
\\\

---

## ステップ 4：Playwright ブラウザのインストール

\\\ash
playwright install chromium
\\\

**インストール時間**：2～3 分（Chromium ダウンロード）

**確認**：
\\\ash
python -m playwright install --check
\\\

出力：
\\\
Checking browser binaries ...
✓ chromium is up to date
\\\

---

## ステップ 5：環境変数設定

### 1. .env ファイルの作成

\\\ash
copy .env.example .env
\\\
（または手動で \.env\ ファイルを新規作成）

### 2. .env を編集

エディタ（VS Code、Notepad++）で \.env\ を開き、以下を設定：

\\\nv
# OpenAI API キー（GPT-4o Vision 用）
OPENAI_API_KEY=sk-...your-api-key...

# Google Sheets GAS Web App URL
GAS_WEBAPP_URL=https://script.google.com/macros/d/...userweb/app?v=1

# eBay API（オプション）
EBAY_APP_ID=
EBAY_CERT_ID=
EBAY_DEV_ID=
\\\

### 3. API キー設定詳細

#### OpenAI API キー

\\\nv
OPENAI_API_KEY=sk-proj-...
\\\

**取得方法**：
1. https://platform.openai.com/account/api-keys にログイン
2. 「Create new secret key」をクリック
3. キーを \.env\ にコピペ

**確認**：
\\\ash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('OPENAI_API_KEY')
print(f'✓ キー設定済み: {key[:10]}...' if key else '✗ キー未設定')
"
\\\

#### Google Sheets GAS Web App URL

\\\nv
GAS_WEBAPP_URL=https://script.google.com/macros/d/...userweb/app?v=1
\\\

**GAS Web App 作成手順**：

**1. Google Apps Script プロジェクトを作成**
- Google Drive で新規 → その他 → Apps Script
- プロジェクト名：\Bay Research Sheet Sync\

**2. Code.gs に以下を記述**

\\\javascript
function doPost(e) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = JSON.parse(e.postData.contents);

  const row = [
    new Date(),
    data.ebay_title || '',
    data.ebay_price_jpy || '',
    data.purchase_price || '',
    data.profit || '',
    data.roi || '',
    JSON.stringify(data.items) || '',
    JSON.stringify(data.keywords) || ''
  ];

  sheet.appendRow(row);

  return ContentService.createTextOutput(JSON.stringify({
    success: true,
    row_number: sheet.getLastRow(),
    timestamp: new Date().toISOString()
  })).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  return HtmlService.createHtmlOutput('eBay Research Sheet Sync - OK');
}
\\\

**3. 公開設定**
- 「新しい展開」 → 種類：\ウェブアプリ\
- 実行者：「自分」
- アクセスできるユーザー：「全員」
- 展開

**4. Web App URL をコピー**
\\\
https://script.google.com/macros/d/[PROJECT_ID]/userweb/app?v=[VERSION]
\\\

**5. .env に設定**
\\\nv
GAS_WEBAPP_URL=https://script.google.com/macros/d/...userweb/app?v=1
\\\

**6. Google Sheets の準備**

新しい Google Sheet を作成し、ヘッダー行を追加：

| A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|
| Timestamp | eBay Title | eBay Price JPY | Purchase Price | Profit | ROI % | Items | Keywords |

---

## ステップ 6：動作確認テスト

### 1. OpenAI API 接続確認

\\\ash
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✓ OpenAI API 接続確認')
"
\\\

### 2. Playwright 動作確認

\\\ash
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://example.com')
        title = await page.title()
        await browser.close()
        print(f'✓ Playwright 動作確認: {title}')

asyncio.run(test())
"
\\\

### 3. 統合テスト

\\\ash
python generate_research_report.py
\\\

**期待される出力**：
\\\
 * Serving Flask app 'generate_research_report'
 * Debug mode: off
 * Running on http://127.0.0.1:5009
\\\

---

## ステップ 7：起動

### 開発環境での起動

\\\ash
python generate_research_report.py
\\\

ブラウザで **http://127.0.0.1:5009** を開く

### 停止

\\\ash
Ctrl + C
\\\

### 仮想環境の終了

\\\ash
deactivate
\\\

---

## トラブルシューティング

### 問題 1：ModuleNotFoundError: No module named 'flask'

**原因**：仮想環境が有効になっていない

**対応**：
\\\ash
# Windows
.\\venv\\Scripts\\Activate.ps1

# macOS / Linux
source venv/bin/activate
\\\

その後、再度インストール：
\\\ash
pip install -r requirements.txt
\\\

### 問題 2：Playwright ブラウザが起動しない

**原因**：Chromium がインストールされていない

**対応**：
\\\ash
playwright install chromium
\\\

### 問題 3：OpenAI API キーエラー

**原因**：.env ファイルが読み込まれていない、または キーが無効

**対応**：
1. \.env\ ファイルが プロジェクトルート（generate_research_report.py と同じディレクトリ）にあるか確認
2. キーが有効か OpenAI ダッシュボードで確認
3. キーの先頭が \sk-\ で始まるか確認

\\\ash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('OPENAI_API_KEY:', os.getenv('OPENAI_API_KEY')[:20] + '...')
"
\\\

### 問題 4：Google Sheets に保存されない

**原因**：GAS_WEBAPP_URL が設定されていない、または Web App の権限が不足

**対応**：
1. \.env\ で \GAS_WEBAPP_URL\ を確認
2. GAS Web App が「全員」にアクセス許可になっているか確認
3. GAS の実行ログを確認（Apps Script エディタ > 実行ログ）

### 問題 5：メルカリで商品が検索されない

**原因**：メルカリの HTML 構造が変更された

**対応**：
1. ブラウザで mercari.com にアクセス
2. 開発者ツール（F12）で HTML 構造を確認
3. generate_research_report.py の \search_mercari\ 関数のセレクタを更新

現在のセレクタ：
\\\python
items = await page.locator('a[href^=\"/item/m\"]').all()
\\\

---

## 本番環境へのデプロイ

### 推奨環境

- **ホスティング**：AWS EC2、Google Cloud Run、Heroku
- **Web サーバー**：Gunicorn、uWSGI
- **リバースプロキシ**：Nginx
- **データベース**：Google Sheets（現在の仕様では不要）

### デプロイ例（Heroku）

\\\ash
# Heroku CLI をインストール
# https://devcenter.heroku.com/articles/heroku-cli

# Heroku にログイン
heroku login

# アプリを作成
heroku create your-app-name

# 環境変数を設定
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set GAS_WEBAPP_URL=https://...

# デプロイ
git push heroku main
\\\

**Procfile**（プロジェクトルートに作成）：
\\\
web: python generate_research_report.py
\\\

---

## セキュリティ注意事項

1. **.env ファイルは絶対に Git にコミットしない**
   - \.gitignore\ に \.env\ が含まれているか確認

2. **API キーを共有しない**
   - GitHub Issues、Slack、メールで共有しない

3. **定期的にキーをローテーション**
   - 3 ヶ月ごとに新しいキーを生成

4. **本番環境では HTTPS を使用**
   - HTTP は開発環境のみ

---

## パフォーマンス最適化

### 1. キャッシング

為替レートをメモリキャッシュ（実行内）

### 2. タイムアウト設定

各検索関数：5～10 秒タイムアウト（1 つのサイト遅延が全体に影響しない）

### 3. 並行処理

\syncio\ で メルカリ、ハードオフ、Yahoo!フリマ、Yahoo!オークション を同時検索

---

**最終更新**：2026-05-08
**バージョン**：V15.2
