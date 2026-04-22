# docs/data-model.md

# eBay-Research-Edge Data Model

## 1. items
商品マスタ的な役割を持つ。

| column | type | description |
|---|---|---|
| item_id | string | 商品ID |
| normalized_name | string | 正規化済み商品名 |
| franchise | string | 作品名 |
| character | string | キャラ名 |
| category | string | 大分類 |
| subcategory | string | 小分類 |
| created_at | datetime | 作成日時 |
| updated_at | datetime | 更新日時 |

## 2. market_records
国内外の取得レコードを保持する。

| column | type | description |
|---|---|---|
| record_id | string | レコードID |
| item_id | string | 商品ID |
| source_site | string | ebay / mercari / yahoo_auction |
| search_keyword | string | 検索キーワード |
| original_title | string | 元タイトル |
| normalized_title | string | 正規化後タイトル |
| price | float | 本体価格 |
| shipping | float | 送料 |
| currency | string | 通貨 |
| total_price | float | price + shipping |
| sold_flag | bool | Soldか |
| active_flag | bool | 出品中か |
| sold_date | datetime/null | 販売日時 |
| listing_url | string | 商品URL |
| fetched_at | datetime | 取得日時 |

## 3. scored_candidates
集計結果と判定を持つ。

| column | type | description |
|---|---|---|
| candidate_id | string | 候補ID |
| item_id | string | 商品ID |
| sold_30d | int | 30日Sold件数 |
| sold_90d | int | 90日Sold件数 |
| active_count | int | 現在出品数 |
| median_price_usd | float | eBay中央値 |
| avg_price_usd | float | eBay平均値 |
| min_price_usd | float | eBay最安値 |
| max_price_usd | float | eBay最高値 |
| domestic_min_price_jpy | float | 国内最安値 |
| domestic_median_price_jpy | float | 国内中央値 |
| estimated_profit_jpy | float | 概算利益額 |
| estimated_profit_rate | float | 概算粗利率 |
| str | float | Sell Through Rate |
| candidate_score | float | 総合スコア |
| decision_status | string | list_candidate / hold / skip |
| calculated_at | datetime | 計算日時 |

## 4. 指標定義
### STR
STR = sold / (sold + active) * 100

### estimated_profit_jpy
estimated_profit_jpy = ebay_sell_price_jpy - domestic_cost_jpy - shipping_jpy - fee_jpy

### estimated_profit_rate
estimated_profit_rate = estimated_profit_jpy / ebay_sell_price_jpy * 100