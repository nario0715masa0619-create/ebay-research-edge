# eBay-Research-Edge - 操作ガイド

このドキュメントでは、eBay-Research-Edge の使用方法を説明します。

## セットアップ

### 1. 依存パッケージのインストール

\\\ash
pip install -r requirements.txt
\\\

### 2. 環境変数の設定（オプション）

\\\.env
ACTIVE_CATEGORY=pokemon_card
DATA_DIR=./data
\\\

## 使用方法

### 方法 1: CLI で実行（コマンドライン）

基本的な実行：
\\\ash
python app.py
\\\

キーワードを指定：
\\\ash
python app.py --keyword "pokemon card" --limit 50
\\\

オプション：
- \--keyword\: 検索キーワード（デフォルト: pokemon card）
- \--limit\: 1ソースあたりの取得件数上限（デフォルト: 50）
- \--category\: カテゴリ名（デフォルト: pokemon_card）

実行例：
\\\ash
python app.py --keyword "anime goods" --limit 100
\\\

### 方法 2: Streamlit ダッシュボード（Web UI）

ダッシュボードを起動：
\\\ash
streamlit run dashboard.py
\\\

ブラウザで \http://localhost:8501\ を開く。

**ダッシュボード機能：**
- 🔍 キーワード入力
- 📊 検索結果の要約メトリクス表示
- 🔎 フィルター＆ソート機能
- 📋 候補リスト表示
- 💾 CSV ダウンロード

## パイプラインの流れ

1. **データ取得**: eBay Sold データ と Mercari データを取得
2. **正規化**: タイトルやメタデータを標準化
3. **集計**: 30日/90日の売上本数、価格統計を計算
4. **スコア計算**: 需要度、利益性、供給度から候補スコアを算出
5. **判定**: LIST候補 / 保留 / 見送り の3段階に分類
6. **出力**: CSV ファイルに結果を保存

## 出力ファイル

### CSV ファイル

結果は \data/processed/\ に以下の形式で保存されます：

\\\
candidates_pokemon_card_20260423_231037.csv
\\\

**CSVカラム：**
| カラム | 説明 |
|--------|------|
| item_name | 商品名（正規化済み） |
| sold_30d | 30日間の売上本数 |
| sold_90d | 90日間の売上本数 |
| active_count | 現在の出品数 |
| median_price_usd | eBay 中央値（USD） |
| domestic_min_price_jpy | 国内最安価格（JPY） |
| domestic_median_price_jpy | 国内中央値（JPY） |
| estimated_profit_jpy | 推定利益（JPY） |
| estimated_profit_rate | 推定利益率（%） |
| str | 売上回転率（%） |
| candidate_score | 総合スコア（0-100） |
| decision_status | 判定（list_candidate/hold/skip） |

## スコアリング基準

### 候補スコア計算式

\\\
candidate_score = 0.4 × demand_score + 0.4 × profit_score + 0.2 × supply_score
\\\

### 判定基準

| スコア | 判定 | 意味 |
|--------|------|------|
| ≥ 80 | list_candidate | 出品を強く推奨 |
| 60-79 | hold | 保留（追加調査推奨） |
| < 60 | skip | 出品を推奨しない |

## カテゴリの追加・変更

新しいカテゴリを追加する場合：

1. \data/categories/\ に新しい YAML ファイルを作成
   \\\
   data/categories/anime_goods.yaml
   \\\

2. ファイル形式（参照: \pokemon_card.yaml\）:
   \\\yaml
   category:
     name: "Anime Goods"
     name_ja: "アニメグッズ"
   ebay:
     keywords: ["anime figurine", "anime goods"]
     exclude_keywords: ["broken", "damaged"]
   mercari:
     keywords: ["アニメグッズ", "フィギュア"]
     exclude_keywords: ["傷"]
   normalization:
     title_patterns: [...]
   pricing:
     ebay_fee_rate: 0.129
     shipping_cost_estimate_usd: 15.0
     mercari_fee_rate: 0.10
   scoring:
     demand_weight: 0.4
     profit_weight: 0.4
     supply_weight: 0.2
   \\\

3. 環境変数で指定:
   \\\ash
   export ACTIVE_CATEGORY=anime_goods
   python app.py
   \\\

   または CLI オプション:
   \\\ash
   python app.py --category anime_goods
   \\\

## トラブルシューティング

### CSV が生成されない

**原因**: 正規化後に eBay と Mercari の両方のデータがない商品のみが該当

**解決策**: 
- キーワードを変更してみる
- 取得件数を増やす（\--limit 100\）

### Streamlit が起動しない

**原因**: Streamlit がインストールされていない

**解決策**:
\\\ash
pip install streamlit
\\\

### eBay API が利用できない（API申請中の場合）

現在はサンプルデータで動作します。eBay API 申請が承認されたら、\src/fetcher/ebay_fetcher.py\ の \_fetch_from_api()\ メソッドを実装してください。

## 開発ルール

新しい機能を追加する場合：

1. \docs/function-specification.md\ に仕様を記入
2. \src/\ に実装
3. \	ests/\ にテストコードを追加
4. \git commit\ でコミット

詳細は \docs/development-guidelines.md\ を参照。

## サポート

問題が発生した場合は、GitHub Issues で報告してください：
https://github.com/nario0715masa0619-create/ebay-research-edge/issues

---

**Last Updated**: 2026-04-23
