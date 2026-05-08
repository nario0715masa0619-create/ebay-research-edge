# API リファレンス - eBay Research Edge

本ドキュメントは、eBay Research Edge の Flask API エンドポイント仕様をまとめています。

**ベース URL**：\http://127.0.0.1:5009\

---

## エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | \/\ | ダッシュボード HTML を返す |
| GET | \/data\ | リアルタイム検索結果を JSON で返す |
| POST | \/analyze\ | AI 画像判定を実行 |
| POST | \/save\ | Google Sheets に結果を保存 |

---

## GET /

**説明**：ダッシュボード HTML を返す

**パラメータ**：なし

**レスポンス**：
- **Content-Type**：\	ext/html; charset=utf-8\
- **ステータスコード**：200 OK
- **本体**：HTML ダッシュボード（template/index.html）

**例**：
\\\ash
curl http://127.0.0.1:5009/
\\\

---

## GET /data

**説明**：リアルタイム検索結果を JSON で返す

**パラメータ**：なし

**レスポンス**：

\\\json
{
  "is_finished": false,
  "progress": "[3/10]",
  "results": [
    {
      "idx": 1,
      "ebay_title": "Mega Charizard X ex SAR 110/080 Inferno X M2",
      "ebay_img": "https://i.ebayimg.com/...",
      "ebay_price_jpy": 15000,
      "fees": 1702.5,
      "shipping": 1500,
      "items": [
        {
          "price": 8000,
          "source": "mercari",
          "url": "https://mercari.com/item/m...",
          "image": "https://api.mercari.jp/...",
          "ai_match": 85
        },
        {
          "price": 7500,
          "source": "hardoff",
          "url": "https://hardoff.jp/...",
          "image": "https://...",
          "ai_match": 82
        },
        {
          "price": 9500,
          "source": "yahoo_flea",
          "url": "https://paypay.ne.jp/...",
          "image": "https://...",
          "ai_match": 88
        },
        {
          "price": 41365,
          "source": "yahoo_auction_history",
          "min": 4580,
          "max": 81500,
          "median": 41365,
          "count": 7,
          "url": "https://auctions.yahoo.co.jp/..."
        }
      ],
      "keywords": ["リザードン", "SAR", "110/080"]
    },
    {
      "idx": 2,
      "ebay_title": "Manaphy 004/PPP 5th Players Experience Promo",
      "ebay_img": "https://i.ebayimg.com/...",
      "ebay_price_jpy": 12000,
      "fees": 1362,
      "shipping": 1500,
      "items": [
        {
          "price": 3800,
          "source": "mercari",
          "url": "https://mercari.com/item/...",
          "image": "https://...",
          "ai_match": 90
        }
      ],
      "keywords": ["マナフィ", "004/PPP"]
    }
  ]
}
\\\

**フィールド説明**：

| フィールド | 型 | 説明 |
|-----------|-----|------|
| \is_finished\ | boolean | 検索が完了したか（true=完了、false=進行中） |
| \progress\ | string | 進捗状況（例：[3/10]） |
| \esults\ | array | 検索結果の配列 |
| \esults[].idx\ | number | eBay 出品インデックス（1～10） |
| \esults[].ebay_title\ | string | eBay 出品タイトル |
| \esults[].ebay_img\ | string | eBay 出品画像 URL |
| \esults[].ebay_price_jpy\ | number | eBay 価格（JPY 換算） |
| \esults[].fees\ | number | eBay 手数料（11.35%） |
| \esults[].shipping\ | number | 送料（デフォルト 1500 円） |
| \esults[].items\ | array | 国内マーケットプレイス検索結果 |
| \esults[].items[].price\ | number | 価格（JPY） |
| \esults[].items[].source\ | string | ソース（mercari, hardoff, yahoo_flea, yahoo_auction_history） |
| \esults[].items[].url\ | string | 商品 URL |
| \esults[].items[].image\ | string | 商品画像 URL |
| \esults[].items[].ai_match\ | number | AI 一致度スコア（0～100%） |
| \esults[].items[].min\ | number | （Yahoo!オークションのみ）最小落札価格 |
| \esults[].items[].max\ | number | （Yahoo!オークションのみ）最大落札価格 |
| \esults[].items[].median\ | number | （Yahoo!オークションのみ）中央値 |
| \esults[].items[].count\ | number | （Yahoo!オークションのみ）落札件数 |
| \esults[].keywords\ | array | 抽出されたキーワード |

**例**：
\\\ash
curl http://127.0.0.1:5009/data
\\\

**ステータスコード**：
- 200 OK：正常取得
- 500 Internal Server Error：サーバーエラー

---

## POST /analyze

**説明**：GPT-4o Vision で eBay 画像と国内マーケットプレイス商品画像を比較し、一致度を判定

**リクエスト形式**：JSON

**リクエスト例**：

\\\json
{
  "ebay_image_url": "https://i.ebayimg.com/...",
  "compare_image_url": "https://api.mercari.jp/...",
  "product_description": "Charizard EX 100/102 Holo Rare Pokemon Card - Mint Condition"
}
\\\

**リクエストフィールド**：

| フィールド | 型 | 説明 | 必須 |
|-----------|-----|------|------|
| \bay_image_url\ | string | eBay 出品画像 URL | ✅ |
| \compare_image_url\ | string | 比較対象の国内商品画像 URL | ✅ |
| \product_description\ | string | 商品説明文 | ❌ |

**レスポンス例**：

\\\json
{
  "match_percentage": 85,
  "analysis": "Same Pokemon card (Charizard EX), same rarity and holo type. Minor difference in card condition (eBay specimen appears to have slightly more wear).",
  "is_counterfeit": false,
  "keywords_detected": ["counterfeit", "replica", "observation"],
  "confidence": 0.92
}
\\\

**レスポンスフィールド**：

| フィールド | 型 | 説明 |
|-----------|-----|------|
| \match_percentage\ | number | 一致度スコア（0～100%） |
| \nalysis\ | string | AI の判定分析結果（日本語） |
| \is_counterfeit\ | boolean | レプリカ・観賞用品か（true=レプリカ、false=正規品） |
| \keywords_detected\ | array | 検出されたキーワード |
| \confidence\ | number | 判定の信頼度（0～1.0） |

**エラーレスポンス例**：

\\\json
{
  "error": "Image URL invalid or unreachable",
  "match_percentage": 0,
  "is_counterfeit": false
}
\\\

**例**：
\\\ash
curl -X POST http://127.0.0.1:5009/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ebay_image_url": "https://i.ebayimg.com/...",
    "compare_image_url": "https://api.mercari.jp/...",
    "product_description": "..."
  }'
\\\

**ステータスコード**：
- 200 OK：判定成功
- 400 Bad Request：パラメータ不足
- 500 Internal Server Error：AI API エラー

---

## POST /save

**説明**：Google Sheets に検索結果を保存

**リクエスト形式**：JSON

**リクエスト例**：

\\\json
{
  "ebay_title": "Mega Charizard X ex SAR 110/080 Inferno X M2",
  "ebay_price_jpy": 15000,
  "purchase_price": 5000,
  "profit": 8798,
  "roi": 176,
  "items": [
    {
      "price": 8000,
      "source": "mercari",
      "url": "https://mercari.com/item/...",
      "image": "https://...",
      "ai_match": 85
    },
    {
      "price": 41365,
      "source": "yahoo_auction_history",
      "min": 4580,
      "max": 81500,
      "median": 41365,
      "count": 7
    }
  ],
  "keywords": ["リザードン", "SAR", "110/080"]
}
\\\

**リクエストフィールド**：

| フィールド | 型 | 説明 | 必須 |
|-----------|-----|------|------|
| \bay_title\ | string | eBay 出品タイトル | ✅ |
| \bay_price_jpy\ | number | eBay 価格（JPY） | ✅ |
| \purchase_price\ | number | 仕入れ値（JPY） | ✅ |
| \profit\ | number | 利益（JPY） | ✅ |
| \oi\ | number | ROI（%） | ✅ |
| \items\ | array | 検索結果一覧 | ❌ |
| \keywords\ | array | キーワード | ❌ |

**レスポンス例**：

\\\json
{
  "success": true,
  "message": "Data saved to Google Sheets successfully",
  "sheet_url": "https://docs.google.com/spreadsheets/d/.../...",
  "row_number": 15,
  "timestamp": "2026-05-08T13:45:30Z"
}
\\\

**レスポンスフィールド**：

| フィールド | 型 | 説明 |
|-----------|-----|------|
| \success\ | boolean | 保存成功か |
| \message\ | string | メッセージ |
| \sheet_url\ | string | Google Sheets URL |
| \ow_number\ | number | 書き込み行番号 |
| \	imestamp\ | string | 保存タイムスタンプ（ISO 8601） |

**エラーレスポンス例**：

\\\json
{
  "success": false,
  "error": "GAS_WEBAPP_URL not configured",
  "message": ".env file missing or invalid"
}
\\\

**例**：
\\\ash
curl -X POST http://127.0.0.1:5009/save \
  -H "Content-Type: application/json" \
  -d '{
    "ebay_title": "...",
    "ebay_price_jpy": 15000,
    "purchase_price": 5000,
    "profit": 8798,
    "roi": 176,
    "items": [...],
    "keywords": [...]
  }'
\\\

**ステータスコード**：
- 200 OK：保存成功
- 400 Bad Request：パラメータ不足
- 500 Internal Server Error：Google Sheets API エラー

---

## レート制限

現在、API レート制限は設定されていません。
本番環境では実装予定です。

---

## エラーハンドリング

### 共通エラーレスポンス

\\\json
{
  "error": "error_code",
  "message": "エラーメッセージ",
  "timestamp": "2026-05-08T13:45:30Z"
}
\\\

### よくあるエラー

| ステータス | エラー | 原因 |
|----------|--------|------|
| 400 | BadRequest | リクエスト形式が不正 |
| 404 | NotFound | エンドポイントが存在しない |
| 500 | InternalServerError | サーバー内部エラー |
| 503 | ServiceUnavailable | 外部 API（OpenAI, Google Sheets）が利用不可 |

---

## 認証

現在、API 認証は実装されていません。
本番環境では API キー認証の実装を予定しています。

---

## ベストプラクティス

### 1. /data ポーリング間隔

JavaScript で 3 秒間隔でポーリングされます。
手動で呼び出す場合は、3～5 秒の間隔を推奨します。

\\\javascript
setInterval(() => {
  fetch('/data')
    .then(res => res.json())
    .then(data => console.log(data));
}, 3000);
\\\

### 2. /analyze の画像 URL

- **形式**：公開アクセス可能な HTTPS URL
- **サイズ**：1MB 以下推奨（超過時は自動圧縮）
- **タイムアウト**：30 秒

### 3. /save の呼び出しタイミング

- ユーザーが「保存」ボタンをクリック時
- または定期的に自動保存（未実装）

---

**最終更新**：2026-05-08
**API バージョン**：v1.0
