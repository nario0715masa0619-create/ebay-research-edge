# docs/function-specification.md

# eBay-Research-Edge 関数仕様書

## 目次
1. [config.py](#1-configpy)
2. [data_models.py](#2-data_modelspy)
3. [analyzer.py](#3-analyzerpy)
4. [normalizer.py](#4-normalizerpy)
5. [ebay_fetcher.py](#5-ebay_fetcherpy)
6. [csv_output.py](#6-csv_outputpy)
7. [グローバル変数](#7-グローバル変数)

---

## 1. config.py

### クラス: Config

**目的**: プロジェクト全体の設定を一元管理し、カテゴリ動的切り替えを実現する。

#### グローバル変数
- \config\: Config インスタンス（モジュール内で唯一のシングルトン）

#### メソッド

##### \__init__()\
- **説明**: 設定オブジェクトを初期化
- **パラメータ**: なし
- **戻り値**: なし
- **動作**:
  - プロジェクトルートパスを取得
  - 環境変数 \ACTIVE_CATEGORY\ から対象カテゴリを読み込み（デフォルト: pokemon_card）
  - カテゴリ設定YAMLを読み込む
- **例外**: FileNotFoundError (カテゴリYAMLが見つからない場合)

##### \_load_category_config()\
- **説明**: カテゴリ設定YAMLファイルを読み込む
- **パラメータ**: なし
- **戻り値**: Dict[str, Any] - カテゴリ設定辞書
- **動作**:
  - \data/categories/{active_category}.yaml\ を読み込む
  - YAML をパースして辞書として返す
- **例外**: FileNotFoundError, yaml.YAMLError

#### プロパティ（読み取り専用）

##### \category_name\
- **説明**: カテゴリの英語名
- **戻り値**: str（例: "Pokemon Card"）

##### \category_name_ja\
- **説明**: カテゴリの日本語名
- **戻り値**: str（例: "ポケモンカード"）

##### \bay_keywords\
- **説明**: eBay検索時の含有キーワード
- **戻り値**: List[str]

##### \bay_exclude_keywords\
- **説明**: eBay検索時の除外キーワード
- **戻り値**: List[str]

##### \mercari_keywords\
- **説明**: メルカリ検索時の含有キーワード
- **戻り値**: List[str]

##### \bay_fee_rate\
- **説明**: eBay手数料率
- **戻り値**: float（例: 0.129）

##### \shipping_cost_estimate_usd\
- **説明**: 推定国内→eBay送料（ドル）
- **戻り値**: float

##### \mercari_fee_rate\
- **説明**: メルカリ手数料率
- **戻り値**: float（例: 0.10）

##### \scoring_config\
- **説明**: スコアリング関連の設定
- **戻り値**: Dict[str, Any]

##### \data_dir\, \aw_data_dir\, \processed_data_dir\
- **説明**: 各データディレクトリのパス
- **戻り値**: Path

---

## 2. data_models.py

### Enum: SourceSite
- **説明**: データソースの種類を定義
- **値**: EBAY, MERCARI, YAHOO_AUCTION

### Enum: DecisionStatus
- **説明**: 候補判定ステータスを定義
- **値**: LIST_CANDIDATE, HOLD, SKIP

### Dataclass: Item

**目的**: 商品マスタ情報を保持

| フィールド | 型 | 説明 |
|-----------|------|------|
| item_id | str | 商品ID（ユニーク） |
| normalized_name | str | 正規化済み商品名 |
| franchise | Optional[str] | 作品名（例: Pokemon） |
| character | Optional[str] | キャラクター名 |
| category | str | カテゴリ（例: pokemon_card） |
| subcategory | Optional[str] | 小分類 |
| created_at | datetime | 作成日時 |
| updated_at | datetime | 更新日時 |

### Dataclass: MarketRecord

**目的**: 国内外の取得レコード（単一の出品データ）を保持

| フィールド | 型 | 説明 |
|-----------|------|------|
| record_id | str | レコードID（ユニーク） |
| item_id | str | 商品ID（Item への外部キー） |
| source_site | SourceSite | データソース |
| search_keyword | str | 検索時のキーワード |
| original_title | str | 元のタイトル（正規化前） |
| normalized_title | str | 正規化後のタイトル |
| price | float | 本体価格 |
| shipping | float | 送料 |
| currency | str | 通貨（USD / JPY） |
| total_price | float | price + shipping |
| sold_flag | bool | Sold済みか |
| active_flag | bool | 出品中か |
| sold_date | Optional[datetime] | 販売日時 |
| listing_url | Optional[str] | 商品URL |
| fetched_at | datetime | 取得日時 |

### Dataclass: ScoredCandidate

**目的**: 集計結果と判定ステータスを保持（商品ごとの最終判定結果）

| フィールド | 型 | 説明 |
|-----------|------|------|
| candidate_id | str | 候補ID（ユニーク） |
| item_id | str | 商品ID |
| sold_30d | int | 30日 Sold 件数 |
| sold_90d | int | 90日 Sold 件数 |
| active_count | int | 現在の出品数 |
| median_price_usd | float | eBay Sold 中央値（ドル） |
| avg_price_usd | float | eBay Sold 平均値（ドル） |
| min_price_usd | float | eBay Sold 最安値（ドル） |
| max_price_usd | float | eBay Sold 最高値（ドル） |
| domestic_min_price_jpy | float | 国内最安値（円） |
| domestic_median_price_jpy | float | 国内中央値（円） |
| estimated_profit_jpy | float | 概算利益額（円） |
| estimated_profit_rate | float | 概算粗利率（%） |
| str | float | Sell Through Rate（%） |
| candidate_score | float | 総合スコア（0-100） |
| decision_status | DecisionStatus | 判定ステータス |
| calculated_at | datetime | 計算日時 |

---

## 3. analyzer.py

### クラス: Analyzer

**目的**: MarketRecord データから指標を計算し、候補スコアを算出する。

#### グローバル変数
- \logger\: logging.Logger - ログ出力オブジェクト

#### メソッド

##### \__init__()\
- **説明**: Analyzer を初期化
- **パラメータ**: なし
- **動作**: Config と scoring_config を読み込む

##### \calculate_sold_counts(records: List[MarketRecord], days_list: List[int] = [30, 90])\
- **説明**: 指定された日数内の Sold 件数を計算
- **パラメータ**:
  - \ecords\: MarketRecord リスト
  - \days_list\: 計算対象の日数（デフォルト: [30, 90]）
- **戻り値**: Dict[int, int]（{日数: Sold件数}）
- **動作**:
  - 現在日時を取得
  - 各 days について、threshold を計算（now - timedelta(days)）
  - records から sold_flag=True かつ sold_date >= threshold を満たす件数をカウント
- **例**:
  \\\python
  result = analyzer.calculate_sold_counts(records, [30, 90])
  # {30: 5, 90: 12}
  \\\

##### \calculate_price_stats(records: List[MarketRecord])\
- **説明**: 価格の統計値（中央値、平均値、最小値、最大値）を計算
- **パラメータ**: \ecords\: MarketRecord リスト
- **戻り値**: Dict[str, float]（{min, max, avg, median}）
- **動作**:
  - records から total_price > 0 のものを抽出
  - 空の場合はすべて 0.0 を返す
  - statistics モジュールで median / mean を計算
- **例**:
  \\\python
  stats = analyzer.calculate_price_stats(records)
  # {min: 29.99, max: 59.99, avg: 45.2, median: 48.5}
  \\\

##### \calculate_str(sold_count: int, active_count: int)\
- **説明**: Sell Through Rate を計算
- **パラメータ**:
  - \sold_count\: Sold 件数
  - \ctive_count\: 現在の出品数
- **戻り値**: float (%)
- **公式**: STR = sold / (sold + active) * 100
- **動作**:
  - sold_count + active_count == 0 の場合は 0.0 を返す
  - そうでない場合は計算式を適用、小数点第2位で四捨五入
- **例**:
  \\\python
  str_value = analyzer.calculate_str(5, 3)
  # 62.5
  \\\

##### \calculate_estimated_profit(ebay_price_usd: float, domestic_cost_jpy: float, exchange_rate: float = 150.0)\
- **説明**: 概算利益と粗利率を計算
- **パラメータ**:
  - \bay_price_usd\: eBay売却価格（ドル）
  - \domestic_cost_jpy\: 国内仕入れ価格（円）
  - \xchange_rate\: 為替レート（円/ドル、デフォルト: 150.0）
- **戻り値**: Dict[str, float]（{profit_jpy, profit_rate}）
- **動作**:
  1. ebay_price_jpy = ebay_price_usd * exchange_rate
  2. ebay_fee = ebay_price_jpy * config.ebay_fee_rate
  3. shipping_cost_jpy = config.shipping_cost_estimate_usd * exchange_rate
  4. estimated_profit_jpy = ebay_price_jpy - ebay_fee - shipping_cost_jpy - domestic_cost_jpy
  5. profit_rate = (estimated_profit_jpy / ebay_price_jpy) * 100（ebay_price_jpy > 0 の場合）
- **例**:
  \\\python
  profit = analyzer.calculate_estimated_profit(50.0, 3000.0)
  # {profit_jpy: 2350, profit_rate: 31.33}
  \\\

##### \calculate_demand_score(sold_30d: int, sold_90d: int, str_value: float)\
- **説明**: 需要の強さを0-100のスコアで評価
- **パラメータ**:
  - \sold_30d\: 30日 Sold 件数
  - \sold_90d\: 90日 Sold 件数
  - \str_value\: Sell Through Rate (%)
- **戻り値**: float (0-100)
- **動作**: (実装予定)
  - 30日 Sold 件数が多いほど加点
  - 90日 Sold 件数が多いほど加点
  - STR が高いほど加点
- **TODO**: 具体的な重み付けロジックを実装

##### \calculate_profit_score(profit_rate: float, profit_jpy: float)\
- **説明**: 利益の出やすさを0-100のスコアで評価
- **パラメータ**:
  - \profit_rate\: 粗利率 (%)
  - \profit_jpy\: 概算利益額（円）
- **戻り値**: float (0-100)
- **動作**: (実装予定)
  - 粗利率が高いほど加点
  - 利益額が高いほど加点
- **TODO**: 具体的な重み付けロジックを実装

##### \calculate_supply_score(active_count: int)\
- **説明**: 競合の強さ・供給過多リスクを0-100のスコアで評価
- **パラメータ**: \ctive_count\: 現在の出品数
- **戻り値**: float (0-100)
- **動作**: (実装予定)
  - active_count が少ないほど加点（競合が少ない = 売れやすい）
- **TODO**: 具体的なしきい値を決定

##### \calculate_candidate_score(demand_score: float, profit_score: float, supply_score: float)\
- **説明**: 総合スコアを計算
- **パラメータ**: 各サブスコア
- **戻り値**: float (0-100)
- **公式**:
  \\\
  candidate_score = 0.4 * demand_score + 0.4 * profit_score + 0.2 * supply_score
  \\\
- **動作**:
  - scoring_config から重みを取得
  - 加重平均を計算、小数点第2位で四捨五入
- **例**:
  \\\python
  score = analyzer.calculate_candidate_score(85.0, 75.0, 80.0)
  # 80.0
  \\\

##### \determine_decision_status(score: float)\
- **説明**: 総合スコアから判定ステータスを決定
- **パラメータ**: \score\: 総合スコア
- **戻り値**: DecisionStatus
- **動作**:
  - score >= 80.0 → LIST_CANDIDATE
  - 60.0 <= score < 80.0 → HOLD
  - score < 60.0 → SKIP
  - しきい値は scoring_config から取得可能
- **例**:
  \\\python
  status = analyzer.determine_decision_status(85.0)
  # DecisionStatus.LIST_CANDIDATE
  \\\

---

## 4. normalizer.py

### クラス: Normalizer

**目的**: MarketRecord のタイトルと情報を正規化し、検索精度を向上させる。

#### グローバル変数
- \logger\: logging.Logger - ログ出力オブジェクト

#### メソッド

##### \__init__()\
- **説明**: Normalizer を初期化
- **パラメータ**: なし
- **動作**:
  - Config を読み込む
  - カテゴリ設定から normalization_rules を取得

##### \
ormalize_title(title: str)\
- **説明**: 商品タイトルを正規化
- **パラメータ**: \	itle\: 元のタイトル
- **戻り値**: str - 正規化済みタイトル
- **動作**:
  1. normalization_rules のパターンを順番に適用（正規表現で置換）
  2. 複数連続スペースを単一スペースに統一
  3. 先頭・末尾のスペースを除去
- **例**:
  \\\python
  normalized = normalizer.normalize_title("Pokemon Card (Japanese) - Charizard")
  # "Pokemon Card - Charizard"
  \\\

##### \
ormalize_records(records: List[MarketRecord])\
- **説明**: MarketRecord リストのタイトルを一括正規化
- **パラメータ**: \ecords\: MarketRecord リスト
- **戻り値**: List[MarketRecord] - 正規化済みレコード
- **動作**:
  - 各 record の original_title に normalize_title() を適用
  - normalized_title フィールドを更新
  - ログに処理件数を出力

##### \xtract_keywords(title: str)\
- **説明**: タイトルから重要な情報を抽出
- **パラメータ**: \	itle\: 商品タイトル
- **戻り値**: dict - 抽出された情報
- **動作**: (実装予定)
  - カテゴリ固有のパターンマッチング
  - franchise, character など を自動抽出
- **例**:
  \\\python
  keywords = normalizer.extract_keywords("Pokemon Card Charizard EX Holo")
  # {franchise: "Pokemon", character: "Charizard", rarity: "EX"}
  \\\

---

## 5. ebay_fetcher.py

### クラス: eBayFetcher

**目的**: eBay Sold データを取得し、MarketRecord に変換する。

#### グローバル変数
- \logger\: logging.Logger - ログ出力オブジェクト

#### メソッド

##### \__init__()\
- **説明**: eBayFetcher を初期化
- **パラメータ**: なし
- **動作**:
  - eBay API ベースURL を設定
  - API キーを環境変数から取得（TODO）
  - Config を読み込む

##### \etch_sold_listings(keyword: str, limit: int = 100)\
- **説明**: eBay Sold リスティングを取得
- **パラメータ**:
  - \keyword\: 検索キーワード
  - \limit\: 取得件数上限（デフォルト: 100）
- **戻り値**: List[Dict[str, Any]] - 取得したリスティングデータ
- **動作**: (実装予定)
  1. eBay API に検索リクエストを送信
  2. Sold フィルタを適用
  3. exclude_keywords に該当するアイテムを除外
  4. 生データを保存（data/raw/ に JSON で保存）
  5. リスティングリストを返す
- **例外**: requests.RequestException, APIエラー
- **注**: 現在は実装スケルトンのみ

##### \convert_to_market_records(raw_listings: List[Dict])\
- **説明**: eBay リスティングを MarketRecord に変換
- **パラメータ**: \aw_listings\: eBay API から取得したリスティングデータ
- **戻り値**: List[MarketRecord]
- **動作**: (実装予定)
  1. 各リスティングから item_id を生成
  2. 通貨を USD に統一
  3. 送料を処理
  4. MarketRecord インスタンスを生成
  5. リストを返す
- **注**: 現在は実装スケルトンのみ

---

## 6. csv_output.py

### クラス: CSVOutput

**目的**: データを CSV 形式で出力し、外部分析やバックアップに対応する。

#### グローバル変数
- \logger\: logging.Logger - ログ出力オブジェクト

#### メソッド

##### \__init__()\
- **説明**: CSVOutput を初期化
- **パラメータ**: なし
- **動作**:
  - Config を読み込む
  - output_dir (data/processed/) を取得
  - ディレクトリが存在しない場合は作成

##### \xport_candidates(candidates: List[ScoredCandidate], filename: str = None)\
- **説明**: 候補一覧を CSV ファイルに出力
- **パラメータ**:
  - \candidates\: ScoredCandidate リスト
  - \ilename\: 出力ファイル名（Noneの場合は自動生成 \candidates_{category}_{timestamp}.csv\）
- **戻り値**: Path - 出力ファイルパス
- **動作**:
  1. ファイル名が未指定の場合はタイムスタンプで自動生成
  2. output_dir 内に CSV ファイルを作成
  3. fieldnames を定義
  4. ヘッダーと各 candidate をリストアップ
  5. decision_status を文字列に変換
- **例外**: IOError, csv.Error
- **例**:
  \\\python
  output_path = csv_output.export_candidates(candidates)
  # data/processed/candidates_pokemon_card_20240422_153000.csv
  \\\

##### \xport_raw_data(data: List[dict], filename: str)\
- **説明**: 生データ（辞書リスト）を CSV ファイルに出力
- **パラメータ**:
  - \data\: 出力対象のデータ（辞書リスト）
  - \ilename\: 出力ファイル名
- **戻り値**: Path - 出力ファイルパス
- **動作**:
  1. data が空の場合はログ警告を出力
  2. data[0].keys() から fieldnames を取得
  3. output_dir 内に CSV ファイルを作成
  4. ヘッダーと各行をリストアップ
- **例外**: IOError, csv.Error
- **例**:
  \\\python
  output_path = csv_output.export_raw_data(raw_listings, "ebay_raw_pokemon.csv")
  # data/processed/ebay_raw_pokemon.csv
  \\\

---

## 7. グローバル変数

### config.py
- **変数**: \config\
- **型**: Config
- **説明**: プロジェクト全体で参照されるシングルトン設定オブジェクト
- **アクセス**: \rom src.config.config import config\
- **用途**: 他モジュールで \config.ebay_keywords\ など でカテゴリ情報にアクセス

### analyzer.py, normalizer.py, ebay_fetcher.py, csv_output.py
- **変数**: \logger\
- **型**: logging.Logger
- **説明**: 各モジュール内のログ出力用オブジェクト
- **生成**: \logger = logging.getLogger(__name__)\
- **用途**: logger.info(), logger.debug(), logger.error() でログ出力

---

## 今後の実装ロードマップ

### TODO リスト（analyzer.py）
- [ ] calculate_demand_score() の詳細ロジック実装
- [ ] calculate_profit_score() の詳細ロジック実装
- [ ] calculate_supply_score() の詳細ロジック実装
- [ ] 単体テストの追加

### TODO リスト（normalizer.py）
- [ ] extract_keywords() の実装
- [ ] ポケモンカード固有のパターン定義
- [ ] 単体テストの追加

### TODO リスト（ebay_fetcher.py）
- [ ] eBay API キー管理の実装
- [ ] fetch_sold_listings() の API 呼び出し実装
- [ ] convert_to_market_records() の実装
- [ ] エラーハンドリングの強化
- [ ] 単体テストの追加

### TODO リスト（全般）
- [ ] 統合テストの作成
- [ ] ドキュメンテーション文字列（docstring）の充実
- [ ] エラーログとログレベルの最適化
## Scoring Implementation Details

### Demand Score Calculation

The demand_score evaluates market demand based on sales velocity and sell-through rate.

**Scoring Tiers (30-day sold count):**
- 0-1 sold: 0 points
- 2-3 sold: 20 points
- 4-5 sold: 40 points
- 6-7 sold: 60 points
- 8+ sold: 100 points

**STR Bonus:**
- STR < 20%: 0 bonus
- STR 20-40%: +10 points
- STR 40-60%: +20 points
- STR > 60%: +30 points

**90-day consideration:**
- If sold_90d significantly higher than sold_30d * 3: +10 bonus
- (Indicates sustained demand)

**Formula:**
\\\
base_score = tier_points(sold_30d)
str_bonus = calculate_str_bonus(str)
consistency_bonus = check_90d_consistency(sold_30d, sold_90d)
demand_score = min(100, base_score + str_bonus + consistency_bonus)
\\\

### Profit Score Calculation

The profit_score evaluates profitability based on rate and absolute amount.

**Profit Rate Tiers:**
- < 5%: 0 points
- 5-10%: 30 points
- 10-15%: 50 points
- 15-20%: 70 points
- > 20%: 100 points

**Profit Amount Bonus (in JPY):**
- < 500: 0 bonus
- 500-1000: +10 points
- 1000-2000: +20 points
- > 2000: +30 points

**Formula:**
\\\
rate_score = tier_points(profit_rate)
amount_bonus = calculate_amount_bonus(profit_jpy)
profit_score = min(100, rate_score + amount_bonus)
\\\

### Supply Score Calculation

The supply_score evaluates competitive intensity based on active listings.

**Active Count Tiers:**
- > 50: 0 points
- 30-50: 20 points
- 15-30: 40 points
- 5-15: 60 points
- < 5: 100 points

**Formula:**
\\\
supply_score = tier_points(active_count)
\\\

Lower supply (fewer competitors) = higher score = more favorable.
