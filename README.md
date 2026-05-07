# eBay-Research-Edge

eBay での売上データと日本国内マーケットプレイス（Amazon、Yahoo、Rakuten など）の仕入値を比較分析し、利益機会を自動検出するリサーチツール。

**Status:** Phase 5 完成（CSV インポート・バッチ処理）

---

## 🎯 主な機能

### Phase 1-3: コア機能（完成）
- ✅ **eBay Fetcher**: eBay 販売データの取得（モック実装、API 復活待ち）
- ✅ **Mercari Fetcher**: メルカリダミーデータのインポート
- ✅ **Normalizer**: 商品タイトル正規化
- ✅ **Analyzer**: 需要・利益・供給スコア計算
- ✅ **Streamlit Dashboard**: リアルタイムリサーチダッシュボード

### Phase 4: マルチソース準備（完成）
- ✅ **SourceSite Enum 拡張**: Amazon、Yahoo（Auction/Shopping/Fril）、Rakuten に対応
- ✅ **フェッチャ骨格**: 5 つのプラットフォーム用の fetcher スケルトン

### Phase 5: Live Scraping & Interactive Report (✨ 最新・完成)
- ✅ **Live Scraping**: メルカリ、ハードオフ、Yahoo!フリマからのリアルタイムデータ取得
- ✅ **Interactive Report**: クリックで利益計算・ROIをシミュレーションできるHTMLレポート生成
- ✅ **eBay API Integration**: eBay Browse API を使用した正確な商品画像取得
- ✅ **Filter Optimization**: 複数枚セット、フィギュア、ボックス、オークション形式の自動除外

---

## 🚀 クイックスタート

### インストール

\\\ash
# 依存パッケージをインストール
pip install -r requirements.txt

# ディレクトリを作成
mkdir -p data/imports data/imports/archive
\\\

### 基本的な使い方

#### 方法 1: オンラインフェッチ（eBay + Mercari）

\\\ash
python app.py
# または
python app.py --keyword "pokemon card" --limit 50
\\\

#### 方法 2: 単一 CSV インポート

\\\ash
python app.py --import-csv data/imports/amazon.csv --source amazon
python app.py --import-csv data/imports/yahoo_auction.csv --source yahoo_auction
\\\

#### 方法 3: バッチインポート（複数 CSV 一括処理）

\\\ash
# data/imports/ 内のすべての CSV を自動処理
python app.py --batch-import

# 処理済みファイルをアーカイブ
python app.py --batch-import --archive
\\\

#### 方法 4: Streamlit ダッシュボード

\\\ash
streamlit run dashboard.py
\\\

---

## 📊 CSV フォーマット

各プラットフォーム用の CSV テンプレートを用意しています：

\\\
docs/csv_formats/
├── amazon_template.csv
├── yahoo_auction_template.csv
├── yahoo_shopping_template.csv
├── yahoo_fril_template.csv
└── rakuten_template.csv
\\\

詳細は **[Phase 5 ガイド](docs/PHASE5_GUIDE.md)** を参照。

---

## 📁 プロジェクト構成

\\\
ebay-research-edge/
├── app.py                          # メインエントリーポイント
├── dashboard.py                    # Streamlit ダッシュボード
├── requirements.txt                # 依存パッケージ
├── src/
│   ├── config/                     # 設定管理
│   ├── fetcher/                    # データ取得（eBay、Mercari、Amazon等）
│   ├── normalizer/                 # データ正規化
│   ├── analyzer/                   # スコア計算
│   ├── models/                     # データモデル
│   ├── display/                    # CSV 出力
│   └── utils/
│       ├── csv_importer.py         # CSV インポーター
│       └── batch_processor.py      # バッチ処理エンジン
├── tests/
│   ├── test_phase5_csv_import.py
│   └── test_phase5b_batch_import.py
├── docs/
│   ├── PHASE5_GUIDE.md             # Phase 5 使用ガイド
│   ├── function-specification.md   # 機能仕様書
│   └── csv_formats/                # CSV テンプレート
├── data/
│   ├── categories/                 # YAML カテゴリ設定
│   ├── imports/                    # CSV インポート用ディレクトリ
│   │   └── archive/                # アーカイブ
│   ├── raw/                        # 取得データ
│   └── processed/                  # 分析結果
└── README.md                       # このファイル
\\\

---

## 🔧 使用技術

- **Python 3.8+**
- **Streamlit**: Web UI
- **Pandas**: データ処理
- **PyYAML**: 設定管理
- **eBay API**: 販売データ取得（準備中）

---

## 📖 ドキュメント

- **[Phase 5 ガイド](docs/PHASE5_GUIDE.md)** – CSV インポート・バッチ処理の詳細
- **[機能仕様書](docs/function-specification.md)** – システムアーキテクチャ・API 仕様
- **[使用ガイド](docs/USAGE.md)** – 基本的な操作方法

---

## 🗓️ ロードマップ

| フェーズ | 機能 | 状態 |
|---------|------|------|
| Phase 1 | eBay Fetcher + Scoring | ✅ 完成 |
| Phase 2 | Mercari Fetcher + Tests | ✅ 完成 |
| Phase 3 | Streamlit Dashboard | ✅ 完成 |
| Phase 4 | マルチソース準備 | ✅ 完成 |
| Phase 5 | ライブスクレイピング & インタラクティブ・レポート | ✅ 完成 (New!) |
| Phase 6 | Amazon/Yahoo/Rakuten 実装 | 🔄 計画中 |
| Phase 7 | マルチカテゴリ対応 | 🔄 計画中 |

---

## 🚨 既知の制限事項

1. **eBay API**: セキュリティ確認中（2026 年 4-5 月復活予定）
2. **Mercari**: 現在ダミーデータのみ（Web スクレイピングまたは API 連携予定）
3. **スコアリング**: eBay データが無い場合、国内単独データでは スコア 50.0（skip）となります

---

## 🔐 セキュリティ

- 認証情報（API キー等）は **環境変数**で管理してください
- **.env** ファイルは **.gitignore** に追加済み
- 本番環境では HTTPS + Token 認証を推奨

---

## 📞 サポート

問題が発生した場合：

1. **[docs/PHASE5_GUIDE.md](docs/PHASE5_GUIDE.md)** のトラブルシューティングを確認
2. **ログ出力**を確認（INFO/ERROR レベルのメッセージ）
3. **GitHub Issues** で類似問題を検索

---

## 📝 ライセンス

MIT License

---

## 👤 作成者

eBay-Research-Edge Development Team

**最終更新:** 2026-04-24（Phase 5B 完成）
