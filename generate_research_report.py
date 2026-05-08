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
        
        new_page = await asyncio.wait_for(browser.new_page(), timeout=5)
        new_page.set_default_timeout(5000)
        
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        
        await asyncio.wait_for(new_page.goto(url, wait_until='domcontentloaded'), timeout=8)
        await new_page.wait_for_timeout(1000)
        
        text = await new_page.evaluate('() => document.body.innerText')
        await new_page.close()
        
        min_match = re.search(r'最安\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最高\s*(\d+,?\d*)\s*円', text)
        
        if min_match and avg_match and max_match:
            return {
                'min': int(min_match.group(1).replace(',', '')),
                'avg': int(avg_match.group(1).replace(',', '')),
                'max': int(max_match.group(1).replace(',', ''))
            }
    except asyncio.TimeoutError:
        print(f'Yahoo timeout for: {search_query}')
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
    mapping = {'manaphy':'マナフィ','charizard':'リザードン','pikachu':'ピカチュウ','blastoise':'カメックス','venusaur':'フシギバナ','gengar':'ゲンガー','articuno':'フリーザー'}
    for en, ja in mapping.items():
        if en in t: kw.append(ja); break
    if 'sar' in t: kw.append('SAR')
    m = re.search(r'(\d+/[A-Z0-9]+)', title.upper())
    if m: kw.append(m.group(1))
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
                    const img = el.querySelector('img');
                    let title = img ? img.alt : "";
                    if (!title || title.includes('¥')) {
                        title = el.getAttribute('aria-label') || "";
                    }
                    // 価格部分を削除 (例: "商品名 ¥1,000" -> "商品名")
                    title = title.replace(/¥\s?[\d,]+/g, '').trim();
                    return {
                        title: title,
                        price: el.innerText,
                        href: el.href,
                        img: img ? img.src : "",
                        html: el.innerHTML
                    }
                }""")
                if any(x in d['price'] or x in d['title'] or x in d['html'] for x in ["入札", "オークション", "現在", "残り", "〜"]): continue
                m = re.search(r'¥\s*([\d,]+)', d['price'])
                if m:
                    price = int(m.group(1).replace(',',''))
                    if price < 100 or "盗難防止" in d['title'] or "盗難防止" in d['html']: continue
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
                if any(x in d['price'] or x in d['html'] for x in ["入札", "オークション", "現在", "残り", "〜", "盗難防止"]): continue
                if "盗難防止" in d['title']: continue
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
                    const link = el.querySelector('a[href*="/product/"]');
                    const img = el.querySelector('img');
                    let title = img ? img.alt : "";
                    if (!title) {
                        const titleEl = el.querySelector('.item-name, h2, h3');
                        title = titleEl ? titleEl.innerText : "";
                    }
                    const text = el.innerText;
                    const p = text.match(/[\\d,]+/g);
                    return { 
                        title: title.trim(), 
                        price: p ? p[p.length-1] : "0", 
                        href: link ? link.href : "", 
                        img: img ? img.src : "" 
                    }
                }""")
                if data['href']:
                    price = int(data['price'].replace(',',''))
                    if price >= 100 and "盗難防止" not in data['title']:
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
                print("DEBUG: About to call fetch_yahoo_auction_history")
                y_history = await fetch_yahoo_auction_history(kw, browser)
                print(f"DEBUG: y_history result = {y_history}")
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

        .yahoo-history-box {
            grid-column: 1 / -1;
            background: linear-gradient(90deg, rgba(255, 0, 51, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
            border: 1px solid rgba(255, 0, 51, 0.3);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            justify-content: space-around;
            align-items: center;
        }

        .yahoo-stat { text-align: center; }
        .yahoo-stat .val { font-size: 1.5rem; font-weight: 800; color: #fff; }
        .yahoo-stat .label { font-size: 0.7rem; color: #ff9999; text-transform: uppercase; }

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

                    // ヤフオク履歴の詳細リンク生成
                    const encodedKw = encodeURIComponent((res.keywords || []).join(' '));
                    const yahooHistoryUrl = `https://auctions.yahoo.co.jp/closedsearch/closedsearch?p=${encodedKw}&va=${encodedKw}&b=1&n=50`;

                    const historyHtml = res.y_history ? `
                        <div class="yahoo-history-box">
                            <div style="text-align:center;">
                                <div style="font-weight:700; color:#ff0033;">ヤフオク履歴</div>
                                <a href="${yahooHistoryUrl}" target="_blank" style="font-size:10px; color:#fff; opacity:0.7;">履歴一覧を開く</a>
                            </div>
                            <div class="yahoo-stat"><div class="label">最安</div><div class="val">¥${res.y_history.min.toLocaleString()}</div></div>
                            <div class="yahoo-stat"><div class="label">平均</div><div class="val">¥${res.y_history.avg.toLocaleString()}</div></div>
                            <div class="yahoo-stat"><div class="label">最高</div><div class="val">¥${res.y_history.max.toLocaleString()}</div></div>
                        </div>
                    ` : '<div class="yahoo-history-box" style="opacity:0.5;">ヤフオク履歴 取得中...</div>';

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
                                    <div class="stat-value purchase-price-${res.idx}" style="color:var(--accent);">-</div>
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

            const profit = e - (f + s) - p;
            const margin = e > 0 ? (profit / e) * 100 : 0;

            document.querySelector('.purchase-price-' + idx).innerText = '¥' + p.toLocaleString();
            const profitEl = document.querySelector('.profit-val-' + idx);
            profitEl.innerText = '¥' + Math.round(profit).toLocaleString();
            profitEl.style.color = profit > 0 ? 'var(--success)' : 'var(--danger)';
            
            document.querySelector('.margin-val-' + idx).innerText = 'ROI: ' + Math.round(margin) + '%';

            const aibox = document.getElementById('ai-' + idx);
            aibox.innerHTML = '<span class="pulse" style="color:var(--accent);">【AIプロ判定】 解析中...</span>';

            try {
                const r = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ebay_title: e_title, domestic_title: d_title })
                });
                const d = await r.json();
                if (d.success) {
                    aibox.innerHTML = `<b>【AIプロ判定】 一致度: ${d.result.match_score}%</b><br>${d.result.reason}`;
                } else {
                    aibox.innerText = '判定エラー';
                }
            } catch (e) {
                aibox.innerText = '通信エラー';
            }
        }

        async function saveCurrentItem(idx) {
            const div = document.getElementById('prod-' + idx);
            const selected = div.querySelector('.item-card.selected');
            if (!selected) return alert('アイテムが選択されていません');
            
            const itemData = JSON.parse(selected.dataset.fullInfo);
            const btn = div.querySelector('.save-btn');
            await sendToGAS([itemData], btn);
        }

        async function bulkSave() {
            const itemsToSave = [];
            document.querySelectorAll('.product-card').forEach(div => {
                const selected = div.querySelector('.item-card.selected');
                if (selected) {
                    itemsToSave.push(JSON.parse(selected.dataset.fullInfo));
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

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        d = request.json
        p = f"""プロのトレカ鑑定士として、以下の2つの商品が「同一のカード種別」であるかを厳格に判定してください。
        
        [eBay商品名]: {d['ebay_title']}
        [国内商品名]: {d['domestic_title']}
        
        [判定基準]
        1. ポケモン名が一致しているか。
        2. 型番・コレクター番号（例: 004/PPP, 110/080）が一致しているか。これが一致していればほぼ同一です。
        3. レアリティ（SAR, SR, SA, プロモ等）が一致しているか。
        
        [重要ルール]
        - 型番（番号/記号）が一致している場合は、一致度(match_score)を必ず「90%以上」にしてください。
        - 言語の違い（日本語/英語）は同一カードとして扱い、減点しないでください。
        
        [出力形式]
        JSON形式で {{"match_score": 0-100の数値, "reason": "日本語での簡潔な理由"}} を返してください。"""
        r = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": p}], response_format={"type": "json_object"})
        return jsonify({'success': True, 'result': json.loads(r.choices[0].message.content)})
    except: return jsonify({'success': False})

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
