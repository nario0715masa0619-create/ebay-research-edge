# eBay-Research-Edge

日本国内調達を前提に、eBay Sold と国内価格を比較し、LIST候補を数値ベースで抽出する日本人セラー向けリサーチ支援ツールです。

## 概要

eBay-Research-Edge は、次のような課題を解決することを狙ったツールです。

- eBay の Sold 実績確認に時間がかかる
- 国内価格との比較を毎回手作業で行っている
- 「売れそう」「利益が出そう」という判断が感覚に寄りがち
- LIST候補の優先順位付けが属人的になりやすい

このツールは、eBay Sold と国内プラットフォーム（メルカリ / ヤフオク 等）の価格データを集計し、**売れ行き・価格帯・国内外価格差・概算粗利率**といった指標から LIST候補を自動スコアリングすることを目指します。

## 目的

- 日本国内で調達可能な商品について、eBay 側の需要と国内側の供給状況を比較し、**「どの商品を優先的に仕入れて、LIST候補にするか」を数値ベースで判断できるようにすること。**
- 手作業中心のリサーチを「感覚」から「データ＋感覚」のハイブリッドに移行させること。

## ターゲットユーザー

- 日本国内から eBay に出品するセラー
- 国内仕入れ → eBay 販売の価格差を狙う個人・小規模事業者
- 完全自動化ではなく、**半自動で候補抽出と判断支援**を求めている人

## プロジェクト構成

\\\
eBay-Research-Edge/
├── src/
│   ├── config/              # 設定管理
│   │   ├── config.py
│   │   └── __init__.py
│   ├── fetcher/             # データ取得層
│   │   ├── ebay_fetcher.py
│   │   └── __init__.py
│   ├── normalizer/          # 正規化層
│   │   ├── normalizer.py
│   │   └── __init__.py
│   ├── analyzer/            # 分析層
│   │   ├── analyzer.py
│   │   └── __init__.py
│   ├── models/              # データモデル
│   │   ├── data_models.py
│   │   └── __init__.py
│   ├── display/             # 表示層
│   │   ├── csv_output.py
│   │   └── __init__.py
│   └── __init__.py
├── data/
│   ├── categories/          # カテゴリ設定
│   │   └── pokemon_card.yaml
│   ├── raw/                 # 生データ
│   └── processed/           # 処理済みデータ
├── docs/                    # ドキュメント
│   ├── basic-design.md
│   ├── requirements.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── implementation-plan.md
│   ├── acceptance-criteria.md
│   ├── scoring-rules.md
│   ├── sample-output.md
│   ├── open-questions.md
│   ├── genspark-implementation-prompt.md
│   ├── function-specification.md
│   └── development-guidelines.md
├── tests/                   # テスト
│   ├── sample_data_generator.py
│   ├── test_sample_data.py
│   ├── test_scoring_logic.py
│   ├── test_phase1_integration.py
│   └── generate_sample_data.py
├── main.py                  # メインエントリーポイント
├── pyproject.toml           # プロジェクト設定
├── requirements.txt         # 依存パッケージ
├── .env.example             # 環境変数テンプレート
├── .gitignore               # Git除外設定
└── README.md                # このファイル
\\\

## MVPでやること

最初のバージョン（MVP）では、スコープを意図的に絞ります。

- **対象ジャンル**: ポケモンカード
- **海外データ**: eBay Sold
- **国内データ**: メルカリJP
- **分析期間**: 30日（＋90日を補助指標として利用）
- **出力**: CSV / テーブル表示

## 想定する主な指標

- \sold_30d\ / \sold_90d\：直近30日 / 90日の Sold 件数
- \ctive_count\：現在の出品数
- \median_price_usd\：eBay Sold 中央値
- \vg_price_usd\：eBay Sold 平均値
- \min_price_usd\ / \max_price_usd\：価格レンジ
- \domestic_min_price_jpy\：国内最安価格
- \domestic_median_price_jpy\：国内中央値
- \stimated_profit_jpy\ / \stimated_profit_rate\：概算利益額 / 概算粗利率
- \str\：Sell Through Rate（売れ行きの強さ）
- \candidate_score\：LIST候補判定のための総合スコア

## システム構成

本システムは以下の4層構造とします。

1. **取得層** (fetcher): eBay, 国内サイトからデータ取得
2. **整形層** (normalizer): タイトル正規化、価格統一
3. **分析層** (analyzer): 指標計算、スコアリング
4. **表示層** (display): CSV出力、ダッシュボード表示

## 開発フェーズ

### ✅ Phase 1: eBay Sold MVP - **完了**
- ✅ eBay Sold データ取得スケルトン
- ✅ 基本集計（sold_30d, sold_90d）
- ✅ CSV出力
- ✅ スコアリングロジック実装（demand, profit, supply）
- ✅ サンプルデータ生成（55レコード）
- ✅ 統合テスト（正規化 → メトリクス計算 → スコアリング → CSV出力）

**Phase 1 の成果:**
- サンプルデータから最終的なCSV出力までの完全なパイプラインが動作確認済み
- 3つのポケモンカード商品について、スコア計算（score=76.0, status=hold）が正常に実行される
- すべての単体テスト＋統合テスト合格

### Phase 2: 国内価格比較 - **予定**
- 国内1サイト対応（メルカリ）
- 国内外価格差・粗利率算出
- candidate_score 実装（✅完了）
- decision_status 判定（✅完了）

### Phase 3: ダッシュボード化 - **予定**
- 検索UI
- サマリーカード
- 候補一覧テーブル
- 詳細パネル

## セットアップ

### 前提条件
- Python 3.9 以上
- pip または poetry

### インストール

\\\ash
# 1. リポジトリをクローン
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge

# 2. 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. 環境変数を設定
cp .env.example .env
# .env を編集して、APIキーなどを設定
\\\

## 使用方法

### Phase 1 MVP (サンプルデータでの動作確認)

\\\ash
# サンプルデータ生成
python tests/generate_sample_data.py

# 統合テスト実行（正規化 → メトリクス → スコアリング → CSV出力）
python tests/test_phase1_integration.py

# 結果確認
cat data/processed/test_phase1_candidates.csv
\\\

## ドキュメント

- [基本設計書](./docs/basic-design.md)
- [要件定義](./docs/requirements.md)
- [アーキテクチャ](./docs/architecture.md)
- [データモデル](./docs/data-model.md)
- [実装計画](./docs/implementation-plan.md)
- [採択基準](./docs/acceptance-criteria.md)
- [スコアリングルール](./docs/scoring-rules.md)
- [出力サンプル](./docs/sample-output.md)
- [未解決質問](./docs/open-questions.md)
- **[関数仕様書](./docs/function-specification.md)** ← 開発時の参照
- **[開発ガイドライン](./docs/development-guidelines.md)** ← コード作成時のルール

## スコアリングロジック

\\\
candidate_score = 0.4 * demand_score + 0.4 * profit_score + 0.2 * supply_score
\\\

### 判定基準
- **80点以上**: list_candidate（LIST推奨）
- **60〜79点**: hold（保留・後で検討）
- **59点以下**: skip（見送り）

### スコア計算詳細

**demand_score（需要評価）:**
- sold_30d: 0-1件(0) → 2-3件(20) → 4-5件(40) → 6-7件(60) → 8件以上(100)
- STR bonus: <20%(0) → 20-40%(+10) → 40-60%(+20) → >60%(+30)
- 90日一貫性bonus: sold_90d > sold_30d * 2.5 なら +10

**profit_score（利益評価）:**
- profit_rate: <5%(0) → 5-10%(30) → 10-15%(50) → 15-20%(70) → 20%以上(100)
- amount_bonus: <500JPY(0) → 500-1000(+10) → 1000-2000(+20) → 2000以上(+30)

**supply_score（供給・競争評価）:**
- active_count: >50(0) → 30-50(20) → 15-30(40) → 5-15(60) → <5(100)

## 開発ルール

### 📋 コード変更・新規作成時のルール

**重要**: 新しい関数を作成したり、既存関数を変更する場合は、必ず以下の手順に従ってください。

#### Step 1: 関数仕様書を先に書く
\docs/function-specification.md\ に関数の仕様を記載します。

#### Step 2: コードに docstring を追加
ソースコードに英語で詳細な docstring を書きます。

#### Step 3: 仕様と実装を同期させる
変更があれば、両方を更新します。

詳細は [開発ガイドライン](./docs/development-guidelines.md) を参照してください。

## 設計原則

- 完全自動化を目指さない
- 判断を速くすることを優先する
- 人間の意思決定を補強する
- 小さく作って実運用しながら改善する
- **カテゴリを動的に切り替え可能にする**

## テスト実行

\\\ash
# サンプルデータ生成テスト
python tests/test_sample_data.py

# スコアリングロジックテスト
python tests/test_scoring_logic.py

# 統合テスト（完全パイプライン）
python tests/test_phase1_integration.py
\\\

## 今後のロードマップ

1. ✅ Phase 1: サンプルデータ + スコアリング（完了）
2. Phase 2: eBay API 実装 + メルカリ取得実装
3. Phase 3: Streamlit ダッシュボード構築
4. Phase 4: 複数カテゴリ対応への拡張

---

**最終更新**: 2026-04-22 | **Status**: Phase 1完了、Phase 2準備中
