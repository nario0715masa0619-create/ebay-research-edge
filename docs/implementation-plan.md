# docs/implementation-plan.md

# eBay-Research-Edge Implementation Plan

## Phase 1: eBay Sold MVP
### 目的
eBay Sold の相場把握を半自動化する。

### タスク
- 検索入力機能
- eBay Sold データ取得
- CSV保存
- sold_30d / sold_90d 計算
- median / avg / min / max 計算

### 完了条件
- 任意キーワードで集計済みCSVが出力できる
- 30日 / 90日の基本指標が見られる

## Phase 2: 国内価格比較
### 目的
国内価格比較と粗利判断を可能にする。

### タスク
- 国内1サイト対応
- 国内価格取得
- 国内最安値 / 中央値算出
- 概算利益 / 粗利率算出
- candidate_score 初版実装
- decision_status 判定実装

### 完了条件
- eBay と国内価格を比較表示できる
- LIST候補 / 保留 / 見送りを自動表示できる

## Phase 3: UI / Dashboard
### 目的
毎日のリサーチ起点として使える画面を作る。

### タスク
- 検索UI
- サマリーカード
- 候補一覧テーブル
- 詳細パネル
- CSVダウンロード
- フィルタ / ソート

### 完了条件
- 毎日のリサーチをUI上で完結できる