# 🛠️ eBay Research Edge (ERE) - Runtime Configuration
# 運用設定値の集約管理

# --- [ 検索・取得設定 ] ---
# リサーチ対象とする商品の上限数 (スプレッドシートの先頭からの件数)
MAX_RESEARCH_ITEMS = 10

# 固定送料 (円)
DEFAULT_SHIPPING_COST_JPY = 1500

# --- [ 手数料設定 ] ---
# ジャンル別のeBay販売手数料率 (手数料 + 海外決済手数料等の合算)
FEE_RATES = {
    "ポケモンカード": 0.1135,
    "フィギュア": 0.127,
    "ゲーム": 0.127,
    "default": 0.150            # 未定義ジャンルのための安全マージン
}

# --- [ スクレイピング設定 ] ---
# 検索結果から除外するキーワード
EXCLUDED_KEYWORDS = ["盗難防止", "観賞用", "展示用", "レプリカ"]
# 各種リクエストのタイムアウト (秒)
REQUEST_TIMEOUT_SECONDS = 30
API_REQUEST_TIMEOUT_SECONDS = 10  # eBay API等の軽量リクエスト用

# Playwright ブラウザ操作のタイムアウト (ミリ秒)
BROWSER_TIMEOUT_MS = 60000
BROWSER_GOTO_TIMEOUT_MS = 30000      # ページ遷移
BROWSER_SELECTOR_TIMEOUT_MS = 10000  # 要素出現待機

# ページ遷移・要素待機時間 (ミリ秒)
WAIT_FOR_TIMEOUT_MS = 3000
BROWSER_SHORT_WAIT_MS = 1500         # 調整用の短い待機

# メルカリ・ヤフーフリマ等の検索結果ページでの最低待機時間 (ミリ秒)
SEARCH_PAGE_WAIT_MS = 2000

# --- [ サーバー・UI設定 ] ---
# Flask サーバーのポート番号
SERVER_PORT = 5009

# フロントエンドの自動更新 (ポーリング) 間隔 (ミリ秒)
UI_POLLING_INTERVAL_MS = 3000
