# 🛠️ eBay Research Edge (ERE) - Runtime Configuration
# 運用設定値の集約管理とバリデーション

import sys

def _validate(name, value, type_hint, min_val=None, max_val=None, fallback=None):
    """
    設定値の型と範囲をチェックし、異常があればフォールバック値を返す。
    """
    try:
        # 型変換・チェック
        if type_hint == int:
            final_val = int(value)
        elif type_hint == float:
            final_val = float(value)
        elif type_hint == dict:
            if not isinstance(value, dict): raise ValueError("Not a dict")
            final_val = value
        elif type_hint == list:
            if not isinstance(value, list): raise ValueError("Not a list")
            final_val = value
        else:
            final_val = value

        # 範囲チェック (数値の場合)
        if isinstance(final_val, (int, float)):
            if min_val is not None and final_val < min_val:
                raise ValueError(f"Value {final_val} is below minimum {min_val}")
            if max_val is not None and final_val > max_val:
                raise ValueError(f"Value {final_val} is above maximum {max_val}")
        
        return final_val
    except Exception as e:
        print(f"  [CONFIG WARNING] '{name}' に異常値を検出 ({value}): {e}. 安全な規定値 '{fallback}' を使用します。", file=sys.stderr)
        return fallback

# --- [ 生の設定値定義 (Raw Values) ] ---
# 運用者はここを編集してください。

# リサーチ対象上限
_MAX_RESEARCH_ITEMS = 10

# 固定送料 (円)
_DEFAULT_SHIPPING_COST_JPY = 1500

# ジャンル別手数料率
_FEE_RATES = {
    "ポケモンカード": 0.1135,
    "フィギュア": 0.127,
    "ゲーム": 0.127,
    "default": 0.150
}

# 除外キーワード
_EXCLUDED_KEYWORDS = ["盗難防止", "観賞用", "展示用", "レプリカ"]

# タイムアウト系 (秒/ミリ秒)
_REQUEST_TIMEOUT_SECONDS = 30
_API_REQUEST_TIMEOUT_SECONDS = 10
_BROWSER_TIMEOUT_MS = 60000
_BROWSER_GOTO_TIMEOUT_MS = 30000
_BROWSER_SELECTOR_TIMEOUT_MS = 10000
_WAIT_FOR_TIMEOUT_MS = 3000
_BROWSER_SHORT_WAIT_MS = 1500
_SEARCH_PAGE_WAIT_MS = 2000

# サーバー・UI設定
_SERVER_PORT = 5009
_UI_POLLING_INTERVAL_MS = 3000


# --- [ バリデーション済み定数のエクスポート ] ---
# アプリケーション内ではこれらを使用してください。

MAX_RESEARCH_ITEMS = _validate("MAX_RESEARCH_ITEMS", _MAX_RESEARCH_ITEMS, int, min_val=1, fallback=10)
DEFAULT_SHIPPING_COST_JPY = _validate("DEFAULT_SHIPPING_COST_JPY", _DEFAULT_SHIPPING_COST_JPY, int, min_val=0, fallback=1500)
FEE_RATES = _validate("FEE_RATES", _FEE_RATES, dict, fallback={"default": 0.15})
EXCLUDED_KEYWORDS = _validate("EXCLUDED_KEYWORDS", _EXCLUDED_KEYWORDS, list, fallback=[])

REQUEST_TIMEOUT_SECONDS = _validate("REQUEST_TIMEOUT_SECONDS", _REQUEST_TIMEOUT_SECONDS, int, min_val=1, fallback=30)
API_REQUEST_TIMEOUT_SECONDS = _validate("API_REQUEST_TIMEOUT_SECONDS", _API_REQUEST_TIMEOUT_SECONDS, int, min_val=1, fallback=10)
BROWSER_TIMEOUT_MS = _validate("BROWSER_TIMEOUT_MS", _BROWSER_TIMEOUT_MS, int, min_val=1000, fallback=60000)
BROWSER_GOTO_TIMEOUT_MS = _validate("BROWSER_GOTO_TIMEOUT_MS", _BROWSER_GOTO_TIMEOUT_MS, int, min_val=1000, fallback=30000)
BROWSER_SELECTOR_TIMEOUT_MS = _validate("BROWSER_SELECTOR_TIMEOUT_MS", _BROWSER_SELECTOR_TIMEOUT_MS, int, min_val=0, fallback=10000)
WAIT_FOR_TIMEOUT_MS = _validate("WAIT_FOR_TIMEOUT_MS", _WAIT_FOR_TIMEOUT_MS, int, min_val=0, fallback=3000)
BROWSER_SHORT_WAIT_MS = _validate("BROWSER_SHORT_WAIT_MS", _BROWSER_SHORT_WAIT_MS, int, min_val=0, fallback=1500)
SEARCH_PAGE_WAIT_MS = _validate("SEARCH_PAGE_WAIT_MS", _SEARCH_PAGE_WAIT_MS, int, min_val=0, fallback=2000)

SERVER_PORT = _validate("SERVER_PORT", _SERVER_PORT, int, min_val=1, max_val=65535, fallback=5009)
UI_POLLING_INTERVAL_MS = _validate("UI_POLLING_INTERVAL_MS", _UI_POLLING_INTERVAL_MS, int, min_val=500, fallback=3000)
