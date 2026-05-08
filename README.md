# eBay Research Edge - 自動価格リサーチダッシュボード

## 概要

**eBay Research Edge** は、eBay の商品情報を基に、国内複数のフリマアプリ・オークションサイトから自動的に相場情報を収集し、利益計算を行う Python/Flask ベースの Web アプリケーションです。ポケモンカードなどのトレーディングカード転売ビジネスに最適化されています。

バージョン V15.2：AI 判定強化版、Yahoo!オークション落札履歴統合、Google Sheets GAS 連携完成

## 主な機能

### 1. 複数サイトからのリアルタイム価格取得

- **メルカリ**：Playwright を使用した動的スクレイピング。商品画像、価格、リンク自動抽出
- **ハードオフ**：オンラインストアから商品情報を取得
- **Yahoo!フリマ**：Yahoo!フリマのマーケットプレイスから価格情報を収集
- **Yahoo!オークション**：落札履歴から最小・最大・中央値の統計を自動計算

### 2. eBay 統合

- eBay API を使用した出品情報の自動取得
- USD から JPY への為替レート自動換算（リアルタイム）
- 手数料自動計算（eBay 手数料 11.35%）

### 3. AI を使用した高精度判定

- **GPT-4o Vision**：eBay 出品画像と国内マーケットプレイス商品画像の比較判定
- **レプリカ・観賞用品検知**：商品説明から「レプリカ」「観賞用」「展示用」などのキーワードを検出し、一致度を 0% に強制設定
- **高精度キーワード抽出**：カード番号（例：110/080）とレアリティ（SAR、AR など）を優先的に抽出し、検索精度を向上

### 4. 利益計算と自動管理

- **仕入れ値編集機能**：テキストボックスで手動入力可能
- **リアルタイム利益計算**：利益 = eBay価格 JPY - (手数料 + 送料) - 仕入れ値
- **ROI 自動計算**：ROI = (利益 / 仕入れ値) × 100%
- **Google Sheets 自動保存**：GAS Web App を経由して分析結果を自動保存

### 5. スマートフィルタリング

- **低価格除外**：100 円未満の商品を自動除外
- **不適切商品除外**：「盗難防止品」などのキーワードを含む商品をフィルタ
- **スクレイピング除外フィルタ**：タイトル・HTML に除外キーワードを含む商品を検索から排除

### 6. インタラクティブダッシュボード

- リアルタイム検索進捗表示（例：[3/10]）
- 各サイトの検索結果を段階的に表示
- 詳細情報ボタンで商品の全情報を確認（画像、価格、AI 判定スコア）
- 個別保存・一括保存機能

## システム構成

### アーキテクチャ

\\\
┌─────────────────────────────────────────────────┐
│    eBay Research Edge - Frontend (HTML/CSS/JS)  │
│      インタラクティブダッシュボード表示          │
└────────────────────┬────────────────────────────┘
                     │ AJAX (3秒ポーリング)
┌────────────────────▼────────────────────────────┐
│     Flask Backend (Python 3.10+)                │
│  ├─ GET  /        (HTML ダッシュボード)        │
│  ├─ GET  /data    (リアルタイム検索結果)       │
│  ├─ POST /analyze (AI 画像判定)                │
│  └─ POST /save    (Google Sheets 保存)         │
└────────────────────┬────────────────────────────┘
                     │
     ┌───────────────┼───────────────┬────────────┐
     │               │               │            │
  ┌──▼──┐  ┌────────▼──────┐  ┌────▼─────┐  ┌──▼──┐
  │ eBay│  │  Mercari      │  │ Hard Off  │  │Yahoo│
  │ API │  │ (Playwright)  │  │(Playwright)  │FM & │
  └─────┘  └───────────────┘  └───────────┘  │Auc  │
                                              │tion │
           ┌─────────────────┐               └─────┘
           │  OpenAI GPT-4o  │
           │  Vision API     │
           │  (画像判定)     │
           └─────────────────┘
                     │
           ┌─────────▼─────────┐
           │ Google Sheets     │
           │ (GAS Web App)     │
           │ リサーチ結果保存   │
           └───────────────────┘
\\\

### 使用技術

**バックエンド**
- Python 3.10+
- Flask 2.0+：Web アプリケーションフレームワーク
- Playwright 1.40+：動的スクレイピング（メルカリ、ハードオフ、Yahoo!フリマ、Yahoo!オークション）
- asyncio：非同期処理による並行実行
- OpenAI Python SDK：GPT-4o Vision API 連携
- requests：HTTP リクエスト処理

**フロントエンド**
- HTML5 / CSS3
- JavaScript（Vanilla、フレームワーク不使用）
- AJAX ポーリング（3 秒間隔でサーバーから検索結果を取得）

**データ連携**
- Google Apps Script (GAS)：Web App として動作、Google Sheets への書き込み
- JSON：API レスポンスフォーマット

**外部 API**
- OpenAI GPT-4o Vision：画像認識・比較判定
- eBay Browse API：商品情報取得
- exchangerate-api.com：為替レート取得（無料）

## ファイル構成

\\\
ebay-research-edge/
├── generate_research_report.py    （メインアプリケーション、893 行）
├── requirements.txt               （Python 依存ライブラリ）
├── .env.example                   （環境変数テンプレート）
├── .gitignore                     （Git 除外ファイル）
├── README.md                      （このファイル）
├── CHANGELOG.md                   （更新履歴）
├── docs/
│   ├── API.md                    （API リファレンス）
│   ├── SETUP.md                  （セットアップ詳細）
│   └── FEATURES.md               （機能詳細）
└── templates/
    └── index.html                 （ダッシュボード HTML）
\\\

## インストール・セットアップ

### 前提条件

- **Python**：3.10 以上
- **ブラウザ**：Chrome / Chromium（Playwright 用）
- **API キー**：
  - OpenAI API キー（GPT-4o Vision 利用）
  - eBay Developer キー（オプション）
  - Google Workspace アカウント（Sheets 連携用）

### インストール手順

#### 1. リポジトリのクローン

\\\ash
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge
\\\

#### 2. Python 依存ライブラリのインストール

\\\ash
pip install -r requirements.txt
\\\

**主要なライブラリ**
- flask, flask-cors
- playwright
- requests
- python-dotenv
- openai

#### 3. Playwright ブラウザのインストール

\\\ash
playwright install chromium
\\\

#### 4. 環境変数設定

\.env\ ファイルを作成（\.env.example\ をコピーして使用）：

\\\nv
# OpenAI（GPT-4o Vision）
OPENAI_API_KEY=sk-...your-api-key...

# Google Sheets GAS Web App URL
GAS_WEBAPP_URL=https://script.google.com/macros/d/...userweb/app?v=1

# eBay API（オプション）
EBAY_APP_ID=...
EBAY_CERT_ID=...
EBAY_DEV_ID=...
\\\

#### 5. 起動

\\\ash
python generate_research_report.py
\\\

ブラウザで **http://127.0.0.1:5009** を開きます。

## 使用方法

### 基本的なリサーチフロー

1. **メイン画面でリサーチ開始**
   - ダッシュボードが表示される
   - 自動的に eBay、メルカリ、ハードオフ、Yahoo!フリマ、Yahoo!オークション から検索を開始

2. **リアルタイム検索結果の確認**
   - 各サイトの検索が完了するたびに結果が段階的に表示
   - 進捗状況が「[N/10]」で表示（例：[3/10]）

3. **AI 判定結果の確認**
   - 各商品の AI 判定スコア（例：85%）が表示
   - レプリカ・観賞用品の場合は 0% で警告表示

4. **仕入れ値の入力と利益計算**
   - 「仕入れ値」欄にテキストボックスで金額を入力
   - 利益、ROI がリアルタイムで自動計算表示
   - 計算式：利益 = eBay価格 JPY - (手数料 + 送料) - 仕入れ値

5. **Google Sheets へ保存**
   - 「保存」ボタンをクリック
   - GAS を経由して Google Sheets に自動書き込み
   - 過去のリサーチ履歴として蓄積

### ダッシュボード機能詳細

**詳細ボタン**
- 各商品の「詳細」をクリックすると全情報を表示
- eBay 画像、国内サイト画像、AI 判定スコア、商品説明文

**フィルタリング（自動）**
- 100 円未満の商品：表示なし（自動除外）
- 「盗難防止品」キーワード含む：表示なし（自動除外）

**保存オプション**
- 「個別保存」：選択した 1 件を保存
- 「すべて保存」：全検索結果を保存

## API リファレンス

### エンドポイント一覧

#### GET /
ダッシュボード HTML を返す

#### GET /data
リアルタイム検索結果を JSON で返す

**レスポンス例**：
\\\json
{
  "is_finished": false,
  "progress": "[3/10]",
  "results": [
    {
      "idx": 1,
      "ebay_title": "Mega Charizard X ex SAR 110/080",
      "ebay_price_jpy": 15000,
      "fees": 1702,
      "shipping": 1500,
      "items": [
        {
          "price": 8000,
          "source": "mercari",
          "url": "https://mercari.com/...",
          "image": "https://..."
        },
        {
          "price": 7500,
          "source": "hardoff",
          "url": "https://hardoff.jp/...",
          "image": "https://..."
        }
      ],
      "keywords": ["リザードン", "SAR", "110/080"]
    }
  ]
}
\\\

#### POST /analyze
AI 画像判定を実行

**リクエスト例**：
\\\json
{
  "ebay_image_url": "https://...",
  "compare_image_url": "https://...",
  "product_description": "Pokemon Card Charizard..."
}
\\\

**レスポンス例**：
\\\json
{
  "match_percentage": 85,
  "analysis": "Same card, same rarity, minor condition difference",
  "is_counterfeit": false
}
\\\

#### POST /save
Google Sheets に結果を保存

**リクエスト例**：
\\\json
{
  "ebay_title": "Mega Charizard X ex SAR 110/080",
  "ebay_price_jpy": 15000,
  "purchase_price": 5000,
  "profit": 8798,
  "roi": 176,
  "items": [...]
}
\\\

## 実装済み関数一覧

| 関数名 | 説明 |
|--------|------|
| \parse_currency\ | 通貨文字列をパース（例：".00" → 15.0） |
| \get_exchange_rate\ | USD → JPY 為替レートを取得 |
| \get_ebay_token\ | eBay API トークンを取得（キャッシュ対応） |
| \etch_yahoo_auction_history\ | Yahoo!オークション落札履歴から統計計算 |
| \get_ebay_image\ | eBay 出品画像 URL を取得 |
| \xtract_keywords\ | 商品名からカード番号・レアリティを抽出 |
| \search_mercari\ | メルカリから価格・画像・リンク取得（Playwright） |
| \search_yahoo\ | Yahoo!フリマから同上 |
| \search_hardoff\ | ハードオフから同上 |
| \main_process\ | メイン処理（非同期で全サイト検索を並行実行） |
| \nalyze\ | GPT-4o Vision で画像判定 |
| \save_to_sheet\ | Google Sheets GAS に保存 |

## トラブルシューティング

### ダッシュボードが空白のまま動かない

**原因**：Playwright ブラウザが起動していない、または依存ライブラリ不足

**対応**：
\\\ash
pip install -r requirements.txt
playwright install chromium
python generate_research_report.py
\\\

### Yahoo!オークション検索でタイムアウト

**原因**：ネットワーク遅延またはサイト側の応答遅延

**対応**：generate_research_report.py の \etch_yahoo_auction_history\ 関数内のタイムアウト値を増やす

\\\python
await asyncio.wait_for(
    new_page.goto(url, wait_until='domcontentloaded'),
    timeout=15  # 15秒に増やす
)
\\\

### Google Sheets に保存されない

**原因**：GAS_WEBAPP_URL が設定されていない、または GAS の権限が不足

**対応**：
1. \.env\ で \GAS_WEBAPP_URL\ を確認
2. Google Apps Script で Web App が「全員」にアクセス許可になっているか確認
3. GAS ログ（Apps Script 管理画面 > 実行ログ）を確認

### メルカリで商品が検索されない

**原因**：メルカリの DOM 構造が変更された

**対応**：generate_research_report.py の \search_mercari\ 関数内のセレクタを最新に更新

現在のセレクタ：
\\\python
items = await page.locator('a[href^="/item/m"]').all()
\\\

## パフォーマンス最適化

### 並行処理

メルカリ、ハードオフ、Yahoo!フリマ、Yahoo!オークション の検索は Python の \syncio\ を使用して並行実行されます。
\\\python
m_res = await search_mercari(page, kw)
y_res = await search_yahoo(page, kw)
y_history = await fetch_yahoo_auction_history(kw, browser)
h_res = await search_hardoff(page, kw)
\\\

### タイムアウト設定

各検索関数には独立したタイムアウト（5～10 秒）が設定されており、1 つのサイト遅延が全体に影響しません。

### キャッシング

為替レートは メモリキャッシュ で保持され、1 回の実行内で複数回の API 呼び出しを削減

## ライセンス

MIT License

## 貢献

Pull Request を歓迎します。大きな変更の場合は、まず Issue を開いて変更内容を議論してください。

## サポート

問題が発生した場合は、GitHub Issues で報告してください。

---

**最終更新**：2026-05-08
**バージョン**：V15.2
**ステータス**：本番リリース (main ブランチ)

機能：AI 判定強化版、Yahoo!オークション落札履歴統合、Google Sheets GAS 連携完成、メルカリ DOM 対応、レプリカ検知フィルタ、中央値採用
