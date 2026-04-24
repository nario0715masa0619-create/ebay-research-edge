# Phase 5: CSV Import & Batch Processing Guide

このドキュメントでは、**Phase 5（CSV インポート・バッチ処理）** の使用方法を詳しく説明します。

## 概要

Phase 5 では、複数の国内マーケットプレイスから CSV をインポートして、eBay データと組み合わせて分析・スコアリングできるようになりました。

**対応プラットフォーム：**
- Amazon（アマゾン）
- Yahoo Auction（ヤフオク）
- Yahoo Shopping（Yahoo ショッピング）
- Yahoo Fril（ラクマ、Yahoo フリマ）
- Rakuten（楽天）

---

## セットアップ

### 1. CSV 形式の確認

各プラットフォーム用のテンプレート CSV は、以下の場所にあります：

\\\
docs/csv_formats/
├── amazon_template.csv
├── yahoo_auction_template.csv
├── yahoo_shopping_template.csv
├── yahoo_fril_template.csv
└── rakuten_template.csv
\\\

### 2. データディレクトリの作成

バッチインポート用のディレクトリを作成します：

\\\ash
mkdir -p data/imports
mkdir -p data/imports/archive
\\\

---

## 使用方法

### 方法 1: 単一 CSV ファイルのインポート

**1 つの CSV ファイルをインポートしたい場合：**

\\\ash
python app.py --import-csv <csv-file> --source <source-name>
\\\

**例：**

\\\ash
# Amazon CSV をインポート
python app.py --import-csv data/imports/amazon_pokemon_20260424.csv --source amazon

# Yahoo Auction CSV をインポート
python app.py --import-csv data/imports/yahoo_auction_pokemon_20260424.csv --source yahoo_auction

# Yahoo Shopping CSV をインポート
python app.py --import-csv data/imports/yahoo_shopping_pokemon_20260424.csv --source yahoo_shopping

# Yahoo Fril CSV をインポート
python app.py --import-csv data/imports/yahoo_fril_pokemon_20260424.csv --source yahoo_fril

# Rakuten CSV をインポート
python app.py --import-csv data/imports/rakuten_pokemon_20260424.csv --source rakuten
\\\

**出力結果：**
- 分析結果 CSV → \data/processed/candidates_pokemon_card_<timestamp>.csv\
- ログ → コンソール出力

---

### 方法 2: バッチインポート（複数 CSV の一括処理）

**複数の CSV ファイルを一度に処理したい場合：**

#### Step 1: CSV ファイルを準備

\data/imports/\ ディレクトリに、以下の命名規則で CSV ファイルを置きます：

\\\
data/imports/
├── amazon_<name>.csv                    # Amazon 用
├── yahoo_auction_<name>.csv            # Yahoo Auction 用
├── yahoo_shopping_<name>.csv           # Yahoo Shopping 用
├── yahoo_fril_<name>.csv               # Yahoo Fril 用
├── rakuten_<name>.csv                  # Rakuten 用
└── archive/                             # 処理済みファイルの保存先
\\\

**例：**

\\\
data/imports/
├── amazon_pokemon_20260424.csv
├── amazon_anime_20260424.csv
├── yahoo_auction_pokemon_20260424.csv
├── yahoo_shopping_anime_20260424.csv
├── rakuten_pokemon_20260424.csv
└── archive/
\\\

#### Step 2: バッチインポート実行

\\\ash
# すべての CSV を処理
python app.py --batch-import

# 処理後、ファイルをアーカイブ
python app.py --batch-import --archive
\\\

**出力結果：**
- 分析結果 CSV → \data/processed/candidates_pokemon_card_<timestamp>.csv\
- アーカイブ（--archive 使用時）→ \data/imports/archive/\ 

**アーカイブファイル例：**
\\\
data/imports/archive/
├── amazon_pokemon_20260424_20260424_161549.csv
├── yahoo_auction_pokemon_20260424_20260424_161549.csv
└── ...
\\\

---

## CSV 形式の詳細

### Amazon CSV

**必須カラム：**
\\\
商品名,価格,送料,URL,販売者,入札数,終了日時
\\\

**例：**
\\\csv
商品名,価格,送料,URL,販売者,入札数,終了日時
ポケモンカード リザードン EX ホロ,2999,500,https://amazon.co.jp/example-1,Amazon,0,2026-04-24
ポケモンカード ピカチュウ プロモ,4999,500,https://amazon.co.jp/example-2,Amazon,0,2026-04-24
\\\

### Yahoo Auction CSV

**必須カラム：**
\\\
商品名,現在の価格,送料,商品URL,出品者,入札数,終了日時
\\\

**例：**
\\\csv
商品名,現在の価格,送料,商品URL,出品者,入札数,終了日時
ポケモンカード リザードン EX ホロ,2500,800,https://page.auctions.yahoo.co.jp/jp/example-1,seller-1,5,2026-04-25
ポケモンカード ピカチュウ プロモ,3800,800,https://page.auctions.yahoo.co.jp/jp/example-2,seller-2,3,2026-04-25
\\\

### Yahoo Shopping CSV

**必須カラム：**
\\\
商品名,価格,送料,商品URL,ストア名
\\\

### Yahoo Fril CSV

**必須カラム：**
\\\
商品名,価格,送料,商品URL,出品者,いいね数
\\\

### Rakuten CSV

**必須カラム：**
\\\
商品名,価格,送料,商品URL,ショップ名,評価
\\\

---

## スコアリング結果の解釈

### Decision Status（判定ステータス）

バッチインポート後の CSV には、以下のステータスが付与されます：

| ステータス | 意味 | スコア範囲 | 推奨アクション |
|-----------|------|-----------|--------------|
| **list_candidate** | 仕入れ候補 | 70+ | 仕入れを検討すべき商品 |
| **hold** | 保留中 | 50-69 | データを集めてから判断 |
| **skip** | スキップ | <50 | 仕入れ対象外 |

### データソース（data_source）

結果 CSV の data_source カラムは、どのデータを組み合わせて分析したかを示します：

- **multi-source (ebay + amazon)**：eBay + Amazon データの組み合わせ
- **domestic-only (amazon)**：Amazon データのみ

#### 注：スコアが低い場合

Amazon のみのデータの場合、スコアは 50.0（skip）となります。これは、**eBay データとの価格比較がないため**です。

**改善方法：**
1. eBay API が復活するまで待つ
2. 複数の国内プラットフォーム CSV を組み合わせて分析
3. 手動で eBay の相場を調べて追加分析

---

## ワークフロー例

### 例：毎週日曜日に複数プラットフォームから仕入れ候補を探す

#### 準備（1 回目のみ）

\\\ash
mkdir -p data/imports/archive
\\\

#### 毎週のワークフロー

1. **Amazon、Yahoo、Rakuten から CSV をダウンロード**
   - 各プラットフォームの検索結果を CSV エクスポート
   - data/imports/ に配置

2. **バッチインポート実行**
   \\\ash
   python app.py --batch-import --archive
   \\\

3. **結果を確認**
   - \data/processed/candidates_pokemon_card_<timestamp>.csv\ を開く
   - \list_candidate\ ステータスの商品をチェック

4. **仕入れ判断**
   - スコアが高い商品を優先的に調査
   - 利益率が見合うか確認

5. **ファイル整理**
   - 処理済みファイルは自動的に \data/imports/archive/\ に移動

---

## トラブルシューティング

### Q1: エラー「CSV file not found」が出る

**原因：** ファイルパスが間違っている、またはファイルが存在しない

**解決策：**
\\\ash
# ファイルの存在確認
ls -la data/imports/

# ファイル名に日本語が含まれている場合は、UTF-8 エンコーディングで保存されていることを確認
\\\

### Q2: 「Candidates scored: 0」と表示される

**原因：** CSV データと eBay データのマッチングに失敗している、または eBay データがない

**解決策：**
1. CSV の商品名が正規化されているか確認
2. 複数の CSV を組み合わせてみる
3. \pp.py\ の正規化ロジックをカスタマイズ

### Q3: バッチ処理が遅い

**原因：** ファイルが多い、またはレコード数が多い

**解決策：**
1. CSV ファイルを複数に分割
2. キーワードごとに処理を分ける
3. \--limit\ パラメータを減らす（eBay フェッチの件数削減）

---

## 高度な使用方法

### カスタム CSV 形式への対応

\src/utils/csv_importer.py\ の各 parser を編集することで、カスタム CSV 形式に対応できます。

例：カラム名が異なる場合

\\\python
# src/utils/csv_importer.py の _parse_amazon_csv を編集
def _parse_amazon_csv(self, file_path: str) -> List[Dict]:
    listings = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # カラム名をマッピング
            listings.append({
                'title': row['Item Name'],  # カスタムカラム名
                'price': row['Price'],
                'shipping': row['Shipping Cost'],
                'url': row['Product Link'],
            })
    return listings
\\\

### スコアリングロジックのカスタマイズ

\pp.py\ の \_process_and_score_records\ 関数でスコアリングロジックを調整できます。

---

## 参考資料

- **app.py**：メインエントリーポイント
- **src/utils/csv_importer.py**：CSV パーサー
- **src/utils/batch_processor.py**：バッチ処理エンジン
- **docs/csv_formats/**：CSV テンプレート

---

## サポート

問題が発生した場合は、以下をチェックしてください：

1. ログ出力を確認（INFO レベルのメッセージ）
2. CSV ファイルの形式が正しいか確認
3. GitHub Issues で類似の問題を検索

