import asyncio, os, re, requests, unicodedata, urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import pandas as pd, webbrowser

load_dotenv()

def get_exchange_rate():
    try:
        r = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=10)
        if r.status_code == 200:
            return r.json()['rates']['JPY']
    except:
        pass
    return 157.12

def get_ebay_token():
    client_id = os.getenv('EBAY_REST_CLIENT_ID')
    client_secret = os.getenv('EBAY_REST_CLIENT_SECRET')
    auth = (client_id, client_secret)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'}
    try:
        r = requests.post('https://api.ebay.com/identity/v1/oauth2/token', auth=auth, headers=headers, data=data, timeout=10)
        if r.status_code == 200:
            return r.json()['access_token']
    except Exception as e:
        print(f"⚠️ トークン取得エラー: {e}")
    return None

def extract_keywords(title):
    kw = []
    t = unicodedata.normalize('NFKD', title).lower()
    mapping = {'manaphy':'マナフィ','charizard':'リザードン','pikachu':'ピカチュウ','blastoise':'フリーザー','venusaur':'フシギバナ','gengar':'ゲンガー'}
    for en, ja in mapping.items():
        if en in t:
            kw.append(ja)
            break
    if 'mega' in t: kw.append('メガ')
    if ' ex ' in t or t.endswith('ex'): kw.append('EX')
    if 'sar' in t: kw.append('SAR')
    m = re.search(r'(\d+/PPP)', title, re.I)
    if m: kw.append(m.group(1))
    return kw

def calculate_ebay_fees(price_usd, usd_to_jpy):
    return price_usd * usd_to_jpy * 0.27

def calculate_shipping_cost():
    return 1500

async def search_price(page, site, keywords_list):
    query = ' '.join(keywords_list)
    print(f"🔍 {site} で '{query}' を検索中...")
    
    if site == 'mercari':
        url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote(query)}'
        await page.goto(url, wait_until='load', timeout=15000)
        await page.wait_for_timeout(2000)
        items = await page.locator('a[data-testid="item-card"]').all()
        results = []
        for it in items[:3]:
            try:
                txt = await it.locator('span:has-text("¥")').first.text_content()
                m = re.search(r'¥([\d,]+)', txt)
                if m:
                    price = int(m.group(1).replace(',',''))
                    img = await it.locator('img').first.get_attribute('src')
                    href = await it.get_attribute('href')
                    results.append({'price':price,'image':img,'url':href})
            except:
                pass
        print(f" → {len(results)}件取得")
        return results if results else None
    
    elif site == 'hardoff':
        url = f'https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote(query)}&s=7&p=1'
        await page.goto(url, wait_until='load', timeout=15000)
        await page.wait_for_timeout(2000)
        items = await page.locator('div.itemcolmn_item').all()
        results = []
        for it in items[:3]:
            try:
                txt = await it.locator('span.item-price-en').first.text_content()
                m = re.search(r'[\d,]+', txt)
                if m:
                    price = int(m.group(0).replace(',',''))
                    img = await it.locator('img').first.get_attribute('src')
                    href = await it.locator('a').first.get_attribute('href')
                    results.append({'price':price,'image':img,'url':href})
            except:
                pass
        print(f" → {len(results)}件取得")
        return results if results else None
    
    elif site == 'yahoofleamarket':
        encoded_query = urllib.parse.quote(query, safe='')
        url = f'https://paypayfleamarket.yahoo.co.jp/search/{encoded_query}?open=1'
        print(f"      URL: {url}")
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # 修正: a[data-cl-params*="exhibit"] を使用（販売中の商品のみ）
        items = await page.locator('a[data-cl-params*="exhibit"]').all()
        results = []
        for it in items[:3]:
            try:
                # 価格を含む span を探す
                price_txt = await it.locator('text=/円/').first.text_content()
                # "1,234円" または "1,234 円" の形式から抽出
                m = re.search(r'([\d,]+)\s*円', price_txt)
                if m:
                    price = int(m.group(1).replace(',',''))
                    # 画像を取得
                    img = await it.locator('img').first.get_attribute('src')
                    href = await it.get_attribute('href')
                    results.append({'price':price,'image':img,'url':href})
            except:
                pass
        print(f" → {len(results)}件取得")
        return results if results else None
    
    return None

async def main():
    usd_to_jpy = get_exchange_rate()
    print(f"📊 為替レート: 1 USD = ¥{usd_to_jpy:.2f}\n")
    token = get_ebay_token()
    if not token:
        print('❌ eBay トークン取得失敗')
        return
    
    csv_url = f"https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SHEETS_ID')}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        print(f"❌ スプシ取得失敗: {e}")
        return
    
    html_content = """<!DOCTYPE html>
<html lang='ja'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>eBay ポケモンカード リサーチレポート</title>
<style>
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }
.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; }
.exchange-rate { background: #e8f4f8; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
.product-block { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.price-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin: 15px 0; }
.price-item { background: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 4px solid #667eea; }
.price-item strong { color: #667eea; }
.profit-positive { color: #2ecc71; font-weight: bold; }
.profit-negative { color: #e74c3c; font-weight: bold; }
.images { display: flex; gap: 10px; margin: 15px 0; flex-wrap: wrap; }
.images img { max-width: 120px; max-height: 120px; border-radius: 5px; }
.timestamp { text-align: center; margin-top: 40px; color: #999; font-size: 0.9em; }
</style>
</head>
<body>
<div class='header'>
<h1>📊 eBay ポケモンカード リサーチレポート</h1>
<p>最安仕入価格と eBay 売値から利益分析</p>
</div>
<div class='exchange-rate'>
<strong>📈 為替レート:</strong> 1 USD = ¥{:.2f}
</div>
<main>
""".format(usd_to_jpy)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        for idx, row in df.iterrows():
            if idx >= 10:
                break
            
            ebay_title = str(row['ebay_title']).strip()
            ebay_price_usd = float(row['ebay_price']) if 'ebay_price' in row else 0
            kw_list = extract_keywords(ebay_title)
            kw_display = '　'.join(kw_list)
            
            print(f"\n📦 [{idx+1}] {ebay_title[:60]}")
            
            mercari = await search_price(page, 'mercari', kw_list)
            hardoff = await search_price(page, 'hardoff', kw_list)
            yahoo = await search_price(page, 'yahoofleamarket', kw_list)
            
            # 利益計算
            ebay_jpy = ebay_price_usd * usd_to_jpy
            fees = calculate_ebay_fees(ebay_price_usd, usd_to_jpy)
            ship = calculate_shipping_cost()
            
            all_prices = []
            if mercari:
                all_prices.extend([r['price'] for r in mercari])
            if hardoff:
                all_prices.extend([r['price'] for r in hardoff])
            if yahoo:
                all_prices.extend([r['price'] for r in yahoo])
            
            min_price = min(all_prices) if all_prices else None
            
            if min_price:
                profit = ebay_jpy - min_price - fees - ship
                profit_rate = (profit / (min_price + fees + ship) * 100) if (min_price + fees + ship) > 0 else 0
                profit_class = 'profit-positive' if profit >= 0 else 'profit-negative'
                profit_sign = '✓' if profit >= 0 else '❌'
                profit_html = f"""
                <p><strong>仕入最安値:</strong> ¥{min_price:,}</p>
                <p><strong>eBay 売値:</strong> ${ebay_price_usd:.2f} (¥{ebay_jpy:,.0f})</p>
                <p><strong>eBay 手数料:</strong> ¥{fees:,.0f}</p>
                <p><strong>国際配送料:</strong> ¥{ship:,}</p>
                <p class='{profit_class}'>{profit_sign} <strong>利益:</strong> ¥{profit:,.0f} ({profit_rate:.1f}%)</p>
                """
            else:
                profit_html = '<p>⚠️ 検索結果がないため利益計算不可</p>'
            
            # HTML に商品ブロックを追加
            html_content += f"""
<div class='product-block'>
<h2>{ebay_title}</h2>
<p><strong>キーワード:</strong> {kw_display}</p>
<div class='price-grid'>
"""
            
            if mercari:
                html_content += f"""
<div class='price-item'>
<strong>メルカリ:</strong><br>
¥{mercari[0]['price']:,}<br>
<a href='{mercari[0]['url']}' target='_blank'>詳細</a>
</div>
"""
            else:
                html_content += '<div class="price-item"><strong>メルカリ:</strong><br>検索結果なし</div>'
            
            if hardoff:
                html_content += f"""
<div class='price-item'>
<strong>ハードオフ:</strong><br>
¥{hardoff[0]['price']:,}<br>
<a href='{hardoff[0]['url']}' target='_blank'>詳細</a>
</div>
"""
            else:
                html_content += '<div class="price-item"><strong>ハードオフ:</strong><br>検索結果なし</div>'
            
            if yahoo:
                html_content += f"""
<div class='price-item'>
<strong>ヤフーフリマ:</strong><br>
¥{yahoo[0]['price']:,}<br>
<a href='{yahoo[0]['url']}' target='_blank'>詳細</a>
</div>
"""
            else:
                html_content += '<div class="price-item"><strong>ヤフーフリマ:</strong><br>検索結果なし</div>'
            
            html_content += f"""
</div>
{profit_html}
<div class='images'>
"""
            
            for result_list in [mercari, hardoff, yahoo]:
                if result_list and result_list[0].get('image'):
                    html_content += f"<img src='{result_list[0]['image']}' alt='商品画像'>"
            
            html_content += """
</div>
</div>
"""
        
        await browser.close()
    
    html_content += """
</main>
<div class='timestamp'>
レポート生成: """ + datetime.now().strftime('%Y年%m月%d日 %H:%M:%S') + """
</div>
</body>
</html>
"""
    
    os.makedirs('data/reports', exist_ok=True)
    report_path = f"data/reports/research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ レポート保存: {report_path}")
    webbrowser.open(report_path)

asyncio.run(main())
