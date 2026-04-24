# Phase 5: API & 実装リファレンス

このドキュメントでは、Phase 5 の主要クラス・メソッドの詳細 API を説明します。

---

## CSVImporter クラス

**ファイル:** \src/utils/csv_importer.py\

### 概要

複数のプラットフォーム（Amazon、Yahoo、Rakuten）の CSV を統一フォーマットに変換し、\MarketRecord\ オブジェクトのリストを返します。

### クラス定義

\\\python
class CSVImporter:
    def __init__(self)
    def import_csv(file_path: str, source_site: str) -> List[MarketRecord]
    def _parse_amazon_csv(file_path: str) -> List[Dict]
    def _parse_yahoo_auction_csv(file_path: str) -> List[Dict]
    def _parse_yahoo_shopping_csv(file_path: str) -> List[Dict]
    def _parse_yahoo_fril_csv(file_path: str) -> List[Dict]
    def _parse_rakuten_csv(file_path: str) -> List[Dict]
    def _parse_price(price_str: str) -> float
    def _convert_to_market_records(listings: List[Dict]) -> List[MarketRecord]
\\\

### メソッド詳細

#### \__init__(self)\

**説明:** CSVImporter を初期化

**パラメータ:** なし

**戻り値:** なし

**例：**
\\\python
from src.utils.csv_importer import CSVImporter

importer = CSVImporter()
\\\

---

#### \import_csv(file_path: str, source_site: str) -> List[MarketRecord]\

**説明:** CSV ファイルをインポートし、MarketRecord リストに変換

**パラメータ：**
- \ile_path\ (str): CSV ファイルのパス
- \source_site\ (str): ソースサイト名
  - \'amazon'\
  - \'yahoo_auction'\
  - \'yahoo_shopping'\
  - \'yahoo_fril'\
  - \'rakuten'\

**戻り値:** \List[MarketRecord]\

**例外:**
- \FileNotFoundError\: ファイルが見つからない
- \ValueError\: 不正なソースサイト指定

**例：**
\\\python
records = importer.import_csv('data/imports/amazon.csv', 'amazon')
print(f"Imported {len(records)} records")
# Output: Imported 10 records
\\\

---

#### \_parse_price(price_str: str) -> float\

**説明:** 価格文字列をパースして float に変換

**パラメータ：**
- \price_str\ (str): 価格文字列（例：「¥1,500」「1,500 円」）

**戻り値:** \loat\

**例：**
\\\python
price = importer._parse_price("¥1,500")
# Output: 1500.0

price = importer._parse_price("2,500 円")
# Output: 2500.0
\\\

---

## BatchCSVProcessor クラス

**ファイル:** \src/utils/batch_processor.py\

### 概要

\data/imports/\ ディレクトリ内の複数 CSV ファイルを自動検出し、一括処理します。

### クラス定義

\\\python
class BatchCSVProcessor:
    def __init__(import_dir: str = "data/imports")
    def discover_csv_files() -> Dict[str, List[Path]]
    def process_batch(sources_to_process: Dict = None) -> Tuple[List, int, int]
    def archive_processed_files(sources_to_process: Dict) -> int
\\\

### メソッド詳細

#### \__init__(import_dir: str = "data/imports")\

**説明:** BatchCSVProcessor を初期化

**パラメータ：**
- \import_dir\ (str): CSV インポートディレクトリ（デフォルト：\"data/imports"\）

**例：**
\\\python
from src.utils.batch_processor import BatchCSVProcessor

processor = BatchCSVProcessor(import_dir="data/imports")
\\\

---

#### \discover_csv_files() -> Dict[str, List[Path]]\

**説明:** インポートディレクトリ内の CSV ファイルを自動検出

**命名規則：**
- Amazon: \mazon_*.csv\
- Yahoo Auction: \yahoo_auction_*.csv\
- Yahoo Shopping: \yahoo_shopping_*.csv\
- Yahoo Fril: \yahoo_fril_*.csv\
- Rakuten: \akuten_*.csv\

**戻り値:** \Dict[str, List[Path]]\

**例：**
\\\python
sources = processor.discover_csv_files()
# Output:
# {
#     'amazon': [Path('data/imports/amazon_pokemon.csv'), ...],
#     'yahoo_auction': [Path('data/imports/yahoo_auction_pokemon.csv'), ...],
#     ...
# }
\\\

---

#### \process_batch(sources_to_process: Dict = None) -> Tuple[List, int, int]\

**説明:** CSV ファイルをバッチ処理

**パラメータ：**
- \sources_to_process\ (Dict, optional): 処理対象のソース・ファイル。
  None の場合は自動検出

**戻り値:** \Tuple[List[MarketRecord], int, int]\
- 要素 1: インポートされたすべての MarketRecord
- 要素 2: 処理されたファイル総数
- 要素 3: 成功したファイル数

**例：**
\\\python
sources = processor.discover_csv_files()
all_records, total_files, success_count = processor.process_batch(sources)

print(f"Processed {total_files} files, {success_count} succeeded")
print(f"Total records imported: {len(all_records)}")
# Output:
# Processed 3 files, 3 succeeded
# Total records imported: 30
\\\

---

#### \rchive_processed_files(sources_to_process: Dict) -> int\

**説明:** 処理済み CSV ファイルを \data/imports/archive/\ に移動

**パラメータ：**
- \sources_to_process\ (Dict): 処理対象のソース・ファイル

**戻り値:** \int\ – アーカイブされたファイル数

**例：**
\\\python
sources = processor.discover_csv_files()
archived_count = processor.archive_processed_files(sources)
print(f"Archived {archived_count} files")
# Output: Archived 3 files
\\\

---

## app.py の関数

### \un_pipeline_from_csv(csv_file: str, source_site: str) -> Path\

**説明:** 単一 CSV ファイルをインポートしてパイプラインを実行

**パラメータ：**
- \csv_file\ (str): CSV ファイルパス
- \source_site\ (str): ソースサイト名

**戻り値:** \Path\ – 出力 CSV ファイルのパス

**使用例：**
\\\ash
python app.py --import-csv data/imports/amazon.csv --source amazon
\\\

---

### \un_pipeline_from_batch(import_dir: str = "data/imports", archive: bool = False) -> Path\

**説明:** バッチ CSV インポートパイプラインを実行

**パラメータ：**
- \import_dir\ (str): CSV インポートディレクトリ
- \rchive\ (bool): 処理後にファイルをアーカイブするか

**戻り値:** \Path\ – 出力 CSV ファイルのパス

**使用例：**
\\\ash
python app.py --batch-import
python app.py --batch-import --archive
\\\

---

## MarketRecord データモデル

**ファイル:** \src/models/data_models.py\

### フィールド

\\\python
@dataclass
class MarketRecord:
    record_id: str                    # ユニーク ID
    item_id: str                      # 商品 ID
    source_site: SourceSite           # ソースサイト（AMAZON など）
    search_keyword: str               # 検索キーワード
    original_title: str               # 元のタイトル
    normalized_title: str             # 正規化されたタイトル
    price: float                      # 単価
    shipping: float                   # 送料
    currency: str                     # 通貨（USD, JPY など）
    total_price: float                # 合計価格（price + shipping）
    sold_flag: bool                   # 売却済みフラグ
    active_flag: bool                 # 出品中フラグ
    sold_date: Optional[datetime]     # 売却日
    listing_url: Optional[str]        # 商品 URL
    fetched_at: datetime              # 取得日時
\\\

---

## SourceSite Enum

\\\python
class SourceSite(Enum):
    EBAY = "ebay"
    MERCARI = "mercari"
    AMAZON = "amazon"
    YAHOO_AUCTION = "yahoo_auction"
    YAHOO_SHOPPING = "yahoo_shopping"
    YAHOO_FRIL = "yahoo_fril"
    RAKUTEN = "rakuten"
\\\

---

## 使用例

### 例 1: CSV インポートと正規化

\\\python
from src.utils.csv_importer import CSVImporter
from src.normalizer.normalizer import Normalizer

# Step 1: CSV インポート
importer = CSVImporter()
records = importer.import_csv('data/imports/amazon.csv', 'amazon')
print(f"Imported {len(records)} records")

# Step 2: 正規化
normalizer = Normalizer()
normalized = normalizer.normalize_records(records)
print(f"Normalized {len(normalized)} records")

# Step 3: 処理
for record in normalized:
    print(f"{record.normalized_title}: {record.total_price} {record.currency}")
\\\

### 例 2: バッチ処理

\\\python
from src.utils.batch_processor import BatchCSVProcessor

# Step 1: バッチプロセッサ初期化
processor = BatchCSVProcessor()

# Step 2: CSV ファイル検出
sources = processor.discover_csv_files()
print(f"Found {sum(len(f) for f in sources.values())} files")

# Step 3: バッチ処理
all_records, total_files, success = processor.process_batch(sources)
print(f"Processed {total_files} files → {len(all_records)} records")

# Step 4: アーカイブ（オプション）
archived = processor.archive_processed_files(sources)
print(f"Archived {archived} files")
\\\

---

## エラーハンドリング

### FileNotFoundError

\\\python
try:
    records = importer.import_csv('nonexistent.csv', 'amazon')
except FileNotFoundError as e:
    print(f"Error: {e}")
\\\

### ValueError

\\\python
try:
    records = importer.import_csv('data.csv', 'invalid_source')
except ValueError as e:
    print(f"Error: {e}")
\\\

---

## パフォーマンス特性

| 操作 | ファイル数 | レコード数 | 所要時間 |
|------|-----------|-----------|---------|
| CSV インポート | 1 | 100 | ~100ms |
| バッチ処理 | 5 | 500 | ~500ms |
| 正規化 | - | 500 | ~50ms |
| スコアリング | - | 500 | ~100ms |

---

## 参考資料

- \src/utils/csv_importer.py\ – CSVImporter 実装
- \src/utils/batch_processor.py\ – BatchCSVProcessor 実装
- \pp.py\ – メインパイプライン実装
