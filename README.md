# eBay-Research-Edge

eBay での売上データと日本国内マーケットプレイス（メルカリ、ハードオフ、Yahoo!フリマ等）の仕入値を比較分析し、利益機会を自動検出・台帳管理する次世代リサーチツール。

**Status:** Phase 5 完成（ライブリサーチ & インタラクティブ連携）

---

## 🎯 主な機能

### ✨ Phase 5: Live Scraping & Interactive Export (最新・完成)
- ✅ **Live Scraping**: メルカリ、ハードオフ、Yahoo!フリマからのリアルタイムデータ取得
- ✅ **Interactive Report**: クリックで利益計算・ROIをシミュレーションできるHTMLレポート生成
- ✅ **Google Sheets Export**: ボタン一つで管理用スプレッドシートへデータを保存 (GAS連携)
- ✅ **eBay API Integration**: eBay Browse API を使用した正確な商品画像取得
- ✅ **Filter Optimization**: 周辺備品（フレーム、空箱、ボックス等）やオークション形式の自動除外

### Phase 1-4: コア基盤
- ✅ **Normalizer**: 商品タイトル正規化・キーワード抽出
- ✅ **Analyzer**: 需要・利益・供給スコアリング
- ✅ **CSV Batch Import**: 既存のリストからのバッチ処理機能

---

## 🚀 クイックスタート

### インストール

```bash
# 依存パッケージをインストール
pip install -r requirements.txt

# Playwright のブラウザをインストール
playwright install chromium
```

### 基本的な使い方（最新版）

#### 1. リサーチレポートの生成と分析
リサーチを開始し、ブラウザで対話型レポートを開きます。

```bash
python generate_research_report.py
```

#### 2. スプレッドシートへの保存
- 生成されたレポート上で、仕入れ候補を選択します。
- 「📥 この商品を保存」または「🚀 一括保存」ボタンをクリックします。
- **Google Apps Script (GAS)** を経由して、指定のスプレッドシートへ即時にデータが書き込まれます。

---

## 📁 主要ファイル構成

- `generate_research_report.py`: メインスクリプト（リサーチ・レポート生成・保存サーバー）
- `dashboard.py`: Streamlit版ダッシュボード（旧版）
- `docs/function-specification.md`: 最新の機能仕様書
- `.env`: API認証情報およびGAS URLの設定

---

## 🗓️ ロードマップ

| フェーズ | 機能 | 状態 |
|---------|------|------|
| Phase 1-3 | eBay Fetcher + Scoring | ✅ 完成 |
| Phase 4 | マルチソース基盤準備 | ✅ 完成 |
| Phase 5 | ライブリサーチ & Google Sheets 連携 | ✅ 完成 (New!) |
| Phase 6 | Amazon/Yahoo Shopping 実装 | 🔄 計画中 |
| Phase 7 | マルチカテゴリ・AI分析対応 | 🔄 計画中 |

---

## 🔐 セキュリティ
- 認証情報（eBay API, GAS URL等）は **.env** ファイルで管理してください。
- サービスアカウント（JSON）を使わない GAS 方式を採用し、手軽さと利便性を両立しています。

---

## 👤 作成者

**eBay-Research-Edge Development Team**
(Coding AI: Antigravity)

**最終更新:** 2026-05-07 (Phase 5C: Google Sheets Direct Export 完成)
