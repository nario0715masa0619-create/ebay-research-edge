# Phase 5: 統合テストガイド

このドキュメントでは、Phase 5（CSV インポート・バッチ処理）の統合テストを実行する方法を説明します。

---

## テスト実行方法

### 1. Phase 5A テスト（単一 CSV インポート）

\\\ash
python tests/test_phase5_csv_import.py
\\\

**期待される結果：**
\\\
Total: 5/5 passed
  ✓ Amazon CSV Import
  ✓ Yahoo Auction CSV Import
  ✓ All Sources CSV Import
  ✓ CSV Normalization & Scoring
  ✓ Complete CSV Pipeline
\\\

### 2. Phase 5B テスト（バッチ処理）

\\\ash
python tests/test_phase5b_batch_import.py
\\\

**期待される結果：**
\\\
Total: 4/4 passed
  ✓ CSV File Discovery
  ✓ Batch Processing
  ✓ Batch Normalization & Scoring
  ✓ Complete Batch Pipeline
\\\

---

## エンドツーエンドテスト

### シナリオ 1: 単一 CSV のインポート

\\\ash
# Amazon CSV をインポート
python app.py --import-csv docs/csv_formats/amazon_template.csv --source amazon
\\\

**検証項目：**
- [ ] パイプライン開始ログが表示される
- [ ] CSV ファイルが正常に読み込まれる
- [ ] 3 records が Amazon から取得される
- [ ] eBay データ（50 records）が取得される
- [ ] データが正規化される
- [ ] candidates が生成される
- [ ] CSV ファイルが \data/processed/\ に出力される

### シナリオ 2: バッチインポート

\\\ash
# data/imports/ に複数の CSV を配置
cp docs/csv_formats/amazon_template.csv data/imports/amazon_pokemon_001.csv
cp docs/csv_formats/yahoo_auction_template.csv data/imports/yahoo_auction_pokemon_001.csv

# バッチ処理を実行
python app.py --batch-import
\\\

**検証項目：**
- [ ] Batch processor が初期化される
- [ ] 2 つの CSV ファイルが自動検出される
- [ ] 合計 6 records が取得される
- [ ] eBay データ（50 records）が取得される
- [ ] パイプラインが正常に完了する
- [ ] CSV ファイルが出力される

### シナリオ 3: バッチインポート + アーカイブ

\\\ash
# 処理済みファイルをアーカイブ
python app.py --batch-import --archive
\\\

**検証項目：**
- [ ] バッチ処理が完了する
- [ ] 処理済みファイルが \data/imports/archive/\ に移動される
- [ ] アーカイブファイルにタイムスタンプが付与される

---

## パフォーマンステスト

### テスト 1: 大量 CSV ファイルの処理

\\\ash
# 10 個の CSV ファイルを生成
for i in {1..10}; do
  cp docs/csv_formats/amazon_template.csv "data/imports/amazon_test_\.csv"
done

# バッチ処理を実行して所要時間を記録
time python app.py --batch-import
\\\

**期待される所要時間：**
- 10 ファイル × 3 records = 30 records + eBay 50 records → **< 5 秒**

### テスト 2: 大量レコードの処理

CSV に 100 行のレコードを含む場合でも、正常に処理されることを確認。

---

## エラーハンドリングテスト

### テスト 1: ファイルが見つからない

\\\ash
python app.py --import-csv nonexistent.csv --source amazon
\\\

**期待される結果：**
\\\
ERROR: FileNotFoundError: nonexistent.csv not found
\\\

### テスト 2: 無効なソース指定

\\\ash
python app.py --import-csv data/imports/amazon_template.csv --source invalid_source
\\\

**期待される結果：**
\\\
error: argument --source: invalid choice: 'invalid_source'
\\\

### テスト 3: --import-csv なし --source あり

\\\ash
python app.py --source amazon
\\\

**期待される結果：**
\\\
ERROR: --source is required when using --import-csv
\\\

---

## Streamlit ダッシュボードテスト

\\\ash
streamlit run dashboard.py
\\\

**検証項目：**
- [ ] ダッシュボードがブラウザで開く
- [ ] サイドバーのキーワード入力フィールドが表示される
- [ ] 「Run Research」ボタンが機能する
- [ ] 結果テーブルが表示される
- [ ] CSV ダウンロードボタンが機能する
- [ ] フィルター・ソート機能が動作する

---

## テスト結果レポート

テスト実行後、以下の項目をチェックリストで確認してください：

### Phase 5A テスト
- [ ] All 5 tests passed
- [ ] Import functionality works correctly
- [ ] Normalization completes without errors
- [ ] CSV output is generated

### Phase 5B テスト
- [ ] All 4 tests passed
- [ ] CSV file discovery works
- [ ] Batch processing completes successfully
- [ ] Archive functionality works (if --archive used)

### エンドツーエンド
- [ ] Single CSV import works
- [ ] Batch import works
- [ ] Dashboard displays results
- [ ] Error handling is appropriate

---

## トラブルシューティング

### 問題: テスト実行時に ModuleNotFoundError

**解決策：**
\\\ash
# Python パスを確認
echo 

# プロジェクトルートから実行
cd /path/to/ebay-research-edge
python tests/test_phase5_csv_import.py
\\\

### 問題: CSV が見つからない

**解決策：**
\\\ash
# ファイルの存在確認
ls -la docs/csv_formats/
ls -la data/imports/

# パスを絶対パスで指定
python app.py --import-csv \D:\AI_スクリプト成果物\ebay-research-edge/docs/csv_formats/amazon_template.csv --source amazon
\\\

### 問題: エンコーディングエラー

**解決策：**
\\\ash
# CSV を UTF-8 で保存し直す
# （Windows の場合、メモ帳で「UTF-8 BOM なし」を選択）
\\\

---

## CI/CD テスト（GitHub Actions）

将来的に GitHub Actions で自動テストを実装予定。

テストが自動実行されるようになったら、以下をチェック：

- [ ] Python 3.8+ で実行
- [ ] すべてのテストが PASS
- [ ] Code coverage > 80%

