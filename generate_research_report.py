import asyncio, os, re, requests, unicodedata, urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import pandas as pd
import webbrowser
import time

load_dotenv()

def parse_currency(value):
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # Remove '$', ',', and other non-numeric except '.'
    clean_value = re.sub(r'[^\d.]', '', str(value))
    try:
        return float(clean_value)
    except:
        return 0.0

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
    return price_jpy * 0.1135

def calculate_shipping_cost():
    return 1500

def is_relevant(title, keywords):
    if not title:
        return False
    title_norm = unicodedata.normalize('NFKD', str(title)).lower()
    
    # Exclude obvious garbage and accessories
    exclude_list = ["展示用", "まとめ売り", "確認用", "box", "空箱", "フレーム", "パック", "ケース", "シュリンク", "ボックス", "セット", "まとめ", "フィギュア", "ぬいぐるみ", "キーホルダー", "ポスター", "スリーブ", "台座"]
    for word in exclude_list:
        if word in title_norm:
            return False
            
    if not keywords:
        return True

    # Very lenient matching: at least one non-generic keyword must match
    generic = ['ex', 'メガ', 'mega', 'ポケモン', 'カード', 'pokemon', 'card']
    essential = [k for k in keywords if k.lower() not in generic]
    if not essential: essential = keywords
    
    for k in essential:
        k_norm = unicodedata.normalize('NFKD', str(k)).lower()
        if k_norm in title_norm:
            return True
            
    return False

async def search_price(page, site, keywords_list):
    search_query = ' '.join(keywords_list)
    print(f"  🔍 {site} で '{search_query}' を検索中...")
    try:
        if site == 'mercari':
            # Use status=on_sale for "In Stock", and item_types=1 for "Regular Listings" (exclude auctions)
            url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote(search_query)}&status=on_sale&item_types=1'
            await page.goto(url, wait_until='networkidle', timeout=25000)
            
            # Scroll down to trigger lazy loading
            await page.evaluate('window.scrollBy(0, 1000)')
            await page.wait_for_timeout(3000)
            
            items = await page.locator('a[href^="/item/m"], a[data-testid="item-card"]').all()
            print(f"      [DEBUG] Mercari 検出: {len(items)}件")
            results = []
            for it in items:
                if len(results) >= 3: break
                try:
                    # One-shot extraction to avoid element detachment
                    data = await it.evaluate('''el => {
                        const img = el.querySelector('img');
                        const priceArea = el.innerText;
                        return {
                            title: el.ariaLabel || (img ? img.alt : "") || el.innerText,
                            inner: el.innerText,
                            href: el.href,
                            img: img ? (img.getAttribute("src") || img.getAttribute("data-src") || img.src) : null,
                            isAuction: priceArea.includes("現在")
                        };
                    }''')
                    
                    if data['isAuction']:
                        # print("        [DEBUG] Mercari オークション除外")
                        continue
                    
                    title = data['title']
                    price_val = data['inner']
                    img_src = data['img']
                    url_item = data['href']

                    if title:
                        title = re.sub(r'¥\s*[\d,]+', '', title).strip()

                    if not is_relevant(title, keywords_list):
                        continue
                    
                    print(f"        ✓ Mercari 採用: {title[:30]}...")
                        
                    # Robust price extraction for Mercari
                    price_val = data['inner']
                    price = 0
                    m = re.search(r'(?:¥|円)\s*([\d,]+)', price_val)
                    if m:
                        price = int(m.group(1).replace(',',''))
                    else:
                        all_nums = re.findall(r'([\d,]+)', price_val)
                        for num_str in reversed(all_nums):
                            p = int(num_str.replace(',', ''))
                            if p >= 100:
                                price = p
                                break
                    
                    if price > 0:
                        results.append({'price': price,'image':img_src,'url':url_item, 'title': title})
                        print(f"        ✓ Mercari 確定: {price}円")
                    else:
                        print(f"        ⚠️ Mercari 価格抽出失敗: '{price_val.replace('\\n',' ')}'")
                except Exception as e:
                    # print(f"        ⚠️ Mercari個別エラー: {e}")
                    pass
            print(f"    → {len(results)}件取得")
            return results if results else None
        elif site == 'hardoff':
            # Use exso=1 for "In Stock", and prefix with 'ポケモンカード'
            full_search = f"ポケモンカード {search_query}"
            url = f'https://netmall.hardoff.co.jp/search/?exso=1&q={urllib.parse.quote(full_search)}&s=7&p=1'
            await page.goto(url, wait_until='networkidle', timeout=20000)
            await page.wait_for_timeout(3000)
            
            items = await page.locator('a[href*="/product/"]').all()
            print(f"      [DEBUG] HardOff 検出: {len(items)}件")
            
            # If no items, try broader search (without 'ポケモンカード' prefix first)
            if not items and len(keywords_list) > 1:
                broader_query = f"ポケモンカード {keywords_list[0]}"
                print(f"      [DEBUG] HardOff ヒットなし。広域検索 '{broader_query}' を試行...")
                url = f'https://netmall.hardoff.co.jp/search/?exso=1&q={urllib.parse.quote(broader_query)}&s=7&p=1'
                await page.goto(url, wait_until='networkidle', timeout=20000)
                await page.wait_for_timeout(3000)
                items = await page.locator('a[href*="/product/"]').all()

            results = []
            for it in items:
                if len(results) >= 3: break
                try:
                    # One-shot extraction for Hard Off
                    data = await it.evaluate('''el => {
                        const img = el.querySelector('img');
                        // Split innerText by newline. The 3rd part is usually the title.
                        const parts = el.innerText.split('\\n').map(s => s.trim()).filter(s => s.length > 0);
                        let titleText = "";
                        if (parts.length >= 3) {
                            titleText = parts[2]; // Product Name
                        } else if (parts.length > 0) {
                            titleText = parts[0];
                        }
                        
                        return {
                            title: titleText || (img ? img.alt : "") || el.innerText,
                            inner: el.innerText,
                            href: el.href,
                            img: img ? img.src : null
                        };
                    }''')
                    
                    title = data['title']
                    price_val = data['inner']
                    img_src = data['img']
                    href = data['href']
                    
                    print(f"        [DEBUG] HardOff 候補: '{title}'")

                    if not is_relevant(title, keywords_list):
                        print(f"        [DEBUG] HardOff スキップ (is_relevant): '{title}'")
                        continue
                    
                    # Check for mandatory rarity keywords
                    rarities = ['sar', 'sr', 'sa', 'ur', 'hr', 'csr', 'chr', 'rrr', 'rr', 'r', 'ar']
                    has_mandatory = any(k.lower() in title.lower() for k in keywords_list if k.lower() in rarities)
                    
                    # Only enforce "card" requirement if no mandatory rarity keyword exists
                    if not has_mandatory and "カード" not in title and "card" not in title.lower():
                         continue
                    
                    print(f"        ✓ HardOff 採用: {title[:30]}...")
                        
                    # Robust price extraction for Hard Off
                    price_val = data['inner']
                    # Prioritize number with ¥ or 円
                    m = re.search(r'(?:¥|円)\s*([\d,]+)', price_val)
                    if not m:
                        # Find all numbers and pick the one that's likely a price
                        all_nums = re.findall(r'([\d,]+)', price_val)
                        price = 0
                        for num_str in reversed(all_nums):
                            p = int(num_str.replace(',', ''))
                            if p >= 100 and p != 2024: # Avoid years or small numbers
                                price = p
                                break
                        if price == 0 and all_nums:
                            price = int(all_nums[-1].replace(',', ''))
                    else:
                        price = int(m.group(1).replace(',',''))

                    if price > 0:
                        if href and not href.startswith('http'):
                            href = 'https://netmall.hardoff.co.jp' + href
                        results.append({'price': price,'image':img_src,'url':href, 'title': title.strip() if title else "ハードオフ商品"})
                        print(f"        ✓ HardOff 確定: {price}円")
                    else:
                        print(f"        ⚠️ HardOff 価格抽出失敗: '{price_val.replace('\\n',' ')}'")
                except Exception as e:
                    # print(f"        ⚠️ HardOff個別エラー: {e}")
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
                
                # Check for "No results" message
                no_results = await page.locator('text="お探しの条件に一致する商品は見つかりませんでした"').is_visible()
                if no_results:
                    print("      [DEBUG] 検索結果0件（おすすめのみ表示されているためスキップ）")
                    return None
                
                # Check for result count to avoid recommended items
                try:
                    count_text = await page.evaluate('''() => {
                        const el = Array.from(document.querySelectorAll('p, span, div')).find(e => e.innerText && e.innerText.includes('件/') && /\\d+\\s*件/.test(e.innerText));
                        return el ? el.innerText : "";
                    }''')
                    match = re.search(r'/\s*([\d,]+)\s*件', count_text)
                    total_count = int(match.group(1).replace(',', '')) if match else 999
                except:
                    total_count = 999
                
                # Updated selector: a[href^="/item/"] is more specific to product items
                exhibits = await page.locator('a[href^="/item/"]').all()
                print(f"      [DEBUG] 検出: {len(exhibits)}件 (検索ヒット: {total_count}件)")
                results = []
                for idx, exhibit in enumerate(exhibits):
                    if idx >= total_count: 
                        # print("      [DEBUG] おすすめセクションに到達したため終了")
                        break
                    if len(results) >= 3: break
                    try:
                        href = await exhibit.get_attribute('href')
                        if not href:
                            continue
                        if not href.startswith('http'):
                            href = 'https://paypayfleamarket.yahoo.co.jp' + href
                        
                        # Debug: print outerHTML to see structure if needed
                        # print(f"        [DEBUG] item html: {await exhibit.evaluate('el => el.outerHTML[:100]')}")
                            
                        # Improved price extraction: Try data-cl-params first (contains raw price)
                        cl_params = await exhibit.get_attribute('data-cl-params')
                        if cl_params:
                            price_match = re.search(r'price:(\d+)', cl_params)
                            if price_match:
                                price = int(price_match.group(1))
                            else:
                                price_match = None
                        
                        if not price_match:
                            # Fallback: Target the price element specifically
                            price_val = await exhibit.evaluate('''el => {
                                const p = el.querySelector('p:not(:first-child)');
                                if (p) return p.innerText;
                                const allP = Array.from(el.querySelectorAll('p'));
                                const priceP = allP.find(p => p.innerText.includes('円'));
                                return priceP ? priceP.innerText : el.innerText;
                            }''')
                            
                            price_match = re.search(r'([\d,]+)\s*円', price_val)
                            if not price_match:
                                price_match = re.search(r'([\d,]+)', price_val)
                                
                            if price_match:
                                price_str = price_match.group(1).replace(',', '')
                                price = int(price_str)
                            else:
                                # Final fallback: try to find any number in the element
                                price_val = await exhibit.inner_text()
                                price_match = re.search(r'([\d,]+)', price_val)
                                if price_match:
                                    price = int(price_match.group(1).replace(',', ''))
                                else:
                                    continue

                        # Improved image extraction: check src and data-src
                        img_src = await exhibit.evaluate('''el => {
                            const img = el.querySelector("img");
                            if (!img) return null;
                            return img.getAttribute("src") || img.getAttribute("data-src") || img.src;
                        }''')
                        
                        # Extract title: img alt is usually the most complete title
                        title = await exhibit.evaluate('''el => {
                            const img = el.querySelector('img');
                            if (img && img.alt) return img.alt;
                            // Fallback to p tags
                            const pTags = Array.from(el.querySelectorAll('p'));
                            if (pTags.length > 0) return pTags[0].innerText;
                            return "";
                        }''')
                        
                        if not is_relevant(title, keywords_list):
                            # if idx < 5: print(f"        [DEBUG] スキップ: {title[:30]}...")
                            continue

                        results.append({'price': price,'image':img_src,'url':href, 'title': title})
                        print(f"        ✓ 価格: {price}円 ({title[:25]}...)")
                    except Exception as e:
                        print(f"        ⚠️ 個別商品取得エラー: {e}")
                        continue
                print(f"    → {len(results)}件取得")
                return results if results else None
            except Exception as e:
                print(f"    ⚠️ ヤフーフリマエラー: {str(e)[:100]}")
                return None
    except Exception as e:
        print(f"    ❌ エラー: {str(e)[:80]}")
    return None

async def get_ebay_image(token, title):
    if not token:
        return 'https://via.placeholder.com/300?text=No+Token'
    try:
        url = f"https://api.ebay.com/buy/browse/v1/item_summary/search?q={urllib.parse.quote(title)}&limit=1"
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if 'itemSummaries' in data and len(data['itemSummaries']) > 0:
                item = data['itemSummaries'][0]
                if 'image' in item:
                    return item['image']['imageUrl']
        print(f"      [DEBUG] eBay API 画像取得失敗 ({r.status_code}): {r.text[:100]}")
    except Exception as e:
        print(f"      [DEBUG] eBay API エラー: {e}")
    return 'https://via.placeholder.com/300?text=No+Image'

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

    header_html = f"""
    <header>
        <h1>💎 eBay Research Calculator</h1>
        <p>為替レート: 1 USD = ¥{usd_to_jpy:.2f}</p>
    </header>
    """
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>eBay 売れ筋 × 日本仕入先 リサーチレポート</title>
    <style>
        :root {{
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #22c55e;
            --danger: #ef4444;
            --bg: #f8fafc;
            --card-bg: rgba(255, 255, 255, 0.8);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Outfit', sans-serif;
            background: var(--bg);
            color: #1e293b;
            line-height: 1.6;
            padding-bottom: 50px;
        }}

        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

        header {{
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            color: white;
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
            text-align: center;
        }}
"""

    html_content += """
        .product-card {
            background: var(--card-bg);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        }

        .top-section {
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 20px;
        }

        .ebay-main-img {
            width: 200px;
            height: 200px;
            object-fit: contain;
            border-radius: 10px;
            background: white;
            padding: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .ebay-details { flex: 1; }
        .ebay-details h2 { font-size: 22px; margin-bottom: 10px; color: #0f172a; }

        .price-badge {
            display: inline-block;
            padding: 5px 15px;
            background: #dbeafe;
            color: #1e40af;
            border-radius: 20px;
            font-weight: bold;
            font-size: 18px;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .item-card {
            border: 2px solid transparent;
            border-radius: 15px;
            padding: 15px;
            background: white;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
        }

        .item-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        }

        .item-card.selected {
            border-color: var(--primary);
            background: #f5f3ff;
        }

        .item-card img {
            width: 100%;
            height: 120px;
            object-fit: contain;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .item-card .title {
            font-size: 12px;
            height: 36px;
            overflow: hidden;
            margin-bottom: 8px;
        }

        .item-card .price {
            font-size: 16px;
            font-weight: bold;
            color: var(--primary);
        }

        .calc-panel {
            background: #f1f5f9;
            border-radius: 15px;
            padding: 20px;
            display: flex;
            justify-content: space-around;
            align-items: center;
            border: 2px solid #e2e8f0;
        }

        .calc-box { text-align: center; flex: 1; }
        .calc-operator { font-size: 24px; font-weight: bold; color: #94a3b8; margin: 0 10px; }
        .calc-label { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px; }
        .calc-val { font-size: 18px; font-weight: 800; }

        .profit-val { color: var(--success); font-size: 22px; }
        .profit-val.negative { color: var(--danger); }

        .select-hint {
            font-size: 14px;
            color: #64748b;
            font-style: italic;
        }
    </style>
</head>
<body>
<div class="container">
""" + header_html

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        for idx, row in df.iterrows():
            if idx >= 10: break
            try:
                ebay_title = str(row.get('ebay_title', 'Unknown Title')).strip()
                ebay_price_usd = parse_currency(row.get('avg_price_usd', 0))
                kw_list = extract_keywords(ebay_title)
                kw_display = '　'.join(kw_list)
    
                print(f"\n📦 [{idx+1}] {ebay_title[:60]}")
    
                mercari_results = await search_price(page, 'mercari', kw_list)
                hardoff_results = await search_price(page, 'hardoff', kw_list)
                yahoo_results = await search_price(page, 'yahoofleamarket', kw_list)
    
                ebay_price_jpy = ebay_price_usd * usd_to_jpy
                ebay_fees = calculate_ebay_fees(ebay_price_usd, usd_to_jpy)
                shipping = calculate_shipping_cost()
                
                # Try to get image from eBay directly via API
                ebay_img = await get_ebay_image(token, ebay_title)
                print(f"      [DEBUG] eBay Image: {ebay_img}")

                def format_items(results, site_name):
                    html = ""
                    if results:
                        for r in results:
                            html += f"""
                            <div class="item-card" onclick="selectItem(this, {r['price']}, {ebay_price_jpy}, {ebay_fees}, {shipping})">
                                <img src="{r['image']}" onerror="this.src='https://via.placeholder.com/150';" />
                                <div class="title">{r.get('title', 'ポケモンカード')[:40]}...</div>
                                <div class="price">¥{r['price']:,}</div>
                                <p style="font-size:10px; color:#999;">{site_name}</p>
                                <a href="{r['url']}" target="_blank" onclick="event.stopPropagation();">詳細</a>
                            </div>"""
                    return html

                mercari_html = format_items(mercari_results, "Mercari")
                hardoff_html = format_items(hardoff_results, "HardOff")
                yahoo_html = format_items(yahoo_results, "Yahoo")

                # Find initial min price to pre-fill (filter out suspiciously low prices like cases/frames)
                all_results = (mercari_results or []) + (hardoff_results or []) + (yahoo_results or [])
                # Sort by price and pick the first one that passes a basic relevance check
                # (actually they already passed is_relevant, but let's be safe)
                valid_results = [r for r in all_results if r['price'] > 1000] # Usually cards are > 1000 for these specific items
                if not valid_results: valid_results = all_results
                
                initial_min = min([r['price'] for r in valid_results]) if valid_results else 0
                
                initial_profit = ebay_price_jpy - initial_min - ebay_fees - shipping if initial_min > 0 else 0
                initial_roi = (initial_profit / (initial_min + ebay_fees + shipping)) * 100 if initial_min > 0 else 0
                profit_class = "negative" if initial_profit < 0 else ""

                html_content += f"""
                <div class="product-card" id="prod-{idx}">
                    <div class="top-section">
                        <img class="ebay-main-img" src="{ebay_img}" />
                        <div class="ebay-details">
                            <h2>{ebay_title}</h2>
                            <div class="price-badge">eBay: ${ebay_price_usd:.2f} (¥{ebay_price_jpy:,.0f})</div>
                            <p style="margin-top:10px; color:#64748b;">キーワード: {kw_display}</p>
                        </div>
                    </div>

                    <p class="select-hint">💡 下の商品をクリックして利益計算をシミュレーション</p>
                    <div class="grid">
                        {mercari_html}{hardoff_html}{yahoo_html}
                    </div>

                    <div class="calc-panel" id="calc-{idx}">
                        <div class="calc-box">
                            <div class="calc-label">eBay 売価</div>
                            <div class="calc-val">¥{ebay_price_jpy:,.0f}</div>
                        </div>
                        <div class="calc-operator">−</div>
                        <div class="calc-box">
                            <div class="calc-label">仕入価格</div>
                            <div class="calc-val purchase-price">{f"¥{initial_min:,.0f}" if initial_min > 0 else "-"}</div>
                        </div>
                        <div class="calc-operator">−</div>
                        <div class="calc-box">
                            <div class="calc-label">手数料+送料</div>
                            <div class="calc-val">¥{ebay_fees + shipping:,.0f}</div>
                        </div>
                        <div class="calc-operator">＝</div>
                        <div class="calc-box">
                            <div class="calc-label">予想利益 (ROI)</div>
                            <div class="calc-val profit-val {profit_class}">
                                {f'¥{initial_profit:,.0f} ({initial_roi:.1f}%)' if initial_min > 0 else "-"}
                            </div>
                        </div>
                    </div>
                </div>"""
            except Exception as e:
                print(f"❌ 商品 [{idx+1}] 処理中にエラー: {e}")
                continue
        await browser.close()

    html_content += """
    </main>

    <script>
    function selectItem(el, buyPrice, ebayPrice, fees, shipping) {
        const parent = el.closest('.product-card');
        
        // UI update: remove selected from all cards in THIS product-card
        parent.querySelectorAll('.item-card').forEach(card => card.classList.remove('selected'));
        el.classList.add('selected');

        // Calculation
        const profit = ebayPrice - buyPrice - fees - shipping;
        const totalCost = buyPrice + fees + shipping;
        const profitRate = totalCost > 0 ? (profit / totalCost) * 100 : 0;
        
        const panel = parent.querySelector('.calc-panel');
        panel.querySelector('.purchase-price').innerText = '¥' + Math.round(buyPrice).toLocaleString();
        
        const profitEl = panel.querySelector('.profit-val');
        profitEl.innerText = '¥' + Math.round(profit).toLocaleString() + ' (' + profitRate.toFixed(1) + '%)';
        
        if (profit >= 0) {
            profitEl.style.color = '#22c55e';
        } else {
            profitEl.style.color = '#ef4444';
        }
    }
    </script>

    <footer>
        <p>このレポートは参考用です。実際の仕入れ・販売判断は慎重に行ってください。</p>
    </footer>
</div>
</body>
</html>"""

    os.makedirs('data/reports', exist_ok=True)
    filename = f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    report_path = os.path.abspath(os.path.join('data/reports', filename))

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"\n✅ レポート保存: {report_path}")

    if os.path.exists(report_path):
        time.sleep(1)
        webbrowser.open(f"file:///{report_path.replace(os.sep, '/')}")
    else:
        print(f"❌ レポートファイルの作成に失敗しました: {report_path}")

asyncio.run(main())
