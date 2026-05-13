# セットアップガイド - eBay Research Edge

本ドキュメントは、eBay Research Edge の詳細な環境構築手順および設定項目の解説をまとめています。

---

## 1. 環境構築手順

### ステップ 1: リポジトリのクローン
```bash
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge
```

### ステップ 2: 仮想環境の作成
OSに合わせて以下のコマンドを実行してください。

**Windows (PowerShell)**:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux (Terminal)**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### ステップ 3: 依存ライブラリのインストール
```bash
pip install -r requirements.txt
playwright install chromium
```

### ステップ 4: 環境変数 (.env) の設定
`.env.example` をコピーして `.env` を作成し、必要な情報を入力してください。

```bash
cp .env.example .env
```

---

## 2. 環境変数 (.env) 詳細

| 変数名 | 説明 | 必須 |
| :--- | :--- | :---: |
| `OPENAI_API_KEY` | キーワード変換、画像比較で使用します。 | ✅ |
| `EBAY_REST_CLIENT_ID` | eBay API アクセス用の App ID です。 | ✅ |
| `EBAY_REST_CLIENT_SECRET` | eBay API アクセス用の Cert ID です。 | ✅ |
| `GOOGLE_SHEETS_ID` | 読み込み元のスプレッドシートIDです。URLの `/d/[ID]/edit` の部分です。 | ✅ |
| `GAS_WEBAPP_URL` | 保存用の GAS Web App のデプロイ済み URL です。 | ✅ |

---

## 3. 運用設定 (`config_runtime.py`) ガイド

頻繁に変更する設定値は `config_runtime.py` で管理されています。

### 主要設定項目
- **`MAX_RESEARCH_ITEMS`**: 1回の実行でリサーチする最大件数 (デフォルト: 10)
- **`DEFAULT_SHIPPING_COST_JPY`**: 固定送料の初期値 (デフォルト: 1500)
- **`FEE_RATES`**: ジャンルごとの手数料率を定義する辞書。
- **`SERVER_PORT`**: Flaskサーバーが待機するポート (デフォルト: 5009)
- **`UI_POLLING_INTERVAL_MS`**: UIが情報を取得する間隔 (デフォルト: 3000ms)

### タイムアウト設定
- **`BROWSER_GOTO_TIMEOUT_MS`**: ページ遷移の最大待ち時間。
- **`BROWSER_SELECTOR_TIMEOUT_MS`**: 商品要素が現れるまでの待ち時間。
- **`API_REQUEST_TIMEOUT_SECONDS`**: 各種APIリクエストのタイムアウト。

---

## 4. バリデーション機能と警告

`config_runtime.py` には、設定ミスによるアプリの停止を防ぐためのバリデーターが実装されています。

### フォールバック (安全な代入)
異常な値（負の数、間違った型など）が設定された場合、自動的に安全なデフォルト値が使用されます。

**例:**
- `SERVER_PORT = "invalid"` → `5009` を使用
- `MAX_RESEARCH_ITEMS = -5` → `10` を使用

### [CONFIG WARNING]
フォールバックが発生した場合、アプリケーション起動時にターミナルへ警告が出力されます。

```text
[CONFIG WARNING] 'MAX_RESEARCH_ITEMS' に異常値を検出 (-5): Value -5 is below minimum 1. 安全な規定値 '10' を使用します。
```
起動時にこの警告が出ている場合は、`config_runtime.py` の設定内容を見直してください。

---

## 5. トラブルシューティング

### 起動時に `ModuleNotFoundError` が出る
`requirements.txt` のインストールが完了していない可能性があります。
`pip install -r requirements.txt` を再実行してください。

### ブラウザが立ち上がらない / スクレイピングに失敗する
Playwright のブラウザ本体がインストールされていない可能性があります。
`playwright install chromium` を実行してください。

### `[CONFIG WARNING]` が頻発する
`config_runtime.py` 内の設定値の型（`int` であるべき場所に文字列がある等）や、最小値の制限（タイムアウト値が0以下等）を確認してください。

### 検索結果が表示されない / 進まない
1. `.env` の API キーが正しいか確認してください。
2. `GOOGLE_SHEETS_ID` が正しいスプレッドシートを指しているか確認してください。
3. タイムアウトが頻発する場合は、`config_runtime.py` の `BROWSER_GOTO_TIMEOUT_MS` などの値を増やしてください。

---
**最終更新**: 2026-05-13
