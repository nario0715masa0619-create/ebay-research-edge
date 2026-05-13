# 🏆 eBay Research Edge (ERE) - Official Entry Point (V16.x)
# [Role] Active Dashboard & Scraper
# [Run] python generate_research_report.py

import asyncio, os, re, requests, unicodedata, urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import pandas as pd
import webbrowser
import time
import json
import threading
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from openai import OpenAI
import config_runtime as config

# 🏆 V15.1: カタログページ完全排除版 (No Catalog Hub)
# ヤフーフリマの「製品カタログ(/product/)」を排除し、個別の出品物(/item/)のみを対象に。

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESEARCH_RESULTS = []
IS_FINISHED = False
IS_SEARCHING = False
LAST_ERROR = None
SEARCH_STATE_LOCK = threading.Lock()
CURRENT_GENRE = "ポケモンカード"
MAIN_PROCESS_THREAD = None

def parse_currency(value):
    if pd.isna(value): return 0.0
    v = re.sub(r'[^\d.]', '', str(value))
    try: return float(v)
    except: return 0.0

def get_exchange_rate():
    try:
        r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=config.API_REQUEST_TIMEOUT_SECONDS)
        return r.json()['rates']['JPY']
    except: return 157.50

def get_ebay_token():
    try:
        r = requests.post('https://api.ebay.com/identity/v1/oauth2/token', 
                          auth=(os.getenv('EBAY_REST_CLIENT_ID'), os.getenv('EBAY_REST_CLIENT_SECRET')), 
                          data={'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'}, timeout=config.API_REQUEST_TIMEOUT_SECONDS)
        return r.json().get('access_token')
    except: return None

def clean_ebay_id(id_val):
    if not id_val or pd.isna(id_val): return ""
    s = str(id_val).strip()
    # v1|123456789|0 形式の抽出
    match = re.search(r'v1\|(\d+)\|0', s)
    if match: return match.group(1)
    # 指数表記やフロート形式の修正
    try:
        if 'e+' in s.lower() or '.' in s:
            return "{:.0f}".format(float(s))
    except: pass
    return s.replace('.0', '')

async def fetch_yahoo_auction_history(search_query, browser):
    try:
        if isinstance(search_query, list):
            search_query = ' '.join(search_query)
        
        new_page = await asyncio.wait_for(browser.new_page(), timeout=config.API_REQUEST_TIMEOUT_SECONDS)
        # より広範囲のクラス名で価格を取得
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        
        await asyncio.wait_for(new_page.goto(url, wait_until='domcontentloaded'), timeout=config.API_REQUEST_TIMEOUT_SECONDS + 5)
        await new_page.wait_for_timeout(config.BROWSER_SHORT_WAIT_MS)
        
        # fontWeightBold を含むクラスから数値を抽出
        prices = await new_page.evaluate("""() => {
            const elements = document.querySelectorAll('[class*="fontWeightBold"]');
            return Array.from(elements)
                .map(el => el.innerText.replace(/[^0-9]/g, ''))
                .filter(v => v.length >= 2)
                .map(v => parseInt(v));
        }""")
        
        text_full = await new_page.evaluate('() => document.body.innerText')
        await new_page.close()
        
        if prices:
            prices.sort()
            n = len(prices)
            # 極端な外れ値を除外（上位・下位10%）
            trimmed = prices[max(1, n//10):max(n, n-n//10)] if n > 10 else prices
            median = trimmed[len(trimmed)//2]
            
            return {
                'min': min(prices),
                'median': median,
                'max': max(prices),
                'count': n,
                'url': url
            }
    except Exception as e:
        print(f'Yahoo error: {e}')
    return None


async def get_ebay_item_info(token, title, item_id=None):
    if not token: return {'img': 'https://via.placeholder.com/300', 'url': 'https://www.ebay.com', 'title': title, 'price': None}
    try:
        # 1. IDがある場合は、その商品の詳細を直接取得
        if item_id:
            full_id = f"v1|{item_id}|0" if str(item_id).isdigit() else str(item_id)
            url = f"https://api.ebay.com/buy/browse/v1/item/{full_id}"
            r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=config.API_REQUEST_TIMEOUT_SECONDS)
            if r.status_code == 200:
                data = r.json()
                price_data = data.get('price', {})
                return {
                    'img': data.get('image', {}).get('imageUrl', 'https://via.placeholder.com/300'),
                    'url': data.get('itemWebUrl', f"https://www.ebay.com/itm/{item_id}"),
                    'title': data.get('title', title),
                    'price': float(price_data.get('value', 0)) if price_data.get('value') else None,
                    'id': clean_ebay_id(data.get('itemId'))
                }

        # 2. IDがない、または直接取得に失敗した場合は検索
        url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={urllib.parse.quote(title)}&limit=1"
        r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=config.API_REQUEST_TIMEOUT_SECONDS)
        if r.status_code == 200:
            data = r.json()
            if 'itemSummaries' in data and data['itemSummaries']:
                item = data['itemSummaries'][0]
                price_data = item.get('price', {})
                return {
                    'img': item.get('image', {}).get('imageUrl', 'https://via.placeholder.com/300'),
                    'url': item.get('itemWebUrl', 'https://www.ebay.com'),
                    'title': item.get('title', title),
                    'price': float(price_data.get('value', 0)) if price_data.get('value') else None,
                    'id': clean_ebay_id(item.get('itemId'))
                }
    except: pass
    return {'img': 'https://via.placeholder.com/300', 'url': 'https://www.ebay.com', 'title': title, 'price': None}

def extract_keywords(title):
    kw = []
    t = unicodedata.normalize('NFKD', title).lower()
    
    # 1. 型番抽出 (例: 123/456) - これが最優先
    m = re.search(r'(\d+/[A-Z0-9]+)', title.upper())
    card_number = m.group(1) if m else None
    
    # 2. レアリティ抽出 (独立単語として)
    rarity = None
    if re.search(r'\bsar\b', t): rarity = 'SAR'
    elif re.search(r'\bsr\b', t): rarity = 'SR'
    elif re.search(r'\bar\b', t): rarity = 'AR'
    elif re.search(r'\bhr\b', t): rarity = 'HR'
    elif re.search(r'\bur\b', t): rarity = 'UR'
    
    # 3. ポケモン名の翻訳マッピング
    mapping = {'pikachu':'ピカチュウ','charizard':'リザードン','manaphy':'マナフィ','gengar':'ゲンガー','mewtwo':'ミュウツー','mew':'ミュウ'}
    ja_name = None
    for en, ja in mapping.items():
        if en in t: ja_name = ja; break
    
    # 【重要】検索ワードの組み立て
    if card_number:
        # 型番がある場合は、型番とレアリティを優先 (以前の絶好調な組み合わせ)
        if rarity: kw.append(rarity)
        kw.append(card_number)
        # 念のため、名前も最後に入れる（ノイズになるようなら外すことも検討）
        if ja_name: kw.append(ja_name)
    else:
        # 型番がない場合は、名前とレアリティを主役にする
        if ja_name: kw.append(ja_name)
        if rarity: kw.append(rarity)
        
    # フォールバック: 全くキーワードがない場合のみ、タイトルから抽出
    if not kw:
        words = re.findall(r'[a-zA-Z0-9]{3,}', title)
        kw = words[:2]
        
    kw = list(dict.fromkeys(kw))
    return kw



def extract_keywords_ai(title, genre):
    """AIを使って日本のフリマサイト向けに最適な日本語キーワードを抽出する"""
    try:
        # 特殊な記号が含まれている場合などのためにクリーンアップ
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        
        prompt = f"""以下のeBayの商品名から、日本のフリマサイト（メルカリ、ヤフオク等）で検索するのに最適な「日本語のキーワード」を3〜5単語程度で抽出してください。
        
        ジャンル: {genre}
        eBay商品名: {title}
        
        [重要ルール]
        - **作品名やキャラクター名は、日本公式の「漢字表記（フルネーム）」を絶対に最優先してください（例: Isagi Yoichi -> 潔世一, Yoichi Isagi -> 潔世一）。**
        - **「イサギヨイチ」のようなカタカナ表記は、漢字が不明な場合を除き禁止します。**
        - ジャンル名も適切に日本語に変換してください（例: Figure -> フィギュア）。
        - 出力は、最も重要な単語をスペース区切りで「キーワードのみ」返してください。
        - 余計な説明や記号は一切不要です。"""
        
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )
        kw_str = r.choices[0].message.content.strip()
        kw = [k.strip() for k in kw_str.split(' ') if k.strip()]
        print(f"  [AI-KW] {title[:20]}... -> {kw}")
        return kw
    except Exception as e:
        print(f"  [AI-KW-ERR] {e}")
        # フォールバックとして元のロジックを使用
        return extract_keywords(title)

async def search_mercari(page, kw, genre="ポケモンカード", is_manual=False):
    if not kw: return []
    # 重複排除
    words = ([genre] if not is_manual else []) + kw
    unique_words = []
    for w in words:
        if w not in unique_words: unique_words.append(w)
    
    # クエリが長すぎるとヒットしないため、最大4単語に制限
    query = ' '.join(unique_words[:4])
    
    try:
        url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote(query, safe="")}&status=on_sale'
        await page.goto(url, timeout=config.BROWSER_GOTO_TIMEOUT_MS)
        
        # 読み込み待ちを強化
        try:
            await page.wait_for_selector('a[href^="/item/m"]', timeout=config.BROWSER_SELECTOR_TIMEOUT_MS)
        except:
            pass
            
        items = await page.locator('a[href^="/item/m"]').all()
        res = []
        for it in items[:15]:
            try:
                d = await it.evaluate("""el => {
                    const imgDiv = el.querySelector('div[aria-label]');
                    const img = el.querySelector('img');
                    let rawTitle = imgDiv ? imgDiv.getAttribute('aria-label') : (img ? img.alt : "");
                    let title = rawTitle.replace(/の(画像|サムネイル).*$/, "").replace(/¥\s?[\d,]+/, "").trim();
                    return {
                        title: title,
                        price: el.innerText,
                        href: el.href,
                        img: img ? img.src : "",
                        html: el.innerHTML
                    }
                }""")
                
                # 「〜」は装飾でよく使われるため、除外リストから削除。またメルカリにオークション系用語は不要
                exclude_kws = ["盗難防止", "観賞用", "展示用", "レプリカ"]
                if any(x in d.get('title','') or x in d.get('html','') for x in exclude_kws): continue
                
                m = re.search(r'¥\s*([\d,]+)', d['price'])
                if m:
                    price = int(m.group(1).replace(',',''))
                    if price < 100: continue
                    res.append({'price':price, 'title':d['title'], 'url':d['href'], 'image':d['img'], 'site':'メルカリ'})
            except: continue
        return res[:5]
    except: return []

async def search_yahoo(page, kw, genre="ポケモンカード", is_manual=False):
    if not kw: return []
    words = ([genre] if not is_manual else []) + kw
    unique_words = []
    for w in words:
        if w not in unique_words: unique_words.append(w)
    query = ' '.join(unique_words[:6])
    try:
        url = f"https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote(query, safe='')}?open=1"
        await page.goto(url, timeout=config.BROWSER_GOTO_TIMEOUT_MS)
        try:
            await page.wait_for_selector('a[href*="/item/"]', timeout=config.BROWSER_SELECTOR_TIMEOUT_MS)
        except: pass
        items = await page.locator('a[href*="/item/"]').all()
        res = []
        for it in items[:15]:
            try:
                d = await it.evaluate("""el => {
                    const img = el.querySelector('img');
                    return {
                        title: img ? img.alt : "ヤフーフリマ商品",
                        allText: el.innerText,
                        href: el.href,
                        img: img ? img.src : ""
                    }
                }""")
                
                # 事実に基づいた価格抽出
                price_match = re.search(r'([\d,]+)\s*円', d['allText'])
                if not price_match:
                    price_match = re.search(r'¥\s*([\d,]+)', d['allText'])
                
                if price_match:
                    price_val = int(price_match.group(1).replace(',', ''))
                else:
                    # 最終手段: 「円」が含まれる行の数字を全部つなげる
                    m = re.search(r'.*円', d['allText'])
                    if m:
                        price_val = int(re.sub(r'[^\d]', '', m.group(0)))
                    else:
                        continue

                exclude_kws = ["盗難防止", "観賞用", "展示用", "レプリカ"]
                if any(x in d['title'] for x in exclude_kws): continue
                if price_val > 100:
                    res.append({'site': 'ヤフーフリマ', 'title': d['title'], 'price': price_val, 'url': d['href'], 'image': d['img']})
            except: continue
        
        if not res and len(items) > 0:
            await page.screenshot(path="debug_yahoo_0hits.png")
            print("  [DEBUG-Y] Items found but 0 hits after filtering. Screenshot saved.")
            
        return res[:5]
    except Exception as e:
        print(f"  [ERR-Y] {e}")
        return []


async def search_hardoff(page, kw, genre="ポケモンカード", is_manual=False):
    if not kw: return []
    if is_manual:
        query = ' '.join(kw)
    else:
        query = ' '.join([genre] + kw[:5])
    
    try:
        url = f'https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote(query)}'
        await page.goto(url, timeout=config.BROWSER_GOTO_TIMEOUT_MS)
        await page.wait_for_timeout(config.BROWSER_SHORT_WAIT_MS)
        items = await page.locator('div.item, .product-card, div:has(> a[href*="/product/"])').all()
        res = []
        for it in items[:5]:
            try:
                data = await it.evaluate("""el => {
                    const link = el.querySelector('a');
                    const text = el.innerText;
                    const p = text.match(/[\\d,]+/g);
                    return { title: text.split('\\n')[0], price: p?p[p.length-1]:"0", href: link?link.href:"", img: el.querySelector('img')?el.querySelector('img').src:"" }
                }""")
                if data['href']:
                    price = int(data['price'].replace(',',''))
                    exclude_kws = config.EXCLUDED_KEYWORDS
                    if price >= 100 and not any(x in data['title'] for x in exclude_kws):
                        res.append({'price':price, 'title':data['title'], 'url':data['href'], 'image':data['img'], 'site':'ハードオフ'})
            except: continue
        return res
    except: return []

# 手数料率は config_runtime.py で定義
FEE_RATES = config.FEE_RATES

async def main_process(genre="ポケモンカード"):
    global IS_FINISHED, RESEARCH_RESULTS, CURRENT_GENRE, IS_SEARCHING, LAST_ERROR
    # IS_SEARCHING = True は /start-search 側でセット済み
    try:
        # IS_FINISHED = False も /start-search 側でセット済み
        RESEARCH_RESULTS = [] # 以前の結果をクリア

        # 手数料率の決定
        fee_rate = FEE_RATES.get(genre, FEE_RATES["default"])
        print(f"  [LOG] ジャンル: {genre}, 適用手数料率: {fee_rate*100}%")

        rate = get_exchange_rate()
        ebay_token = get_ebay_token()
        sheet_id = os.getenv('GOOGLE_SHEETS_ID')
        df = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0")

        browser = None
        try:
            async with async_playwright() as p:
                print("  [DEBUG] ブラウザを起動中...")
                browser = await p.chromium.launch(headless=False, timeout=config.BROWSER_TIMEOUT_MS)
                print("  [DEBUG] ブラウザ起動完了")
                context = await browser.new_context()
                page = await context.new_page()
                print(f"  [DEBUG] Spreadsheet Columns: {df.columns.tolist()}")
                id_col = next((c for c in df.columns if c.lower() in ['ebay_item_id', 'item_id', 'ebay_id', 'itemid', 'id', '商品id']), None)
                title_col = next((c for c in df.columns if c.lower() in ['ebay_title', 'title', '商品名']), 'ebay_title')
                price_col = next((c for c in df.columns if c.lower() in ['avg_price_usd', 'price', 'ebay価格(usd)']), 'avg_price_usd')
                status_col = next((c for c in df.columns if c.lower() in ['status', 'ステータス', 'state']), None)

                for idx, row in df.iterrows():
                    if idx >= config.MAX_RESEARCH_ITEMS: break
                    try:
                        title = str(row.get(title_col, 'Unknown'))
                        item_id = clean_ebay_id(row.get(id_col))
                        
                        # スプシからの予備価格とステータス
                        usd_sheet = parse_currency(row.get(price_col, 0))
                        status_val = str(row.get(status_col, '')) if status_col else ''
                        
                        # AIを使って日本語キーワードを生成
                        kw = extract_keywords_ai(title, genre)
                        print(f"[SEARCH] [{idx+1}/10] {title} (ID: {item_id}, Status: {status_val})")
                        
                        print(f"  [LOG] eBay情報取得中... (ID: {item_id})")
                        ebay_data = await get_ebay_item_info(ebay_token, title, item_id)
                        print(f"  [LOG] eBay情報取得完了: {ebay_data['title'][:30]}...")
                        
                        # eBayからの最新データがあればそれを優先、なければスプシ価格を使用
                        usd = ebay_data.get('price') if ebay_data.get('price') else usd_sheet
                        final_id = item_id if item_id else (ebay_data.get('id') or '')
                        
                        res_obj = {
                            'idx': idx,
                            'ebay_title': ebay_data['title'],
                            'ebay_img': ebay_data['img'],
                            'ebay_url': ebay_data['url'],
                            'ebay_item_id': final_id,
                            'genre': genre,
                            'status': status_val,
                            'ebay_price_usd': usd,
                            'ebay_price_jpy': usd * rate,
                            'fees': (usd * rate * fee_rate),
                            'shipping': config.DEFAULT_SHIPPING_COST_JPY,
                            'items': [],
                            'keywords': kw,
                            'y_history': None,
                            'searching': False,
                            'error': None
                        }
                        RESEARCH_RESULTS.append(res_obj)

                        # 1. メルカリ
                        print(f"  [LOG] メルカリ検索中... (ジャンル: {genre})")
                        m_res = await search_mercari(page, kw, genre)
                        res_obj['items'].extend(m_res)
                        
                        # 2. ヤフーフリマ
                        print(f"  [LOG] ヤフーフリマ検索中...")
                        y_res = await search_yahoo(page, kw, genre)
                        res_obj['items'].extend(y_res)
                        
                        # 3. ハードオフ
                        print(f"  [LOG] ハードオフ検索中...")
                        h_res = await search_hardoff(page, kw, genre)
                        res_obj['items'].extend(h_res)
                        
                        # 4. ヤフオク履歴
                        print(f"  [LOG] ヤフオク履歴取得中...")
                        y_history = await fetch_yahoo_auction_history(kw, browser)
                        res_obj['y_history'] = y_history
                        
                    except Exception as e:
                        print(f"  [ERROR] 商品スキップ ({idx}): {e}")
                        res_obj['error'] = str(e)
                        continue
        finally:
            if browser:
                await browser.close()
                print("  [DEBUG] ブラウザを正常に終了しました。")
    except Exception as e:
        import traceback
        print(f"[CRITICAL ERROR] main_process failed: {e}")
        traceback.print_exc()
        LAST_ERROR = str(e)
    finally:
        with SEARCH_STATE_LOCK:
            IS_SEARCHING = False
            IS_FINISHED = True
        print(f"  [LOG] 全行程終了 (Genre: {genre})")

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBay Research Edge - Premium</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.4);
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
            --success: #10b981;
            --danger: #ef4444;
            --yahoo: #ff0033;
        }

        * { box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }

        header {
            max-width: 1200px;
            margin: 0 auto 40px;
            text-align: center;
            padding: 40px;
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 50px rgba(0,0,0,0.3);
        }

        header h1 {
            font-family: 'Outfit', sans-serif;
            font-size: 3rem;
            margin: 0;
            background: linear-gradient(135deg, #fff 0%, var(--accent) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
        }

        #status-badge {
            display: inline-block;
            margin-top: 15px;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            background: rgba(99, 102, 241, 0.2);
            color: var(--accent);
            border: 1px solid var(--accent);
        }

        #container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .product-card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border-radius: 32px;
            padding: 30px;
            margin-bottom: 50px;
            border: 1px solid rgba(255,255,255,0.05);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }

        .main-info {
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
            align-items: flex-start;
        }

        .ebay-img {
            width: 180px;
            height: 180px;
            object-fit: contain;
            background: #fff;
            padding: 10px;
            border-radius: 24px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .product-details { flex: 1; }
        .product-details h2 { margin: 0 0 10px; font-size: 1.8rem; font-family: 'Outfit'; }

        .price-pill {
            display: inline-flex;
            align-items: center;
            background: var(--accent);
            padding: 10px 24px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 1.2rem;
            box-shadow: 0 4px 15px var(--accent-glow);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .stat-box {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .stat-label { font-size: 0.8rem; color: var(--text-dim); margin-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }
        .stat-value { font-size: 1.4rem; font-weight: 700; }

        .market-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }

        .item-card {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 20px;
            padding: 15px;
            border: 1px solid rgba(255,255,255,0.05);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .item-card:hover { transform: translateY(-5px); border-color: var(--accent); background: rgba(99, 102, 241, 0.1); }
        .item-card.selected { border: 2px solid var(--accent); background: rgba(99, 102, 241, 0.15); box-shadow: 0 0 20px var(--accent-glow); }

        .item-img { width: 100%; height: 140px; object-fit: contain; border-radius: 12px; margin-bottom: 12px; background: rgba(255,255,255,0.05); }
        .item-title { font-size: 0.85rem; height: 2.6em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; margin-bottom: 8px; line-height: 1.3; }
        .item-price { font-size: 1.1rem; font-weight: 700; color: var(--accent); }
        .item-site { font-size: 0.75rem; color: var(--text-dim); margin-top: 4px; }

        .ai-analysis {
            background: rgba(30, 41, 59, 0.8);
            border-left: 4px solid var(--accent);
            padding: 20px;
            border-radius: 0 15px 15px 0;
            margin-top: 20px;
            font-size: 0.9rem;
            line-height: 1.6;
        }

        .calc-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }

        .profit-highlight {
            text-align: right;
        }

        .profit-big { font-size: 2.5rem; font-weight: 800; color: var(--success); line-height: 1; }
        .margin-small { font-size: 1.1rem; color: var(--success); opacity: 0.8; font-weight: 600; }

        .pulse { animation: pulse-animation 2s infinite; }
        @keyframes pulse-animation { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <header>
        <h1>eBay Research Edge</h1>
        
        <!-- ジャンル選択フォーム -->
        <div id="genre-selector" style="margin-top:25px; display:flex; gap:10px; justify-content:center; align-items:center; background:rgba(255,255,255,0.05); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.1);">
            <div style="text-align:left;">
                <label style="font-size:0.8rem; color:var(--text-dim); display:block; margin-bottom:5px;">リサーチジャンルを選択</label>
                <select id="genre-history" onchange="document.getElementById('new-genre').value = this.value" style="background:#1e293b; color:white; border:1px solid var(--accent); padding:10px; border-radius:10px; width:200px; outline:none;">
                    <option value="ポケモンカード">ポケモンカード</option>
                </select>
            </div>
            <div style="text-align:left; flex:1; max-width:300px;">
                <label style="font-size:0.8rem; color:var(--text-dim); display:block; margin-bottom:5px;">または新規入力</label>
                <input type="text" id="new-genre" placeholder="例: ワンピースカード" style="background:#1e293b; color:white; border:1px solid var(--accent); padding:10px; border-radius:10px; width:100%; outline:none;">
            </div>
            <button id="start-btn" onclick="startResearch()" style="background:var(--accent); color:white; border:none; padding:12px 30px; border-radius:15px; font-weight:700; cursor:pointer; box-shadow:0 10px 20px var(--accent-glow); margin-top:20px;">リサーチ開始</button>
        </div>

        <div id="status-badge" style="margin-top:20px;">ジャンルを選択してリサーチを開始してください</div>
        
        <div id="main-actions" style="margin-top:20px; display:none;">
            <button onclick="bulkSave()" style="background:var(--success); color:white; border:none; padding:12px 30px; border-radius:30px; font-weight:700; cursor:pointer; box-shadow:0 10px 20px rgba(16,185,129,0.3); font-size:1.1rem; transition:all 0.3s;">📥 表示中の選択アイテムを一括保存</button>
        </div>
    </header>

    <div id="container"></div>

    <script>
        async function update() {
            try {
                const r = await fetch('/data');
                const data = await r.json();
                
                // フォーカス状態を保存
                const activeEl = document.activeElement;
                const activeId = activeEl ? activeEl.id : null;
                const selectionStart = (activeEl && activeEl.tagName === 'INPUT') ? activeEl.selectionStart : null;
                const selectionEnd = (activeEl && activeEl.tagName === 'INPUT') ? activeEl.selectionEnd : null;

                const container = document.getElementById('container');
                
                // 開始ボタンの制御
                const startBtn = document.getElementById('start-btn');
                if (startBtn) {
                    if (data.is_searching) {
                        startBtn.disabled = true;
                        startBtn.innerText = '⌛ リサーチ実行中...';
                        startBtn.style.opacity = '0.6';
                        startBtn.style.cursor = 'not-allowed';
                    } else {
                        startBtn.disabled = false;
                        startBtn.innerText = 'リサーチ開始';
                        startBtn.style.opacity = '1';
                        startBtn.style.cursor = 'pointer';
                    }
                }

                const badge = document.getElementById('status-badge');
                if (data.results.length === 0 && !data.finished && !data.searching_any) {
                    badge.innerText = 'ジャンルを選択してリサーチを開始してください';
                    badge.className = '';
                    document.getElementById('main-actions').style.display = 'none';
                    setTimeout(update, POLLING_INTERVAL); // ここで更新を継続させる
                    return;
                }
                
                document.getElementById('main-actions').style.display = 'block';
                
                // システムエラー表示
                if (data.last_error) {
                    badge.innerHTML = `<span style="color:var(--danger); font-weight:bold;">⚠️ システムエラー: ${data.last_error}</span>`;
                } else {
                    badge.innerText = data.finished ? `COMPLETED (${data.genre})` : `RESEARCHING ${data.genre} (${data.results.length} items found)`;
                }

                if (data.finished) badge.classList.remove('pulse');
                else badge.classList.add('pulse');

                data.results.forEach(res => {
                    let div = document.getElementById('prod-' + res.idx);
                    if (!div) {
                        div = document.createElement('div');
                        div.className = 'product-card';
                        div.id = 'prod-' + res.idx;
                        container.appendChild(div);
                    }

                    let historyHtml = '<div class="stat-box history-box" style="grid-column: span 2; background: rgba(30, 41, 59, 0.5); opacity:0.6; text-align:center; padding:15px;">ヤフオク履歴 取得中...</div>';
                    if (res.y_history) {
                        historyHtml = `
                            <div class="stat-box history-box" style="grid-column: span 2; background: rgba(30, 41, 59, 0.5);">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                                    <span style="font-weight:bold; color:var(--accent);">ヤフオク落札相場 (${res.y_history.count}件)</span>
                                    <a href="${res.y_history.url}" target="_blank" style="font-size:10px; color:var(--accent); text-decoration:none; border:1px solid var(--accent); padding:2px 6px; border-radius:4px;">履歴一覧を開く</a>
                                </div>
                                <div style="display:flex; justify-content:space-around; text-align:center;">
                                    <div><div style="font-size:10px; color:#94a3b8;">最安</div><div style="font-weight:bold;">¥${res.y_history.min.toLocaleString()}</div></div>
                                    <div style="border-left:1px solid #334155;"></div>
                                    <div><div style="font-size:10px; color:var(--accent);">中央値</div><div style="font-weight:bold; color:var(--accent);">¥${res.y_history.median.toLocaleString()}</div></div>
                                    <div style="border-left:1px solid #334155;"></div>
                                    <div><div style="font-size:10px; color:#94a3b8;">最高</div><div style="font-weight:bold;">¥${res.y_history.max.toLocaleString()}</div></div>
                                </div>
                            </div>
                        `;
                    }

                    let marketHtml = '';
                    if (res.searching) {
                        marketHtml = '<div style="grid-column: 1 / -1; text-align:center; padding:60px; color:var(--accent); font-weight:bold; font-size:1.2rem;" class="pulse">🔍 指定されたキーワードで再検索中...</div>';
                    } else {
                        const cards = res.items.map(it => {
                        const titleEscaped = (it.title || 'No Title').replace(/'/g, "\\\\'");
                        const ebayTitleEscaped = (res.ebay_title || '').replace(/'/g, "\\\\'");
                        const img = it.image || 'https://via.placeholder.com/150?text=No+Image';
                        
                        if (!window.productData) window.productData = {};
                        const dataKey = `key-${res.idx}-${it.site}-${it.price}`;
                        window.productData[dataKey] = {
                            res: res,
                            item: it
                        };

                        return `
                            <div class="item-card" 
                                 data-key="${dataKey}"
                                 onclick="selectItem(this, ${it.price}, ${res.ebay_price_jpy || 0}, ${res.fees || 0}, ${res.shipping || 0}, ${res.idx}, '${ebayTitleEscaped}', '${titleEscaped}')">
                                <img src="${img}" class="item-img">
                                <div class="item-title" title="${it.title || ''}">${it.title || 'No Title'}</div>
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <div class="item-price">¥${(it.price || 0).toLocaleString()}</div>
                                    <a href="${it.url}" target="_blank" onclick="event.stopPropagation()" style="font-size:10px; color:var(--accent); text-decoration:none; border:1px solid var(--accent); padding:2px 6px; border-radius:4px;">詳細</a>
                                </div>
                                <div class="item-site">${it.site}</div>
                            </div>
                        `;
                        }).join('');
                        marketHtml = historyHtml + cards;
                    }

                    const ebayPrice = Math.round(res.ebay_price_jpy || 0);
                    
                    // 手入力されたキーワードを優先的に保持
                    if (!window.manualKeywords) window.manualKeywords = {};
                    const currentDiv = document.getElementById('prod-' + res.idx);
                    
                    // サブコンテナがない場合は作成（初期化）
                    if (currentDiv && !currentDiv.querySelector('.info-part')) {
                        currentDiv.innerHTML = `
                            <div class="info-part"></div>
                            <div class="market-part"></div>
                            <div class="footer-part"></div>
                        `;
                    }

                    const kwInput = currentDiv ? currentDiv.querySelector('.kw-input') : null;
                    const isKwFocused = kwInput && document.activeElement === kwInput;
                    
                    // 現在の値を保持
                    if (isKwFocused) window.manualKeywords[res.idx] = kwInput.value;
                    const currentKwValue = window.manualKeywords[res.idx] !== undefined ? window.manualKeywords[res.idx] : (res.keywords ? res.keywords.join(' ') : '');

                    // 1. Info Part (タイトル、入力欄、AI判定)
                    const infoHtml = `
                        <div class="main-info">
                            <img src="${res.ebay_img}" class="ebay-img">
                            <div class="product-details">
                                <h2 style="color:#fff; text-shadow: 0 0 10px rgba(99,102,241,0.5); margin-bottom:15px;">${res.ebay_title}</h2>
                                <div style="display:flex; gap:10px; align-items:center; margin-bottom:15px;">
                                    <div class="price-pill">eBay売価: ¥${ebayPrice.toLocaleString()}</div>
                                    <a href="${res.ebay_url}" target="_blank" style="text-decoration:none; background:rgba(255,255,255,0.1); color:#fff; padding:10px 15px; border-radius:50px; font-size:0.9rem; font-weight:600; border:1px solid rgba(255,255,255,0.2); transition:all 0.3s;">🔗 eBayで開く</a>
                                    <div style="flex:1; display:flex; gap:5px; background:rgba(255,255,255,0.05); padding:5px 15px; border-radius:15px; border:1px solid rgba(255,255,255,0.1);">
                                        <span style="font-size:12px; color:var(--text-dim); align-self:center;">🔍 検索ワード:</span>
                                        <input type="text" id="kw-input-${res.idx}" class="kw-input kw-input-${res.idx}" value="${currentKwValue}" 
                                               oninput="window.manualKeywords[${res.idx}] = this.value"
                                               style="flex:1; background:transparent; border:none; color:#fff; font-size:14px; outline:none; padding:5px;">
                                        <button onclick="researchItem(${res.idx})" style="background:var(--accent); color:white; border:none; padding:5px 15px; border-radius:10px; font-size:12px; cursor:pointer; font-weight:600;">再検索</button>
                                    </div>
                                </div>
                                <div class="ai-analysis" id="ai-${res.idx}">${currentDiv && currentDiv.querySelector('.ai-analysis') ? currentDiv.querySelector('.ai-analysis').innerHTML : 'アイテムを選択してAI判定を開始'}</div>
                                ${res.error ? `<div style="margin-top:10px; padding:10px; background:rgba(239,68,68,0.1); border:1px solid var(--danger); border-radius:10px; color:var(--danger); font-size:12px;">❌ エラー: ${res.error}</div>` : ''}
                            </div>
                        </div>
                    `;

                    // 2. Market Part (検索結果)
                    const marketHtmlWrap = `
                        <div class="market-grid">
                            ${marketHtml}
                        </div>
                    `;

                    // 3. Footer Part (計算機)
                    const footerHtml = `
                        <div class="calc-footer">
                            <div class="stats-grid" style="margin:0; flex:1; display:flex; align-items:center; justify-content:space-between; gap:10px;">
                                <div class="stat-box">
                                    <div class="stat-label">eBay販売価格</div>
                                    <div class="stat-value">¥${ebayPrice.toLocaleString()}</div>
                                </div>
                                <div style="font-size:24px; color:#475569; font-weight:bold;">−</div>
                                <div class="stat-box">
                                    <div class="stat-label">手数料 + 送料</div>
                                    <div class="stat-value">¥${Math.round((res.fees || 0) + (res.shipping || 0)).toLocaleString()}</div>
                                </div>
                                <div style="font-size:24px; color:#475569; font-weight:bold;">−</div>
                                <div class="stat-box">
                                    <div class="stat-label">仕入れ値</div>
                                    <div style="display:flex; align-items:center; gap:2px; color:var(--accent);">
                                        <span>¥</span>
                                        <input type="number" class="purchase-input-${res.idx}" 
                                               value="${res.selected_price || (currentDiv && currentDiv.querySelector('.purchase-input-' + res.idx) ? currentDiv.querySelector('.purchase-input-' + res.idx).value : 0)}" 
                                               oninput="recalc(${res.idx}, ${ebayPrice}, ${Math.round((res.fees || 0) + (res.shipping || 0))})"
                                               style="background:transparent; border:none; border-bottom:1px solid var(--accent); color:var(--accent); font-size:18px; font-weight:bold; width:80px; text-align:center; outline:none;">
                                    </div>
                                </div>
                                <div style="font-size:24px; color:#475569; font-weight:bold;">＝</div>
                                <div class="profit-highlight" style="margin:0; min-width:180px;">
                                    <div class="stat-label">予想利益</div>
                                    <div class="profit-big profit-val-${res.idx}">-</div>
                                    <div class="margin-small margin-val-${res.idx}"></div>
                                </div>
                            </div>
                            <div style="margin-left:20px; display:flex; flex-direction:column; gap:10px;">
                                <button class="save-btn" onclick="saveCurrentItem(${res.idx})" style="background:var(--accent); color:white; border:none; padding:12px 25px; border-radius:12px; font-weight:700; cursor:pointer; box-shadow:0 4px 12px var(--accent-glow); transition:all 0.3s; white-space:nowrap;">💾 この商品を保存</button>
                            </div>
                        </div>
                    `;

                    // 個別に更新 (フォーカスがある場合はスキップ)
                    if (div) {
                        const infoPart = div.querySelector('.info-part');
                        const marketPart = div.querySelector('.market-part');
                        const footerPart = div.querySelector('.footer-part');

                        if (infoPart && infoPart.innerHTML !== infoHtml && !infoPart.contains(document.activeElement)) {
                            infoPart.innerHTML = infoHtml;
                        }
                        if (marketPart && marketPart.innerHTML !== marketHtmlWrap && !marketPart.contains(document.activeElement)) {
                            const selectedIdx = marketPart.querySelector('.item-card.selected') ? Array.from(marketPart.querySelectorAll('.item-card')).indexOf(marketPart.querySelector('.item-card.selected')) : -1;
                            marketPart.innerHTML = marketHtmlWrap;
                            if (selectedIdx !== -1) {
                                const newCards = marketPart.querySelectorAll('.item-card');
                                if (newCards[selectedIdx]) newCards[selectedIdx].classList.add('selected');
                            } else if (!res.searching) {
                                const first = marketPart.querySelector('.item-card');
                                if (first) first.click();
                            }
                        }
                        if (footerPart && footerPart.innerHTML !== footerHtml && !footerPart.contains(document.activeElement)) {
                            footerPart.innerHTML = footerHtml;
                            recalc(res.idx, ebayPrice, Math.round((res.fees || 0) + (res.shipping || 0)));
                        }
                    }
                });

                // フォーカス復元ロジックは上記で対応済みのため削除
                // 最初の10件が終わっても更新を継続
                setTimeout(update, POLLING_INTERVAL);

            } catch (e) {
                console.error("Update error:", e);
                setTimeout(update, 5000);
            }
        }

        async function selectItem(el, p, e, f, s, idx, e_title, d_title) {
            el.parentNode.querySelectorAll('.item-card').forEach(x => x.classList.remove('selected'));
            el.classList.add('selected');

            // Set the value in the editable input box
            const input = document.querySelector('.purchase-input-' + idx);
            if (input) input.value = p;

            recalc(idx, e, f + s);

            const aibox = document.getElementById('ai-' + idx);
            if (aibox) aibox.innerHTML = '<span class="pulse" style="color:var(--accent);">【AI画像判定】 解析中...</span>';

            try {
                const dataKey = el.dataset.key;
                const info = window.productData[dataKey];
                
                const r = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        ebay_title: e_title, 
                        domestic_title: d_title,
                        ebay_img: info.res.ebay_img,
                        domestic_img: el.querySelector('img').src,
                        domestic_url: info.item.url
                    })
                });
                const d = await r.json();
                
                // 【重要】UI更新(update)で要素が置換されている可能性があるため、ここで最新の要素を再取得する
                const currentAiBox = document.getElementById('ai-' + idx);
                if (!currentAiBox) return;

                if (d.success) {
                    const score = d.result.match_score;
                    let color = 'var(--danger)';
                    if (score >= 80) color = 'var(--success)';
                    else if (score >= 50) color = 'var(--warning)';

                    currentAiBox.innerHTML = `<b style="color:${color}">【AI画像判定】 一致度: ${score}%</b><br>${d.result.reason}`;
                } else {
                    currentAiBox.innerText = '判定エラー';
                }
            } catch (e) {
                const currentAiBox = document.getElementById('ai-' + idx);
                if (currentAiBox) currentAiBox.innerText = '通信エラー';
            }
        }

        function recalc(idx, ebayPrice, totalFees) {
            const input = document.querySelector('.purchase-input-' + idx);
            if (!input) return;
            
            const p = parseInt(input.value) || 0;
            const profit = ebayPrice - totalFees - p;
            const margin = ebayPrice > 0 ? (profit / ebayPrice) * 100 : 0;

            const profitEl = document.querySelector('.profit-val-' + idx);
            if (profitEl) {
                profitEl.innerText = '¥' + Math.round(profit).toLocaleString();
                profitEl.style.color = profit > 0 ? 'var(--success)' : 'var(--danger)';
            }
            
            const marginEl = document.querySelector('.margin-val-' + idx);
            if (marginEl) {
                marginEl.innerText = 'ROI: ' + Math.round(margin) + '%';
            }
        }

        function getSaveData(idx) {
            const div = document.getElementById('prod-' + idx);
            const selected = div.querySelector('.item-card.selected');
            if (!selected) return null;
            
            const dataKey = selected.dataset.key;
            const info = window.productData[dataKey];
            const res = info.res;
            const it = info.item;
            
            const input = document.querySelector('.purchase-input-' + idx);
            const manualPrice = input ? (parseInt(input.value) || 0) : it.price;
            
            const profit = Math.round(res.ebay_price_jpy - (res.fees + res.shipping) - manualPrice);
            const roi = res.ebay_price_jpy > 0 ? Math.round((profit / res.ebay_price_jpy) * 100) : 0;
            
            const dateStr = new Date().toLocaleDateString('ja-JP');
            return {
                "date": dateStr,
                "ebay_title": res.ebay_title,
                "ebay_price_usd": res.ebay_price_usd,
                "ebay_price_jpy": Math.round(res.ebay_price_jpy),
                "domestic_title": it.title,
                "domestic_price": manualPrice,
                "domestic_site": it.site,
                "domestic_url": it.url,
                "ebay_fees": Math.round(res.fees),
                "shipping": res.shipping,
                "profit": profit,
                "roi": roi,
                "ebay_img": res.ebay_url,    // 13列目(M)
                "ebay_item_id": res.ebay_item_id, // 14列目(N)
                "status": res.status || '',  // 15列目(O)
                "category": res.genre        // 追加: ジャンル情報
            };
        }

        async function saveCurrentItem(idx) {
            const data = getSaveData(idx);
            if (!data) return alert('アイテムが選択されていません');
            
            const div = document.getElementById('prod-' + idx);
            const btn = div.querySelector('.save-btn');
            await sendToGAS([data], btn);
        }

        async function bulkSave() {
            const itemsToSave = [];
            document.querySelectorAll('.product-card').forEach(div => {
                const idx = div.id.replace('prod-', '');
                const data = getSaveData(idx);
                if (data) itemsToSave.push(data);
            });
            
            if (itemsToSave.length === 0) return alert('保存するアイテムがありません');
            if (!confirm(`${itemsToSave.length}件のアイテムを一括保存しますか？`)) return;
            
            await sendToGAS(itemsToSave, event.target);
        }

        async function sendToGAS(dataList, btn) {
            const originalText = btn.innerText;
            btn.innerText = '⌛ 保存中...';
            btn.disabled = true;

            try {
                const r = await fetch('/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dataList)
                });
                const d = await r.json();
                if (d.success || d.status === 'success') {
                    alert('✅ スプレッドシートに保存しました！');
                    btn.innerText = '✅ 保存完了';
                } else {
                    alert('❌ 保存エラー: ' + (d.error || '不明なエラー'));
                    btn.innerText = originalText;
                    btn.disabled = false;
                }
            } catch (e) {
                alert('❌ 通信エラー');
                btn.innerText = originalText;
                btn.disabled = false;
            }
        }

        async function researchItem(idx) {
            const div = document.getElementById('prod-' + idx);
            const kw = div.querySelector('.kw-input').value;
            const btn = div.querySelector('button');
            const originalText = btn.innerText;
            
            btn.innerText = '⌛...';
            btn.disabled = true;

            try {
                const r = await fetch('/research_item', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ idx: idx, keywords: kw })
                });
                const d = await r.json();
                if (d.success) {
                    console.log('Research started for item ' + idx);
                    update(); // 即座に画面を「再検索中」に切り替える
                } else {
                    alert('エラー: ' + d.error);
                }
            } catch (e) {
                alert('通信エラー');
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        }

        function loadGenreHistory() {
            const history = JSON.parse(localStorage.getItem('ebay_research_genres') || '["ポケモンカード"]');
            const select = document.getElementById('genre-history');
            select.innerHTML = history.map(g => `<option value="${g}">${g}</option>`).join('');
            if (history.length > 0) document.getElementById('new-genre').value = history[0];
        }

        function saveGenreHistory(genre) {
            let history = JSON.parse(localStorage.getItem('ebay_research_genres') || '["ポケモンカード"]');
            if (!history.includes(genre)) {
                history.unshift(genre);
                history = history.slice(0, 10);
                localStorage.setItem('ebay_research_genres', JSON.stringify(history));
            }
        }

        async function startResearch() {
            const genre = document.getElementById('new-genre').value.strip ? document.getElementById('new-genre').value.trim() : document.getElementById('new-genre').value;
            if (!genre) return alert('ジャンルを入力してください');
            
            if (!confirm(`${genre} のリサーチを開始しますか？`)) return;
            
            // 即座にボタンを無効化
            const startBtn = document.getElementById('start-btn');
            if (startBtn) {
                startBtn.disabled = true;
                startBtn.innerText = '⌛ 準備中...';
            }

            saveGenreHistory(genre);
            
            try {
                const r = await fetch('/start-search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ genre: genre })
                });
                const d = await r.json();
                if (d.success) {
                    document.getElementById('container').innerHTML = ''; // 画面クリア
                    update();
                } else {
                    alert('エラー: ' + d.error);
                }
            } catch (e) {
                alert('開始エラー');
            }
        }

        loadGenreHistory();
        update();
    </script>
</body>
</html>"""
    return html.replace("POLLING_INTERVAL", str(config.UI_POLLING_INTERVAL_MS))

@app.route('/data')
def get_data():
    searching_count = sum(1 for r in RESEARCH_RESULTS if r.get('searching'))
    # 全体の完了状態とは別に、個別の検索が動いているかどうかも含めて返す
    return jsonify({
        'results': RESEARCH_RESULTS, 
        'finished': IS_FINISHED,
        'is_searching': IS_SEARCHING,
        'last_error': LAST_ERROR,
        'searching_any': searching_count > 0,
        'genre': CURRENT_GENRE
    })

@app.route('/start-search', methods=['POST'])
def start_search():
    global MAIN_PROCESS_THREAD
    try:
        data = request.json
        genre = data.get('genre', 'ポケモンカード')
        
        # すでに実行中のスレッドがあるか確認
        with SEARCH_STATE_LOCK:
            if IS_SEARCHING:
                return jsonify({'success': False, 'error': 'リサーチが既に実行中です。完了するまでお待ちください。'})
            
            # ロック内で状態を確保
            IS_SEARCHING = True
            IS_FINISHED = False
            LAST_ERROR = None
            CURRENT_GENRE = genre
            
        threading.Thread(target=lambda: asyncio.run(main_process(genre)), daemon=True).start()
        
        return jsonify({'success': True, 'genre': genre})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/research_item', methods=['POST'])
def research_item():
    try:
        data = request.json
        idx = data.get('idx')
        new_kw_str = data.get('keywords', '')
        new_kw = [k.strip() for k in new_kw_str.split(' ') if k.strip()]
        
        # RESEARCH_RESULTSから対象を探す
        res_obj = next((item for item in RESEARCH_RESULTS if item['idx'] == idx), None)
        if not res_obj: return jsonify({'success': False, 'error': 'Item not found'})
        
        # 既存の結果をクリアし、キーワードを更新
        res_obj['items'] = []
        res_obj['keywords'] = new_kw
        res_obj['y_history'] = None
        res_obj['searching'] = True
        
        print(f"  [RE-SEARCH] Item {idx} -> Keywords: {new_kw}")
        
        # バックグラウンドで個別に再検索を実行（元の安定した順次実行を使用）
        async def do_work():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context()
                page = await context.new_page()
                # eBayデータの再取得（IDを固定して商品が変わらないようにする）
                ebay_data = await get_ebay_item_info(get_ebay_token(), res_obj['ebay_title'], item_id=res_obj.get('ebay_item_id'))
                rate = get_exchange_rate()
                res_obj['ebay_img'] = ebay_data['img']
                res_obj['ebay_url'] = ebay_data['url']
                res_obj['ebay_title'] = ebay_data['title']
                # 元のIDが空の場合のみ、新しく取得したIDをセット
                if not res_obj.get('ebay_item_id') and ebay_data.get('id'):
                    res_obj['ebay_item_id'] = ebay_data['id']
                
                if (ebay_data.get('price')):
                    res_obj['ebay_price_usd'] = ebay_data['price']
                    res_obj['ebay_price_jpy'] = ebay_data['price'] * rate
                    # 手数料率をDBから取得
                    cur_fee_rate = FEE_RATES.get(res_obj.get('genre'), FEE_RATES["default"])
                    res_obj['fees'] = (ebay_data['price'] * rate * cur_fee_rate)

                try:
                    # メルカリ
                    m_res = await search_mercari(page, new_kw, res_obj['genre'], is_manual=True)
                    res_obj['items'].extend(m_res)
                    # ヤフーフリマ
                    y_res = await search_yahoo(page, new_kw, res_obj['genre'], is_manual=True)
                    res_obj['items'].extend(y_res)
                    # ハードオフ
                    h_res = await search_hardoff(page, new_kw, res_obj['genre'], is_manual=True)
                    res_obj['items'].extend(h_res)
                    # ヤフオク履歴
                    y_history = await fetch_yahoo_auction_history(new_kw, browser)
                    res_obj['y_history'] = y_history
                except Exception as e:
                    print(f"  [ERR] Re-search failed: {e}")
                finally:
                    res_obj['searching'] = False
                    await browser.close()
        
        threading.Thread(target=lambda: asyncio.run(do_work())).start()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def get_item_description(url):
    try:
        # シンプルなリクエストで説明文の抽出を試みる
        # (JavaScriptが必要な場合はさらに工夫が必要ですが、まずはメタタグや構造から試行)
        r = requests.get(url, timeout=config.REQUEST_TIMEOUT_SECONDS, headers={'User-Agent': 'Mozilla/5.0'})
        if r.status_code == 200:
            # メルカリやヤフオクの構造に合わせて、説明文らしき場所を正規表現で探す
            # メルカリ: "description":"..."  ヤフオク: <div class="ProductExplanation__commentText">
            text = r.text
            # 簡易的な抽出（サイトごとの詳細なパースは後ほど最適化）
            desc_match = re.search(r'"description":"(.*?)"', text)
            if desc_match:
                return desc_match.group(1).encode().decode('unicode_escape')
            
            # HTMLタグを無視してテキストを抽出する簡易ロジック
            clean_text = re.sub(r'<.*?>', '', text)
            return clean_text[:2000] # 長すぎる場合はカット
    except: pass
    return "説明文を取得できませんでした"

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        d = request.json
        ebay_title = d.get('ebay_title', '')
        domestic_title = d.get('domestic_title', '')
        ebay_img = d.get('ebay_img')
        domestic_img = d.get('domestic_img')
        domestic_url = d.get('domestic_url')

        description = ""
        if domestic_url:
            description = get_item_description(domestic_url)

        prompt_text = f"""プロのトレカ鑑定士として、以下の情報を比較・鑑定してください。
        
        [画像1 (左)]: eBayの出品画像（基準）
        [画像2 (右)]: 国内サイトの出品画像（判定対象）
        
        [eBay商品名]: {ebay_title}
        [国内商品名]: {domestic_title}
        [国内商品説明]: {description[:1000]}
        
        [鑑定手順]
        1. 2枚の画像が「全く同じイラスト・カード種別」であるか確認してください。
        2. **重要：商品説明文(国内商品説明)の中に、「観賞用」「展示用」「レプリカ」「海外製」「プロキシ」「replica」といった、非正規品であることを示す文言がないか厳格にチェックしてください。**
        3. 画像から、正規品とは異なる特徴（色味、ロゴ、加工）がないか確認してください。
        
        [判定ルール]
        - **商品説明に「観賞用」「展示用」等の記述がある場合は、画像が本物に見えても一致度を必ず「0」にしてください。**
        - 日本語版と英語版は同一カードとして扱います。
        
        [出力形式]
        JSON形式で {{"match_score": 0-100, "reason": "鑑定結果の理由。特に説明文にレプリカの記述があった場合はそれを明記してください。"}} を返してください。"""

        # 画像を含むメッセージ構成
        content = [{"type": "text", "text": prompt_text}]
        if ebay_img:
            content.append({"type": "image_url", "image_url": {"url": ebay_img}})
        if domestic_img:
            content.append({"type": "image_url", "image_url": {"url": domestic_img}})

        r = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            response_format={"type": "json_object"}
        )
        return jsonify({'success': True, 'result': json.loads(r.choices[0].message.content)})
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save', methods=['POST'])
def save_to_sheet():
    try:
        gas_url = os.getenv('GAS_WEBAPP_URL')
        if not gas_url:
            return jsonify({'success': False, 'error': 'GAS_WEBAPP_URL not set in .env'})
        
        data = request.json # List of items
        r = requests.post(gas_url, json=data, timeout=config.REQUEST_TIMEOUT_SECONDS)
        print(f"  [GAS] Status: {r.status_code}, Response: {r.text}")
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(port=config.SERVER_PORT, debug=False, use_reloader=False), daemon=True).start()
    time.sleep(1)
    webbrowser.open(f"http://127.0.0.1:{config.SERVER_PORT}")
    # asyncio.run(main_process())  <-- 自動開始を停止
    while True: time.sleep(1)
