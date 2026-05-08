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

# 🏆 V15.1: カタログページ完全排除版 (No Catalog Hub)
# ヤフーフリマの「製品カタログ(/product/)」を排除し、個別の出品物(/item/)のみを対象に。

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESEARCH_RESULTS = []
IS_FINISHED = False

def parse_currency(value):
    if pd.isna(value): return 0.0
    v = re.sub(r'[^\d.]', '', str(value))
    try: return float(v)
    except: return 0.0

def get_exchange_rate():
    try:
        r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        return r.json()['rates']['JPY']
    except: return 157.50

def get_ebay_token():
    try:
        r = requests.post('https://api.ebay.com/identity/v1/oauth2/token', 
                          auth=(os.getenv('EBAY_REST_CLIENT_ID'), os.getenv('EBAY_REST_CLIENT_SECRET')), 
                          data={'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'}, timeout=10)
        return r.json().get('access_token')
    except: return None

async def fetch_yahoo_auction_history(search_query, browser):
    try:
        if isinstance(search_query, list):
            search_query = ' '.join(search_query)
        
        new_page = await asyncio.wait_for(browser.new_page(), timeout=10)
        # より広範囲のクラス名で価格を取得
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        
        await asyncio.wait_for(new_page.goto(url, wait_until='domcontentloaded'), timeout=15)
        await new_page.wait_for_timeout(1500)
        
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


async def get_ebay_image(token, title):
    if not token: return 'https://via.placeholder.com/300'
    try:
        url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={urllib.parse.quote(title)}&limit=1"
        r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if 'itemSummaries' in data and data['itemSummaries']:
                return data['itemSummaries'][0].get('image', {}).get('imageUrl', 'https://via.placeholder.com/300')
    except: pass
    return 'https://via.placeholder.com/300'

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
        
    return kw

async def search_mercari(page, kw):
    if not kw: return []
    query = ' '.join(kw)
    try:
        url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote(query, safe="")}&status=on_sale'
        await page.goto(url, timeout=20000)
        await page.wait_for_timeout(1500)
        items = await page.locator('a[href^="/item/m"]').all()
        res = []
        for it in items[:15]:
            try:
                d = await it.evaluate("""el => {
                    const imgDiv = el.querySelector('div[aria-label]');
                    const img = el.querySelector('img');
                    let rawTitle = imgDiv ? imgDiv.getAttribute('aria-label') : (img ? img.alt : "");
                    // 「の画像」や「のサムネイル」以降を削除し、さらに価格表示があれば削除
                    let title = rawTitle.replace(/の(画像|サムネイル).*$/, "").replace(/¥\s?[\d,]+/, "").trim();
                    return {
                        title: title,
                        price: el.innerText,
                        href: el.href,
                        img: img ? img.src : "",
                        html: el.innerHTML
                    }
                }""")
                if not d['title']:
                    print(f"DEBUG: Mercari title empty for {d['href']}")
                
                exclude_kws = ["入札", "オークション", "現在", "残り", "〜", "盗難防止", "観賞用", "展示用", "レプリカ"]
                if any(x in d.get('price','') or x in d.get('title','') or x in d.get('html','') for x in exclude_kws): continue
                m = re.search(r'¥\s*([\d,]+)', d['price'])
                if m:
                    price = int(m.group(1).replace(',',''))
                    if price < 100: continue
                    res.append({'price':price, 'title':d['title'], 'url':d['href'], 'image':d['img'], 'site':'メルカリ'})
            except: continue
        return res[:5]
    except: return []

async def search_yahoo(page, kw):
    if not kw: return []
    query = ' '.join(kw)
    try:
        url = f"https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote(query, safe='')}?open=1"
        await page.goto(url, timeout=20000)
        await page.wait_for_timeout(2000)
        # 【重要】/product/ はカタログページのため排除し、/item/ のみを取得
        items = await page.locator('a[href^="/item/"]').all()
        res = []
        for it in items[:15]:
            try:
                d = await it.evaluate("""el => {
                    const img = el.querySelector('img');
                    let title = img ? img.alt : "";
                    if (!title) {
                        const titleEl = el.querySelector('p, span[class*="title"]');
                        title = titleEl ? titleEl.innerText : "";
                    }
                    // 不要な改行や価格情報を掃除
                    title = title.split('\\n')[0].replace(/¥\s?[\d,]+/g, '').trim();
                    return {
                        title: title || "ヤフーフリマ商品",
                        price: el.innerText,
                        href: el.getAttribute('href'),
                        img: img ? img.src : "",
                        html: el.innerHTML
                    }
                }""")
                exclude_kws = ["盗難防止", "観賞用", "展示用", "レプリカ"]
                if any(x in d['title'] or x in d['html'] for x in exclude_kws): continue
                href = d['href']
                if href:
                    if href.startswith('/'): href = "https://paypayfleamarket.yahoo.co.jp" + href
                    m = re.search(r'([\d,]+)', d['price'].replace(',',''))
                    if m:
                        price = int(m.group(1))
                        if price < 100: continue
                        res.append({'price':price, 'title':d['title'] or "ヤフーフリマ商品", 'url':href, 'image':d['img'], 'site':'ヤフーフリマ'})
            except: continue
        return res[:5]
    except: return []

async def search_hardoff(page, kw):
    if not kw: return []
    query = ' '.join(kw)
    try:
        url = f'https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote("ポケモンカード " + query)}'
        await page.goto(url, timeout=20000)
        await page.wait_for_timeout(1500)
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
                    exclude_kws = ["盗難防止", "観賞用", "展示用", "レプリカ"]
                    if price >= 100 and not any(x in data['title'] for x in exclude_kws):
                        res.append({'price':price, 'title':data['title'], 'url':data['href'], 'image':data['img'], 'site':'ハードオフ'})
            except: continue
        return res
    except: return []

async def main_process():
    global IS_FINISHED
    rate = get_exchange_rate()
    ebay_token = get_ebay_token()
    sheet_id = os.getenv('GOOGLE_SHEETS_ID')
    df = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        for idx, row in df.iterrows():
            if idx >= 10: break
            try:
                title = str(row.get('ebay_title', 'Unknown'))
                usd = parse_currency(row.get('avg_price_usd', 0))
                kw = extract_keywords(title)
                print(f"[SEARCH] [{idx+1}/10] {title} ...")
                
                ebay_img = await get_ebay_image(ebay_token, title)
                
                # [NEW] リアルタイム更新のために空のオブジェクトを先に追加
                res_obj = {
                    'idx': idx,
                    'ebay_title': title,
                    'ebay_img': ebay_img,
                    'ebay_price_usd': usd,
                    'ebay_price_jpy': usd * rate,
                    'fees': (usd * rate * 0.1135),
                    'shipping': 1500,
                    'items': [],
                    'keywords': kw,
                    'y_history': None
                }
                RESEARCH_RESULTS.append(res_obj)

                # 1. メルカリ
                m_res = await search_mercari(page, kw)
                res_obj['items'].extend(m_res)
                
                # 2. ヤフーフリマ
                y_res = await search_yahoo(page, kw)
                res_obj['items'].extend(y_res)
                
                # 3. ハードオフ
                h_res = await search_hardoff(page, kw)
                res_obj['items'].extend(h_res)
                
                # 4. ヤフオク履歴
                y_history = await fetch_yahoo_auction_history(kw, browser)
                res_obj['y_history'] = y_history
                
            except Exception as e:
                import traceback
                print(f"[ERROR] Error: {e}")
                traceback.print_exc()
        await browser.close()
    IS_FINISHED = True

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return """<!DOCTYPE html>
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
        <div id="status-badge" class="pulse">Initializing...</div>
        <div style="margin-top:20px;">
            <button onclick="bulkSave()" style="background:var(--success); color:white; border:none; padding:12px 30px; border-radius:30px; font-weight:700; cursor:pointer; box-shadow:0 10px 20px rgba(16,185,129,0.3); font-size:1.1rem; transition:all 0.3s;">📥 表示中の選択アイテムを一括保存</button>
        </div>
    </header>

    <div id="container"></div>

    <script>
        async function update() {
            try {
                const r = await fetch('/data');
                const data = await r.json();
                const container = document.getElementById('container');
                
                const badge = document.getElementById('status-badge');
                badge.innerText = data.finished ? 'COMPLETED' : `RESEARCHING (${data.results.length} items found)`;
                if (data.finished) badge.classList.remove('pulse');

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

                    const cards = res.items.map(it => {
                        const titleEscaped = (it.title || 'No Title').replace(/'/g, "\\\\'");
                        const ebayTitleEscaped = (res.ebay_title || '').replace(/'/g, "\\\\'");
                        const img = it.image || 'https://via.placeholder.com/150?text=No+Image';
                        
                        const fullInfo = JSON.stringify({
                            ebay_title: res.ebay_title,
                            ebay_price_usd: res.ebay_price_usd,
                            ebay_price_jpy: Math.round(res.ebay_price_jpy),
                            domestic_title: it.title,
                            domestic_price: it.price,
                            domestic_site: it.site,
                            domestic_url: it.url,
                            ebay_fees: Math.round(res.fees),
                            shipping: res.shipping,
                            profit: Math.round(res.ebay_price_jpy - (res.fees + res.shipping) - it.price),
                            roi: Math.round(((res.ebay_price_jpy - (res.fees + res.shipping) - it.price) / res.ebay_price_jpy) * 100),
                            ebay_img: res.ebay_img
                        }).replace(/"/g, '&quot;');

                        return `
                            <div class="item-card" 
                                 data-full-info="${fullInfo}"
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

                    const ebayPrice = Math.round(res.ebay_price_jpy || 0);
                    const content = `
                        <div class="main-info">
                            <img src="${res.ebay_img}" class="ebay-img">
                            <div class="product-details">
                                <h2 style="color:#fff; text-shadow: 0 0 10px rgba(99,102,241,0.5);">${res.ebay_title}</h2>
                                <div class="price-pill">eBay売価: ¥${ebayPrice.toLocaleString()}</div>
                                <div class="ai-analysis" id="ai-${res.idx}">アイテムを選択してAI判定を開始</div>
                            </div>
                        </div>

                        <div class="market-grid">
                            ${historyHtml}
                            ${cards}
                        </div>

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
                                               value="${res.selected_price || 0}" 
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

                    if (div.dataset.content !== content) {
                        div.innerHTML = content;
                        div.dataset.content = content;
                        if (!div.querySelector('.item-card.selected')) {
                            const first = div.querySelector('.item-card');
                            if (first) first.click();
                        }
                    }
                });

                if (!data.finished) setTimeout(update, 3000);
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
            aibox.innerHTML = '<span class="pulse" style="color:var(--accent);">【AI画像判定】 解析中...</span>';

            try {
                const itemData = JSON.parse(el.dataset.fullInfo);
                const r = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        ebay_title: e_title, 
                        domestic_title: d_title,
                        ebay_img: itemData.ebay_img,
                        domestic_img: el.querySelector('img').src,
                        domestic_url: itemData.domestic_url
                    })
                });
                const d = await r.json();
                if (d.success) {
                    const score = d.result.match_score;
                    let color = 'var(--danger)';
                    if (score >= 80) color = 'var(--success)';
                    else if (score >= 50) color = 'var(--warning)';

                    aibox.innerHTML = `<b style="color:${color}">【AI画像判定】 一致度: ${score}%</b><br>${d.result.reason}`;
                } else {
                    aibox.innerText = '判定エラー';
                }
            } catch (e) {
                aibox.innerText = '通信エラー';
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

        async function saveCurrentItem(idx) {
            const div = document.getElementById('prod-' + idx);
            const selected = div.querySelector('.item-card.selected');
            if (!selected) return alert('アイテムが選択されていません');
            
            const itemData = JSON.parse(selected.dataset.fullInfo);
            
            // Override price with manual input value
            const input = document.querySelector('.purchase-input-' + idx);
            if (input) {
                const manualPrice = parseInt(input.value) || 0;
                itemData.domestic_price = manualPrice;
                // Also update profit and ROI based on manual price for the spreadsheet
                const ebayPriceJpy = itemData.ebay_price_jpy || 0;
                const fees = itemData.ebay_fees || 0;
                const shipping = itemData.shipping || 0;
                itemData.profit = Math.round(ebayPriceJpy - (fees + shipping) - manualPrice);
                itemData.roi = ebayPriceJpy > 0 ? Math.round((itemData.profit / ebayPriceJpy) * 100) : 0;
            }

            const btn = div.querySelector('.save-btn');
            await sendToGAS([itemData], btn);
        }

        async function bulkSave() {
            const itemsToSave = [];
            document.querySelectorAll('.product-card').forEach(div => {
                const selected = div.querySelector('.item-card.selected');
                if (selected) {
                    const itemData = JSON.parse(selected.dataset.fullInfo);
                    const idx = itemData.idx;
                    const input = document.querySelector('.purchase-input-' + idx);
                    if (input) {
                        const manualPrice = parseInt(input.value) || 0;
                        itemData.domestic_price = manualPrice;
                        const ebayPriceJpy = itemData.ebay_price_jpy || 0;
                        const fees = itemData.ebay_fees || 0;
                        const shipping = itemData.shipping || 0;
                        itemData.profit = Math.round(ebayPriceJpy - (fees + shipping) - manualPrice);
                        itemData.roi = ebayPriceJpy > 0 ? Math.round((itemData.profit / ebayPriceJpy) * 100) : 0;
                    }
                    itemsToSave.push(itemData);
                }
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
                if (d.success) {
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

        update();
    </script>
</body>
</html>"""

@app.route('/data')
def get_data():
    return jsonify({'results': RESEARCH_RESULTS, 'finished': IS_FINISHED})

def get_item_description(url):
    try:
        # シンプルなリクエストで説明文の抽出を試みる
        # (JavaScriptが必要な場合はさらに工夫が必要ですが、まずはメタタグや構造から試行)
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
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
        r = requests.post(gas_url, json=data, timeout=15)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(port=5009, debug=False, use_reloader=False), daemon=True).start()
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:5009")
    asyncio.run(main_process())
    while True: time.sleep(1)
