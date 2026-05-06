import asyncio, os, re, requests, unicodedata, urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import pandas as pd
import webbrowser
import time

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
    price_jpy = price_usd * usd_to_jpy
    return price_jpy * 0.27

def calculate_shipping_cost():
    return 1500

async def search_price(page, site, keywords_list):
    search_query = ' '.join(keywords_list)
    print(f"  🔍 {site} で '{search_query}' を検索中...")
    try:
        if site == 'mercari':
            url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote(search_query)}'
            await page.goto(url, wait_until='load', timeout=15000)
            await page.wait_for_timeout(2000)
            items = await page.locator('a[data-testid="item-card"]').all()
            results = []
            for it in items[:3]:
                try:
                    price_el = await it.locator('span:has-text("¥")').first
                    if price_el:
                        txt = await price_el.text_content()
                        m = re.search(r'¥([\d,]+)', txt)
                        if m:
                            img = await it.locator('img').first
                            img_src = await img.get_attribute('src') if img else None
                            url_item = await it.get_attribute('href')
                            results.append({'price': int(m.group(1).replace(',','')),'image':img_src,'url':url_item})
                except:
                    pass
            print(f"    → {len(results)}件取得")
            return results if results else None
        elif site == 'hardoff':
            url = f'https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote(search_query)}&s=7&p=1'
            await page.goto(url, wait_until='load', timeout=15000)
            await page.wait_for_timeout(2000)
            items = await page.locator('div.itemcolmn_item').all()
            results = []
            for it in items[:3]:
                try:
                    price_el = await it.locator('span.item-price-en').first
                    if price_el:
                        txt = await price_el.text_content()
                        m = re.search(r'[\d,]+', txt)
                        if m:
                            img = await it.locator('img').first
                            img_src = await img.get_attribute('src') if img else None
                            link = await it.locator('a').first
                            href = await link.get_attribute('href') if link else None
                            results.append({'price': int(m.group(0).replace(',','')),'image':img_src,'url':href})
                except:
                    pass
            print(f"    → {len(results)}件取得")
            return results if results else None
        elif site == 'yahoofleamarket':
            try:
                encoded_query = urllib.parse.quote(search_query, safe='')
                url = f'https://paypayfleamarket.yahoo.co.jp/search/{encoded_query}?open=1'
                print(f"      URL: {url}")
                await page.goto(url, wait_until='networkidle', timeout=20000)
                await page.wait_for_timeout(3000)
                exhibits = await page.locator('a[data-cl-params*="exhibit"]').all()
                print(f"      [DEBUG] 検出: {len(exhibits)}件")
                results = []
                for idx, exhibit in enumerate(exhibits[:3]):
                    try:
                        href = await exhibit.get_attribute('href')
                        if not href:
                            continue
                        inner_text = await exhibit.evaluate('el => el.innerText')
                        price_match = re.search(r'(\d+,?\d*)\s*円', inner_text)
                        if price_match:
                            price_str = price_match.group(1).replace(',', '')
                            price = int(price_str)
                        else:
                            continue
                        img_src = await exhibit.evaluate('el => { const img = el.querySelector("img"); if (img) return img.src || img.getAttribute("data-src"); return null; }')
                        results.append({'price': price,'image':img_src,'url':href})
                        print(f"        ✓ 価格: {price}円")
                    except Exception as e:
                        continue
                print(f"    → {len(results)}件取得")
                return results if results else None
            except Exception as e:
                print(f"    ⚠️ ヤフーフリマエラー: {str(e)[:100]}")
                return None
    except Exception as e:
        print(f"    ❌ エラー: {str(e)[:80]}")
    return None

async def main():
    usd_to_jpy = get_exchange_rate()
    print(f"📊 為替レート: 1 USD = ¥{usd_to_jpy:.2f}\n")
    token = get_ebay_token()
    if not token:
        print("❌ eBay トークン取得失敗")
        return
    sheet_id = os.getenv('GOOGLE_SHEETS_ID')
    csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0'
    try:
        df = pd.read_csv(csv_url)
    except Exception as e:
        print(f"❌ スプシ取得失敗: {e}")
        return

    html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBay 売れ筋 × 日本仕入先 リサーチレポート</title>
    <style>
        * { margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        h1 { font-size: 28px; margin-bottom: 10px; }
        .meta { font-size: 14px; opacity: 0.9; }

        .product {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .product h2 {
            color: #333;
            margin-bottom: 15px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }

        .ebay-info {
            background: #f0f8ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }

        .ebay-info p {
            margin: 8px 0;
            font-size: 14px;
        }

        .price {
            font-size: 18px;
            font-weight: bold;
            color: #e74c3c;
        }

        h3 {
            color: #333;
            margin: 20px 0 10px 0;
            font-size: 16px;
        }

        .search-results {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }

        .item {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
            background: #fafafa;
            transition: transform 0.2s;
        }

        .item:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .item img {
            max-width: 100%;
            height: 150px;
            object-fit: cover;
            border-radius: 5px;
            margin-bottom: 10px;
        }

        .item p {
            font-size: 12px;
            color: #333;
            margin: 8px 0;
        }

        .item-price {
            font-size: 16px;
            font-weight: bold;
            color: #27ae60;
        }

        .item a {
            display: inline-block;
            margin-top: 8px;
            padding: 6px 12px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 12px;
        }

        .item a:hover {
            background: #764ba2;
        }

        .profit-analysis {
            background: #f9f9f9;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #27ae60;
        }

        .profit-analysis p {
            margin: 6px 0;
            font-size: 14px;
        }

        .profit-positive {
            color: #27ae60;
            font-weight: bold;
        }

        .profit-negative {
            color: #e74c3c;
            font-weight: bold;
        }

        .notes {
            background: #ffffcc;
            border-radius: 5px;
            padding: 12px;
            margin: 10px 0;
            font-size: 13px;
            border-left: 4px solid #f39c12;
        }

        .no-results {
            color: #999;
            font-style: italic;
            padding: 20px;
            text-align: center;
        }

        footer {
            text-align: center;
            color: #999;
            margin-top: 40px;
            font-size: 12px;
        }
    </style>
</head>
<body>

<div class="container">
    <header>
        <h1>📊 eBay 売れ筋商品 × 日本仕入先 リサーチレポート</h1>
        <div class="meta">
            <p>生成日時: """ + datetime.now().strftime('%Y年%m月%d日 %H:%M:%S') + f"""</p>
            <p>ドル円レート: 1 USD = {usd_to_jpy:.2f} JPY</p>
        </div>
    </header>

    <main>
"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        for idx, row in df.iterrows():
            if idx >= 10: break
            ebay_title = str(row['ebay_title']).strip()
            ebay_price_usd = float(row['ebay_price']) if 'ebay_price' in row else 0
            kw_list = extract_keywords(ebay_title)
            kw_display = '　'.join(kw_list)

            print(f"\n📦 [{idx+1}] {ebay_title[:60]}")
            print(f"  キーワード: {kw_display}")
            print(f"  eBay売値: ${ebay_price_usd:.2f}")

            mercari_results = await search_price(page, 'mercari', kw_list)
            hardoff_results = await search_price(page, 'hardoff', kw_list)
            yahoo_results = await search_price(page, 'yahoofleamarket', kw_list)

            ebay_price_jpy = ebay_price_usd * usd_to_jpy
            ebay_fees = calculate_ebay_fees(ebay_price_usd, usd_to_jpy)
            shipping = calculate_shipping_cost()

            mercari_html = ""
            if mercari_results:
                for res in mercari_results:
                    mercari_html += f"""            <div class="item">
                <img src="{res['image']}" onerror="this.src='https://via.placeholder.com/150';" />
                <p>ポケモンカード</p>
                <p class="item-price">¥{res['price']:,}</p>
                <a href="{res['url']}" target="_blank">詳細</a>
            </div>
"""
            else:
                mercari_html = '            <p class="no-results">見つかりません</p>'

            hardoff_html = ""
            if hardoff_results:
                for res in hardoff_results:
                    hardoff_html += f"""            <div class="item">
                <img src="{res['image']}" onerror="this.src='https://via.placeholder.com/150';" />
                <p>ポケモンカード</p>
                <p class="item-price">¥{res['price']:,}</p>
                <a href="{res['url']}" target="_blank">詳細</a>
            </div>
"""
            else:
                hardoff_html = '            <p class="no-results">見つかりません</p>'

            yahoo_html = ""
            if yahoo_results:
                for res in yahoo_results:
                    yahoo_html += f"""            <div class="item">
                <img src="{res['image']}" onerror="this.src='https://via.placeholder.com/150';" />
                <p>ポケモンカード</p>
                <p class="item-price">¥{res['price']:,}</p>
                <a href="{res['url']}" target="_blank">詳細</a>
            </div>
"""
            else:
                yahoo_html = '            <p class="no-results">見つかりません</p>'

            all_prices = [r['price'] for r in mercari_results or []] + [r['price'] for r in hardoff_results or []] + [r['price'] for r in yahoo_results or []]
            min_price = min(all_prices) if all_prices else None

            if min_price:
                profit = ebay_price_jpy - min_price - ebay_fees - shipping
                profit_rate = (profit / (min_price + ebay_fees + shipping)) * 100 if (min_price + ebay_fees + shipping) > 0 else 0
                profit_class = 'profit-positive' if profit >= 0 else 'profit-negative'
                profit_sign = '✓' if profit >= 0 else '❌'
                profit_html = f"""            <p>仕入最安値: <strong>¥{min_price:,}</strong></p>
            <p>eBay 売価（JPY）: ¥{ebay_price_jpy:,.0f}</p>
            <p>手数料（JPY）: ¥{ebay_fees:,.0f}</p>
            <p>配送料: ¥{shipping:,}</p>
            <p>利益: <span class="{profit_class}">¥{profit:,.0f} ({profit_rate:+.1f}%) {profit_sign}</span></p>
"""
            else:
                profit_html = '            <p>検索結果がないため計算不可</p>'

            html_content += f"""    <div class="product">
        <h2>【{idx+1}】{ebay_title}</h2>

        <div class="ebay-info">
            <p><strong>eBay 情報</strong></p>
            <p>平均価格: <span class="price">${ebay_price_usd:.2f}</span></p>
        </div>

        <h3>🔍 検索キーワード: {kw_display}</h3>

        <h3>メルカリ</h3>
        <div class="search-results">
{mercari_html}
        </div>

        <h3>ハードオフ</h3>
        <div class="search-results">
{hardoff_html}
        </div>

        <h3>ヤフーフリマ</h3>
        <div class="search-results">
{yahoo_html}
        </div>

        <h3>💰 利益分析</h3>
        <div class="profit-analysis">
{profit_html}
        </div>
        <div class="notes">
            <strong>📝 メモ：</strong> 実際の仕入れ前に、検索結果で同じカードか手動で確認してください。
        </div>
    </div>
"""
        await browser.close()

    html_content += """    </main>

    <footer>
        <p>このレポートは参考用です。実際の仕入れ・販売判断は慎重に行ってください。</p>
    </footer>
</div>

</body>
</html>"""

    os.makedirs('data/reports', exist_ok=True)
    report_path = f"data/reports/research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n✅ レポート保存: {report_path}")

    time.sleep(1)
    webbrowser.open(report_path)

asyncio.run(main())
