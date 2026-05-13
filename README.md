# eBay Research Edge - 自動価格リサーチダッシュボード

## 🚀 クイックスタート (正式エントリポイント)

現在の正式なエントリポイントは **`generate_research_report.py`** です。

### 1. 起動手順
```bash
# リポジトリのクローン
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1

# 依存ライブラリのインストール
pip install -r requirements.txt
playwright install chromium

# 設定ファイルの準備 (.env.example をコピーして作成)
cp .env.example .env

# アプリケーションの起動
python generate_research_report.py
```

### 2. アクセス
ブラウザで以下のURLを開きます：
**[http://127.0.0.1:5009/](http://127.0.0.1:5009/)**

> [!NOTE]
> `app.py` および `main.py` は旧系統（試作版）のため、現在は使用しません。

---

## 概要

**eBay Research Edge** は、eBayの商品情報を基に、国内のメルカリ・ヤフーフリマ・ハードオフ等からリアルタイムに価格情報を収集し、利益計算を行う Python/Flask ベースのダッシュボードです。

### 主要機能
- **多重起動ガード**: `/start-search` 実行中の二重起動を防止し、状態の整合性を維持します。
- **実行中表示 (UX)**: バックエンドの検索状態 (`is_searching`) と同期し、UIボタンの自動制御を行います。
- **サイレント・フェイラー可視化**: 検索やAI判定時に発生したエラーをダッシュボード上で透過的に表示します。
- **AI 漢字優先化**: 商品名を日本公式の漢字表記（例：潔世一）にAIで自動変換し、国内サイトのヒット率を最大化します。
- **Google Sheets 連携**: 利益計算結果を GAS Web App 経由でスプレッドシートへ自動保存します。

## 運用設定管理 (`config_runtime.py`)

運用で頻繁に調整が必要な値は、すべて **`config_runtime.py`** に集約されています。コード本体（`generate_research_report.py`）を編集する必要はありません。

### 管理されている主な値
- `MAX_RESEARCH_ITEMS`: 1回の検索で対象とする商品数
- `DEFAULT_SHIPPING_COST_JPY`: デフォルトの送料設定
- `FEE_RATES`: ジャンル別のeBay販売手数料率
- `SERVER_PORT`: アプリケーションの動作ポート番号
- 各種 `timeout` / `wait` 設定：スクレイピングやAPIの待機時間

### 安全化機能 (Validation & Fallback)
設定ファイルには妥当性チェックが組み込まれています。
- 異常な値（負の数値、型不正等）が設定された場合、自動的に**安全な既定値へフォールバック**されます。
- フォールバック発生時は、起動ログに `[CONFIG WARNING]` が出力されます。

## 必須環境変数 (`.env`)

起動には以下の設定が必須です：
- `OPENAI_API_KEY`: AIキーワード抽出・画像比較用
- `EBAY_REST_CLIENT_ID`: eBay APIアクセス用
- `EBAY_REST_CLIENT_SECRET`: eBay APIアクセス用
- `GOOGLE_SHEETS_ID`: 読み込み元スプレッドシートID
- `GAS_WEBAPP_URL`: 保存先 Google Apps Script URL

詳細は [docs/SETUP.md](docs/SETUP.md) を参照してください。

---

## ライセンス
MIT License

**最終更新**: 2026-05-13
**ステータス**: 安定版リリース (generate_research_report.py 系統)
