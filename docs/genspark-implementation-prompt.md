# docs/genspark-implementation-prompt.md

# Genspark Implementation Prompt

あなたはソフトウェアエンジニアとして、以下の仕様に基づいて
「eBay-Research-Edge」を実装してください。

## プロジェクト概要

eBay-Research-Edge は、日本国内調達を前提に、
eBay Sold データと国内価格を比較し、
LIST候補を数値ベースで抽出する日本人セラー向けリサーチ支援ツールです。

## 実装の目的

* 手作業中心のリサーチを半自動化する
* eBay Sold の需要と国内価格差を数値化する
* LIST候補 / 保留 / 見送りを自動判定する

## MVP要件

* 対象ジャンルは1つ
* 海外データは eBay Sold
* 国内データは1サイトのみ
* 30日 / 90日の Sold 件数を出す
* eBay価格の中央値 / 平均値 / 最安値 / 最高値を算出する
* 国内価格との価格差を算出する
* 概算利益 / 粗利率を算出する
* STR を算出する
* candidate\_score を算出する
* decision\_status を表示する
* CSV出力できること

## 期待する構成

* 取得処理
* 正規化処理
* 分析処理
* 表示処理
を責務分離して実装してください。

## 優先事項

1. 動くこと
2. コードの見通しが良いこと
3. スコアロジックを変更しやすいこと
4. 生データを保持できること

## 実装方針

* Pythonベース
* 初期保存形式は CSV または SQLite
* UIは簡易でよい（CLI / Streamlit / 簡易Web UI のいずれか）
* 完全自動化は不要
* MVPでは本番運用より、再現可能なプロトタイプを優先する

## 必須成果物

* ディレクトリ構成
* 実装コード
* requirements.txt または pyproject.toml
* README.md 更新
* docs にある設計ドキュメントとの整合
* サンプル実行方法
* 主要処理の説明
* 今後の拡張ポイント

## 判定ロジック（初期案）

candidate\_score = 0.4 \* demand\_score + 0.4 \* profit\_score + 0.2 \* supply\_score

* demand\_score:

  * sold\_30d
  * sold\_90d
  * str
* profit\_score:

  * estimated\_profit\_rate
  * estimated\_profit\_jpy
* supply\_score:

  * active\_count の少なさ

decision\_status:

* 80点以上: list\_candidate
* 60〜79点: hold
* 59点以下: skip

## STR定義

STR = sold / (sold + active) \* 100

## 出力例

最低限、以下を表またはCSVで出力してください。

* normalized\_name
* sold\_30d
* sold\_90d
* active\_count
* median\_price\_usd
* domestic\_min\_price\_jpy
* estimated\_profit\_jpy
* estimated\_profit\_rate
* str
* candidate\_score
* decision\_status

## 実装時の注意

* タイトル表記ゆれを想定する
* セット品 / 単品混在に注意する
* 生データは必ず保持する
* ロジックを関数単位で分割する
* 後から国内サイトを追加しやすい構造にする

## 作業手順

1. ディレクトリ構成を提案
2. MVPに必要なモジュールを分割
3. 各モジュールを実装
4. サンプルデータまたは実データで動作確認
5. README と docs を整備
6. 実装内容を要約





\## カテゴリ方針

MVPでは初期検証のため1カテゴリを対象とするが、

システム設計はカテゴリ非依存（category-agnostic）で実装すること。



カテゴリ固有の差分はコードに直書きせず、

設定ファイルまたはマスタデータで管理すること。



想定する差分項目:

\- category\_name

\- include\_keywords

\- exclude\_keywords

\- normalization

