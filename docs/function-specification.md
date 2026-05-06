# eBay-Research-Edge 関数仕様書

## プロジェクト概要

**eBay-Research-Edge** は、eBay.com（米国）で日本から発送されている商品の売上実績からリサーチし、日本国内マーケットプレイス（Amazon、Yahoo、Rakuten等）での仕入れ可能性を分析するツールです。

### リサーチフロー

1. **eBay.com で日本から発送されている商品をリサーチ**
   - Site ID: US（0）
   - フィルタ: ShipsFrom = Japan
   - Sold listings を取得

2. **その商品を日本国内マーケットプレイスで仕入れ可能か確認**
   - Amazon、Yahoo Auction、Yahoo Shopping、Yahoo Fril、Rakuten
   - CSV インポート対応

3. **利益計算（eBay.com 販売価格 - 手数料 - 送料 - 国内仕入価格）**
   - eBay 手数料：カテゴリ ID から自動判定
   - 送料：商品サイズ・重さから計算

4. **スコアリングと候補判定**

---

## 5. ebay_fetcher.py

### クラス: eBayFetcher

**目的**: eBay.com で日本から発送されている Sold 商品をリサーチし、MarketRecord に変換する。

#### メソッド

##### \__init__(use_real_api: bool = True)\
- **説明**: eBayFetcher を初期化
- **パラメータ**:
  - use_real_api (bool): True で実API使用、False でサンプルデータ使用
- **動作**:
  - eBay Trading API クライアント（Site ID = US）を初期化
  - 環境変数から認証情報を読み込み（EBAY_APP_ID, EBAY_DEV_ID, EBAY_CERT_ID, EBAY_USER_TOKEN）

##### \etch_sold_listings(keyword: str, limit: int = 100)\
- **説明**: eBay.com で日本発送の Sold 商品をリサーチ
- **パラメータ**:
  - keyword (str): 検索キーワード（例: "pokemon card"）
  - limit (int): 取得件数上限（デフォルト: 100）
- **戻り値**: List[Dict[str, Any]]
  - category_id, category_name を含むリスティングデータ
- **フィルタ**:
  - SearchLocation: AllItemsCompleted（Sold items のみ）
  - ShipsFrom: JP（日本から発送）
  - exclude_keywords: 除外キーワード（config から取得）

##### \convert_to_market_records(raw_listings: List[Dict])\
- **説明**: eBay API フォーマットを MarketRecord に変換
- **パラメータ**: raw_listings (List[Dict]): eBay API から取得したリスティング
- **戻り値**: List[MarketRecord]
- **抽出情報**:
  - itemId → record_id, item_id
  - title → original_title（normalized_title は後で正規化）
  - price.value → price（USD）
  - shipping.shippingCost.value → shipping（USD）
  - currency → USD
  - category_id, category_name → 属性として保存（手数料率決定用）
  - soldDate → sold_date

---

## eBay API 認証情報

### 環境変数（.env）

\\\
# eBay Trading API Credentials
EBAY_APP_ID=<App ID from eBay Developer Portal>
EBAY_DEV_ID=<Dev ID from eBay Developer Portal>
EBAY_CERT_ID=<Cert ID / Client Secret>
EBAY_USER_TOKEN=<User Token from Auth'n'Auth Sign-In>

# Project Settings
ACTIVE_CATEGORY=pokemon_card
DATA_DIR=./data
\\\

### API エンドポイント

- **Base URL**: https://api.ebay.com/ws/api.dll
- **API Type**: Trading API（XML）
- **Site ID**: 0（United States）
- **Call**: GetSearchResults
  - SearchLocation: AllItemsCompleted（Sold items）
  - ShipsFrom: JP（日本から発送）

---

## カテゴリ ID と手数料率

### eBay カテゴリ別手数料率テーブル

| Category ID | Category Name | Fee Rate | Notes |
|-------------|---------------|----------|-------|
| 29323 | Trading Cards & Accessories | 12.9% | ポケモンカード等 |
| 267 | Coins & Paper Money | 12.9% | |
| 30616 | Art | 12.9% | |
| 46081 | Motors | 6.5% | 自動車関連（低い） |
| その他 | - | 12.9% | デフォルト |

※ category_id は eBay API から取得

---

## 利益計算ロジック（改善予定）

### 現在の仕様（簡易版）

\\\
profit_jpy = (eBay_price_usd * exchange_rate)
           - (eBay_price_usd * exchange_rate * fee_rate)
           - (shipping_cost_usd * exchange_rate)
           - domestic_cost_jpy

profit_rate = (profit_jpy / (eBay_price_usd * exchange_rate)) * 100
\\\

### 改善予定

1. **手数料の自動判定**
   - category_id から fee_rate を自動取得
2. **送料の正確な計算**
   - 商品サイズ・重さから梱包後サイズを算出
   - eBay/郵便局の公式送料表を参照
3. **為替レート**
   - 環境変数または API から動的取得

---

## TODO リスト

- [ ] eBay Trading API クライアント（ShipsFrom フィルタ対応）
- [ ] category_id → fee_rate 自動マッピング
- [ ] 送料計算エンジン（サイズ・重さ対応）
- [ ] 為替レート動的取得
