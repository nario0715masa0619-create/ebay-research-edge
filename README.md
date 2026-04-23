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
│   ├── fetcher/             # データ取得層
│   ├── normalizer/          # 正規化層
│   ├── analyzer/            # 分析層
│   ├── models/              # データモデル
│   ├── display/             # 表示層
│   └── __init__.py
├── data/
│   ├── categories/          # カテゴリ設定
│   ├── raw/                 # 生データ
│   └── processed/           # 処理済みデータ
├── docs/                    # ドキュメント
├── tests/                   # テスト
├── main.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
\\\

## MVPでやること

最初のバージョン（MVP）では、スコープを意図的に絞ります。

- **対象ジャンル**: ポケモンカード
- **海外データ**: eBay Sold
- **国内データ**: メルカリJP
- **分析期間**: 30日（＋90日を補助指標として利用）
- **出力**: CSV / テーブル表示

## 開発フェーズ

### ✅ Phase 1: スコアリング & サンプルデータ - **完了**
- ✅ スコアリングロジック実装（demand, profit, supply scores）
- ✅ サンプルデータ生成（55レコード）
- ✅ 統合テスト（正規化 → メトリクス計算 → スコアリング → CSV出力）
- ✅ すべてのテスト合格

### 🔄 Phase 2: eBay Fetcher - **進行中**
- ✅ eBay Fetcher 実装（開発モード：サンプルデータ）
- ✅ キーワードフィルタリング・除外キーワード処理
- ✅ MarketRecord 変換機能
- ✅ eBayFetcher テスト（全テスト合格）
- 🔄 Mercari Fetcher スケルトン（Phase 3 準備）
- 📋 Phase 2 統合テスト（次）
- 📋 README 更新（進行中）

**Phase 2 の現状:**
- eBay API 復旧待ち中（サポート対応中）
- つなぎ実装：サンプルデータで完全に動作確認済み
- API 復旧後：内部実装を切り替えるだけ（外部インターフェース不変）

### Phase 3: Mercari Fetcher & Dashboard - **予定**
- メルカリ データ取得実装
- Streamlit ダッシュボード構築
- Phase 2 完全統合テスト

## セットアップ

### 前提条件
- Python 3.9 以上
- pip

### インストール

\\\ash
git clone https://github.com/nario0715masa0619-create/ebay-research-edge.git
cd ebay-research-edge

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt

cp .env.example .env
# .env を編集して APIキーなどを設定
\\\

## 使用方法

### Phase 1: サンプルデータでの動作確認

\\\ash
# サンプルデータ生成
python tests/generate_sample_data.py

# 統合テスト実行
python tests/test_phase1_integration.py

# 結果確認
cat data/processed/test_phase1_candidates.csv
\\\

### Phase 2: eBay Fetcher テスト

\\\ash
# eBay Fetcher テスト実行
python tests/test_phase2_ebay_fetcher.py
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

## 開発ルール

### 📋 コード変更・新規作成時のルール

新しい関数を作成したり、既存関数を変更する場合：

1. **関数仕様書を先に書く** - \docs/function-specification.md\ に仕様を記載
2. **コードに docstring を追加** - 英語で詳細な docstring を記述
3. **仕様と実装を同期** - 変更があれば両方を更新

詳細は [開発ガイドライン](./docs/development-guidelines.md) を参照してください。

## テスト実行

\\\ash
# サンプルデータテスト
python tests/test_sample_data.py

# スコアリングロジックテスト
python tests/test_scoring_logic.py

# Phase 1 統合テスト
python tests/test_phase1_integration.py

# Phase 2 eBay Fetcher テスト
python tests/test_phase2_ebay_fetcher.py
\\\

## 今後のロードマップ

1. ✅ Phase 1: スコアリング + サンプルデータ（完了）
2. 🔄 Phase 2: eBay Fetcher + Mercari スケルトン（進行中）
3. Phase 3: Mercari Fetcher 実装 + Streamlit ダッシュボード
4. Phase 4: 複数カテゴリ対応

## 設計原則

- 完全自動化を目指さない
- 判断を速くすることを優先する
- 人間の意思決定を補強する
- 小さく作って実運用しながら改善する
- **カテゴリを動的に切り替え可能にする**

---

**最終更新**: 2026-04-22 | **Status**: Phase 2 進行中（eBay API 復旧待ち）
