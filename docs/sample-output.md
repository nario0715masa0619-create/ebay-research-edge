# docs/sample-output.md

# eBay-Research-Edge Sample Output

## 1. 期待する出力列
最低限、以下を出力する。

- normalized_name
- sold_30d
- sold_90d
- active_count
- median_price_usd
- avg_price_usd
- domestic_min_price_jpy
- domestic_median_price_jpy
- estimated_profit_jpy
- estimated_profit_rate
- str
- candidate_score
- decision_status

## 2. CSVイメージ

```csv
normalized_name,sold_30d,sold_90d,active_count,median_price_usd,avg_price_usd,domestic_min_price_jpy,domestic_median_price_jpy,estimated_profit_jpy,estimated_profit_rate,str,candidate_score,decision_status
Anime Postcard A,2,5,3,49.99,47.50,1800,2200,2500,22.5,40.0,81.2,list_candidate
Anime Postcard B,1,2,8,29.99,31.20,2400,2600,300,3.1,11.1,42.8,skip
```

## 3. テーブル表示イメージ

| normalized_name | sold_30d | active_count | median_price_usd | domestic_min_price_jpy | estimated_profit_rate | str | candidate_score | decision_status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Anime Postcard A | 2 | 3 | 49.99 | 1800 | 22.5 | 40.0 | 81.2 | list_candidate |
| Anime Postcard B | 1 | 8 | 29.99 | 2400 | 3.1 | 11.1 | 42.8 | skip |

## 4. UIイメージ
- 上部に検索条件
- その下に指標カード
- メインに候補一覧テーブル
- 行クリックで詳細表示