# 機能詳細ガイド - eBay Research Edge

本ドキュメントは、eBay Research Edge の各機能の詳細な説明と使用方法をまとめています。

---

## 目次

1. [複数サイト価格取得](#複数サイト価格取得)
2. [AI 画像判定](#ai-画像判定)
3. [利益計算](#利益計算)
4. [Google Sheets 連携](#google-sheets-連携)
5. [フィルタリング](#フィルタリング)
6. [ダッシュボード操作](#ダッシュボード操作)

---

## 複数サイト価格取得

### 概要

eBay の商品情報を基に、以下の国内マーケットプレイスから自動的に相場情報を収集します。

- **メルカリ**
- **ハードオフ**
- **Yahoo!フリマ**
- **Yahoo!オークション**（落札履歴）

### メルカリからの取得

**検索方式**：Playwright を使用した動的スクレイピング

**取得情報**：
- 商品価格（JPY）
- 商品画像 URL
- 商品ページリンク

**検索条件**：
- キーワード：eBay タイトルから自動抽出
- 並び順：最新出品順
- 抽出件数：上位 15 件

**コード例**：
\\\python
async def search_mercari(page, keyword):
    # Playwright で mercari.com にアクセス
    # キーワード検索実行
    # 商品情報を抽出
    # 価格 100 円未満は除外
    return results
\\\

**除外条件**（フィルタリング）：
- 価格 100 円未満
- 「盗難防止品」を含むタイトル
- 「詐欺」「注意」などを含む説明文

### ハードオフからの取得

**検索方式**：Playwright スクレイピング

**対象**：ハードオフオンラインストア（https://hardoff.jp/）

**取得情報**：
- 商品価格（JPY）
- 商品画像 URL
- 商品ページリンク

**検索条件**：
- キーワード：eBay タイトルから自動抽出
- 抽出件数：上位 5 件

### Yahoo!フリマからの取得

**検索方式**：Playwright スクレイピング

**対象**：Yahoo!フリマ（https://paypay.ne.jp/）

**取得情報**：
- 商品価格（JPY）
- 商品画像 URL
- 商品ページリンク

### Yahoo!オークション落札履歴

**検索方式**：Playwright スクレイピング（閉札検索ページ）

**URL 形式**：
\\\
https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50
\\\

**取得情報**：
- **最小落札価格**（最安値）
- **最大落札価格**（最高値）
- **中央値**（平均値ではなく中央値を採用）
- **落札件数**

**統計計算**：

\\\python
def fetch_yahoo_auction_history(search_query, browser):
    # ページ取得
    # 正規表現で最安・平均・最高・件数を抽出
    # 中央値を計算
    return {
        'min': int,      # 最小落札価格
        'max': int,      # 最大落札価格
        'median': int,   # 中央値（推定）
        'count': int     # 落札件数
    }
\\\

**例**：
\\\
検索クエリ：「ポケモンカード マナフィ 004/PPP」
結果：
  最安：4,580 円
  最高：81,500 円
  中央値：41,365 円
  落札件数：7 件
\\\

---

## AI 画像判定

### 概要

GPT-4o Vision API を使用して、eBay 出品画像と国内マーケットプレイス商品画像を比較し、同一商品か判定します。

**判定項目**：
- カード番号の一致
- レアリティの一致
- 状態の差異
- 偽造品・レプリカの検知

### 判定スコア

**0～100%**で表示：

| スコア | 意味 |
|--------|------|
| 90～100% | ほぼ同一（購入推奨） |
| 70～89% | 同一商品（状態に差異あり） |
| 50～69% | 類似商品（同じカードだが型違い等） |
| 0～49% | 異なる商品 |
| 0% | レプリカ・観賞用品・展示用 |

### レプリカ・観賞用品の自動検知

商品説明から以下のキーワードを検出した場合、一致度を **強制的に 0%** に設定：

\\\
「レプリカ」「偽造品」「偽物」
「観賞用」「展示用」「飾り用」
「コスプレ」「アクセサリー」
「トレーニング用」「教材用」
\\\

### AI 判定プロセス

1. eBay 画像 URL を取得
2. 国内マーケットプレイス画像 URL を取得
3. 商品説明文を取得
4. GPT-4o Vision API に送信
5. レプリカキーワードをチェック → あれば 0% に強制設定
6. 一致度スコアを返す

**コード例**：
\\\python
async def analyze(ebay_image, compare_image, description):
    # レプリカキーワードをチェック
    if has_counterfeit_keywords(description):
        return {
            'match_percentage': 0,
            'is_counterfeit': True,
            'analysis': 'Counterfeit or display item detected'
        }
    
    # GPT-4o Vision で画像比較
    response = client.vision.analyze(ebay_image, compare_image)
    return response
\\\

### パフォーマンス

- **API 呼び出し時間**：3～5 秒/画像ペア
- **コスト**：1 回あたり数円（OpenAI 従量課金）

---

## 利益計算

### 計算式

\\\
eBay 価格（JPY） = USD 価格 × 為替レート
手数料 = eBay 価格（JPY）× 11.35%
送料 = 1,500 円（固定）
利益 = eBay 価格（JPY）- 手数料 - 送料 - 仕入れ値
ROI（%) = (利益 / 仕入れ値) × 100
\\\

### 例

\\\
eBay 価格：.00
為替レート：156.61（1 USD = 156.61 JPY）
eBay 価格（JPY）：95 × 156.61 = 14,877 円

手数料：14,877 × 11.35% = 1,688 円
送料：1,500 円

仕入れ値：5,000 円（手動入力）

利益 = 14,877 - 1,688 - 1,500 - 5,000 = 6,689 円
ROI = (6,689 / 5,000) × 100 = 133.8%
\\\

### 仕入れ値編集

**ダッシュボード上での操作**：

1. 「仕入れ値」欄をクリック
2. テキストボックスに金額を入力
3. Enter キーを押す
4. 利益・ROI が自動再計算

**リアルタイム再計算**：

\\\javascript
document.getElementById('purchase-price').addEventListener('change', () => {
    const purchase_price = parseFloat(document.getElementById('purchase-price').value);
    const profit = ebay_price_jpy - fees - shipping - purchase_price;
    const roi = (profit / purchase_price) * 100;
    
    document.getElementById('profit').textContent = profit.toLocaleString();
    document.getElementById('roi').textContent = roi.toFixed(1);
});
\\\

### 為替レートの自動取得

**データソース**：exchangerate-api.com（無料 API）

**更新タイミング**：アプリ起動時（メモリキャッシュで 1 実行内で再利用）

**コード例**：
\\\python
def get_exchange_rate():
    try:
        response = requests.get(
            'https://api.exchangerate-api.com/v4/latest/USD',
            timeout=5
        )
        if response.status_code == 200:
            return response.json()['rates']['JPY']
    except:
        pass
    return 150  # フォールバック
\\\

---

## Google Sheets 連携

### 概要

分析結果を Google Sheets に自動保存し、過去のリサーチ履歴を蓄積します。

### 保存フロー

\\\
ダッシュボード「保存」ボタン
         ↓
Flask /save エンドポイント
         ↓
Google Apps Script (GAS) Web App
         ↓
Google Sheets に行追加
\\\

### 保存される情報

| 列 | データ |
|----|--------|
| A | タイムスタンプ（ISO 8601） |
| B | eBay タイトル |
| C | eBay 価格（JPY） |
| D | 仕入れ値（JPY） |
| E | 利益（JPY） |
| F | ROI（%） |
| G | 検索結果（JSON） |
| H | 抽出キーワード |

### 保存オプション

**個別保存**：
- 1 件の商品のみ保存
- ダッシュボード上で商品ごとに「保存」ボタンをクリック

**一括保存**：
- 全検索結果を一度に保存
- 「すべて保存」ボタンをクリック

### Google Sheets の設定

**ヘッダー行**（1 行目）：

\\\
| Timestamp | eBay Title | eBay Price JPY | Purchase Price | Profit | ROI % | Items JSON | Keywords |
\\\

**自動フォーマット設定**：

\\\javascript
// Google Apps Script で自動フォーマット
const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
const range = sheet.getRange('A:F');
range.setNumberFormat('#,##0');  // 3 桁区切り

const priceRange = sheet.getRange('B:B');
priceRange.setNumberFormat('@');  // テキスト形式
\\\

### トラブルシューティング

**問題**：「GAS_WEBAPP_URL not found」エラー

**原因**：.env ファイルで GAS_WEBAPP_URL が設定されていない

**対応**：
1. .env ファイルを確認
2. GAS Web App URL をコピー（Google Apps Script エディタで確認）
3. .env に設定：\GAS_WEBAPP_URL=https://...\

---

## フィルタリング

### 自動フィルタ

ダッシュボードに表示される前に、以下の条件に該当する商品は自動除外：

#### 1. 低価格フィルタ

**除外条件**：価格 100 円未満

**理由**：利益が期待できず、手数料・送料で赤字になる可能性

**コード**：
\\\python
if price < 100:
    continue  # スキップ
\\\

#### 2. キーワード除外フィルタ

**除外キーワード**：
- 「盗難防止品」
- 「注意」「詐欺」「偽物」
- 「観賞用」「展示用」
- 「トレーニング用」「教材用」

**適用場所**：
- メルカリ：タイトル・説明文
- ハードオフ：タイトル・HTML
- Yahoo!フリマ：タイトル・説明文
- Yahoo!オークション：落札結果の「盗難防止品」フラグ

**コード例**：
\\\python
exclude_keywords = ['盗難防止品', '注意', '詐欺', '偽物', '観賞用', '展示用']

def should_exclude(title, description):
    text = (title + ' ' + description).lower()
    for keyword in exclude_keywords:
        if keyword.lower() in text:
            return True
    return False
\\\

### ユーザーによる手動フィルタリング

**ダッシュボード上での操作**：

1. 商品一覧を確認
2. 不要な商品の「削除」ボタンをクリック
3. ダッシュボードから非表示（保存時には除外）

---

## ダッシュボード操作

### レイアウト

\\\
┌─────────────────────────────────────────┐
│  eBay Research Edge - Dashboard         │
├─────────────────────────────────────────┤
│ 進捗：[3/10]  🔄 検索中...              │
├─────────────────────────────────────────┤
│                                         │
│ 【商品 1】                              │
│ Mega Charizard X ex SAR 110/080         │
│ eBay 価格：¥15,000                     │
│ ┌────────────────────────────────┐    │
│ │ 出品                           │    │
│ │ 最新情報：8000 (メルカリ)      │    │
│ │ 最新情報：7500 (ハードオフ)    │    │
│ │ 最新情報：41365 (ヤフオク)     │    │
│ └────────────────────────────────┘    │
│                                        │
│ 仕入れ値：[_____円] 自動計算           │
│ 利益：¥8,798  ROI：133.8%             │
│                                        │
│ [詳細] [保存] [削除]                   │
└─────────────────────────────────────────┘
\\\

### 主要ボタン

| ボタン | 機能 |
|--------|------|
| **詳細** | 商品の全情報を表示（画像、AI 判定スコア、説明文） |
| **保存** | Google Sheets に保存 |
| **削除** | ダッシュボードから非表示（保存時に除外） |
| **すべて保存** | 全検索結果を Google Sheets に保存 |

### リアルタイム更新

**ポーリング間隔**：3 秒

**更新内容**：
- 新しい検索結果がサーバーに追加される
- AJAX で /data エンドポイントから取得
- JavaScript でダッシュボードを動的に更新

**コード例**：
\\\javascript
setInterval(() => {
    fetch('/data')
        .then(res => res.json())
        .then(data => {
            if (data.is_finished) {
                document.getElementById('progress').textContent = '検索完了';
            } else {
                document.getElementById('progress').textContent = data.progress;
            }
            updateDashboard(data.results);
        });
}, 3000);
\\\

### 詳細パネルの表示

「詳細」ボタンをクリック → モーダル表示

**表示内容**：
- eBay 出品画像
- 国内マーケットプレイス画像
- AI 一致度スコア（%）
- 商品説明文（テキスト）
- 各サイトのリンク

---

## キーワード抽出

### 抽出ロジック

eBay タイトルから、以下の優先度で キーワードを抽出：

1. **カード番号**（例：110/080）
   - 正規表現：\/(\d+)/(\d+)/\
   - 例：「110/080」

2. **レアリティ**（例：SAR、AR、SR）
   - 正規表現：\/(SAR|AR|SR|UR|SSR)/\
   - 例：「SAR」

3. **日本語名**（例：リザードン、マナフィ）
   - 辞書マッピング：カード名を日本語に変換
   - 例：「Charizard」→「リザードン」

### 抽出例

**eBay タイトル**：
\\\
Mega Charizard X ex SAR 110/080 Inferno X M2 Pokemon TCG Card
\\\

**抽出キーワード**：
\\\
["リザードン", "SAR", "110/080"]
\\\

### 検索に使用

抽出したキーワード（スペース区切り）で各国内サイトを検索：

\\\
メルカリ検索：「リザードン SAR 110/080」
ハードオフ検索：「リザードン SAR 110/080」
Yahoo!フリマ検索：「リザードン SAR 110/080」
Yahoo!オークション検索：「リザードン SAR 110/080」
\\\

---

## パフォーマンス・最適化

### 並行処理

複数サイトの検索を \syncio\ で並行実行：

\\\python
async def main_process():
    # 全検索を並行実行
    m_res = await search_mercari(page, keywords)
    y_res = await search_yahoo(page, keywords)
    y_history = await fetch_yahoo_auction_history(keywords, browser)
    h_res = await search_hardoff(page, keywords)
\\\

**実行時間**：
- 逐次実行：30～40 秒
- 並行実行：12～15 秒（約 60% 削減）

### タイムアウト設定

各検索関数に独立した タイムアウト を設定（5～10 秒）：

- 1 つのサイト遅延が全体に影響しない
- タイムアウト時は \None\ を返す（スキップ）

### キャッシング

**為替レート**：メモリキャッシュ（1 実行内で再利用）

**API トークン**：24 時間キャッシュ（本実装時）

---

**最終更新**：2026-05-08
**バージョン**：V15.2
