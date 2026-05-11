import asyncio, csv, os, re, requests, unicodedata
from datetime import datetime
from playwright.async_api import async_playwright

def get_exchange_rate():
    """現在のドル円レートを取得"""
    try:
        resp = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            rate = data['rates'].get('JPY')
            if rate:
                print(f"✓ ドル円レート: 1 USD = {rate:.2f} JPY")
                return rate
    except:
        pass
    
    print("⚠️ レート取得失敗。デフォルト値 157.12 JPY を使用")
    return 157.12

def normalize_text(text):
    """Unicode を正規化（é → e など）"""
    return unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('ascii')

def extract_keywords(title):
    """eBay タイトルから検索キーワードを抽出"""
    
    keywords = []
    normalized_title = normalize_text(title).lower()
    
    if 'pokemon' in normalized_title and 'card' in normalized_title:
        keywords.append('ポケモンカード')
    elif 'pokemon' in normalized_title:
        keywords.append('ポケモンカード')
    
    important_keywords = {
        'base set': 'ベースセット',
        'jungle': 'ジャングル',
        'fossil': 'フォッシル',
        'charizard': 'リザードン',
        'pikachu': 'ピカチュウ',
        'blastoise': 'フリーザー',
        'venusaur': 'フシギバナ',
        '1st edition': '初版',
        'psa': 'PSA',
        'cgc': 'CGC',
        'holo': 'ホロ',
        'reverse holo': 'リバースホロ',
        'full art': 'フルアート',
        'tcg': 'TCG',
        'ultra rare': 'ウルトラレア',
        'ex': 'EX',
        'vmax': 'VMAX',
        'vstar': 'VSTAR',
        'xy': 'XY',
        'scarlet': 'スカーレット',
        'violet': 'バイオレット',
        'sword': 'ソード',
        'shield': 'シールド',
    }
    
    for en, ja in important_keywords.items():
        if en in normalized_title:
            keywords.append(ja)
    
    if 'lot' in normalized_title or 'bulk' in normalized_title or 'pack' in normalized_title:
        keywords.append('まとめ売り')
    
    year_match = re.search(r'(19|20)\d{2}', title)
    if year_match:
        keywords.append(year_match.group(0))
    
    return ' '.join(keywords)

def calculate_ebay_fees(selling_price_usd, is_bulk_discount=False):
    """eBay 手数料計算（ポケモンカード 11.35%）"""
    
    ebay_fee_rate = 0.0235 if is_bulk_discount else 0.1135
    ebay_fee = selling_price_usd * ebay_fee_rate
    overseas_fee = selling_price_usd * 0.004
    payoneer_fee = selling_price_usd * 0.02
    tariff = selling_price_usd * 0.153
    
    total_fees = ebay_fee + overseas_fee + payoneer_fee + tariff
    
    return {
        'ebay_fee': ebay_fee,
        'overseas_fee': overseas_fee,
        'payoneer_fee': payoneer_fee,
        'tariff': tariff,
        'total_fees': total_fees,
        'total_fee_rate': (total_fees / selling_price_usd * 100) if selling_price_usd > 0 else 0
    }

async def search_price(page, site, keyword):
    """サイトで商品を検索"""
    try:
        if site == 'mercari':
            url = f'https://jp.mercari.com/search?keyword={keyword}'
            await page.goto(url, wait_until='load', timeout=15000)
            await page.wait_for_timeout(2000)
            
            prices = await page.locator('span:has-text("¥")').all()
            if prices:
                price_text = await prices[0].text_content()
                match = re.search(r'¥([\d,]+)', price_text)
                if match:
                    return int(match.group(1).replace(',', ''))
        
        elif site == 'hardoff':
            url = f'https://netmall.hardoff.co.jp/search/?q={keyword}&s=7&p=1'
            await page.goto(url, wait_until='load', timeout=15000)
            await page.wait_for_timeout(2000)
            
            prices = await page.locator('span.font-en.item-price-en').all()
            if prices:
                price_text = await prices[0].text_content()
                match = re.search(r'[\d,]+', price_text)
                if match:
                    return int(match.group(0).replace(',', ''))
        
        elif site == 'yahoofleamarket':
            # 販売中のみフィルタ付き URL
            url = f'https://paypayfleamarket.yahoo.co.jp/search/{keyword}?open=1'
            await page.goto(url, wait_until='load', timeout=15000)
            await page.wait_for_timeout(3000)
            
            prices = await page.locator('span:has-text("¥")').all()
            if prices:
                price_text = await prices[0].text_content()
                match = re.search(r'¥([\d,]+)', price_text)
                if match:
                    return int(match.group(1).replace(',', ''))
    
    except Exception as e:
        print(f"  ⚠️ {site} 検索エラー: {str(e)[:50]}")
    
    return None

async def analyze_ebay_products():
    results = []
    profitable_count = 0
    
    print("\n" + "="*60)
    print("💱 ドル円レート取得中...")
    print("="*60)
    usd_to_jpy = get_exchange_rate()
    
    try:
        with open('data/imports/ebay_pokemon_cards_japan_ships.csv', 'r', encoding='utf-8-sig') as f:
            ebay_items = list(csv.DictReader(f))
    except:
        print("❌ eBay データが見つかりません")
        return
    
    print(f"\n{'='*60}")
    print(f"📊 利益分析開始（全 {len(ebay_items)} 件）")
    print(f"{'='*60}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        
        for idx, item in enumerate(ebay_items, 1):
            title = item.get('title', '')
            ebay_price_usd = float(item.get('price', 0))
            seller = item.get('seller', '')
            
            print(f"\n[{idx}/{len(ebay_items)}] {title[:60]}")
            print(f"  eBay 売価: ${ebay_price_usd:.2f}")
            
            # キーワード抽出
            keywords = extract_keywords(title)
            print(f"  🔍 検索キーワード: {keywords}")
            
            is_bulk = ebay_price_usd >= 2500
            fees = calculate_ebay_fees(ebay_price_usd, is_bulk_discount=is_bulk)
            
            print(f"  💰 手数料: ${fees['total_fees']:.2f} ({fees['total_fee_rate']:.2f}%)")
            
            # メルカリ検索
            print(f"  🔎 メルカリ検索中...", end='', flush=True)
            mercari_price = await search_price(page, 'mercari', keywords)
            print(f" → ¥{mercari_price:,}" if mercari_price else " → 見つかりません")
            
            # ハードオフ検索
            print(f"  🔎 ハードオフ検索中...", end='', flush=True)
            hardoff_price = await search_price(page, 'hardoff', keywords)
            print(f" → ¥{hardoff_price:,}" if hardoff_price else " → 見つかりません")
            
            # ヤフーフリマ検索（販売中のみ）
            print(f"  🔎 ヤフーフリマ検索中...", end='', flush=True)
            yahoofleamarket_price = await search_price(page, 'yahoofleamarket', keywords)
            print(f" → ¥{yahoofleamarket_price:,}" if yahoofleamarket_price else " → 見つかりません")
            
            sourcing_prices = [p for p in [mercari_price, hardoff_price, yahoofleamarket_price] if p]
            min_price_jpy = min(sourcing_prices) if sourcing_prices else None
            
            if min_price_jpy:
                ebay_price_jpy = ebay_price_usd * usd_to_jpy
                total_fees_jpy = fees['total_fees'] * usd_to_jpy
                profit_jpy = min_price_jpy - ebay_price_jpy - total_fees_jpy
                profit_rate = (profit_jpy / min_price_jpy * 100) if min_price_jpy > 0 else 0
                
                if profit_jpy > 0:
                    status = "✅ 利益あり"
                    profitable_count += 1
                else:
                    status = "❌ 赤字"
                
                print(f"  → 仕入最安: ¥{min_price_jpy:,}")
                print(f"  → 利益: ¥{profit_jpy:,.0f} ({profit_rate:.1f}%) {status}")
                
                results.append({
                    'ebay_title': title,
                    'search_keywords': keywords,
                    'ebay_price_usd': f"{ebay_price_usd:.2f}",
                    'ebay_price_jpy': f"{ebay_price_jpy:.0f}",
                    'total_fees_jpy': f"{total_fees_jpy:.0f}",
                    'mercari_price': mercari_price or '',
                    'hardoff_price': hardoff_price or '',
                    'yahoofleamarket_price': yahoofleamarket_price or '',
                    'min_sourcing_price': min_price_jpy,
                    'profit_jpy': f"{profit_jpy:.0f}",
                    'profit_rate': f"{profit_rate:.1f}%",
                    'seller': seller
                })
            
            if idx >= 10:
                break
        
        await browser.close()
    
    if results:
        os.makedirs('data/analysis', exist_ok=True)
        filename = 'data/analysis/profit_analysis.csv'
        with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
            fieldnames = [
                'ebay_title', 'search_keywords', 'ebay_price_usd', 'ebay_price_jpy',
                'total_fees_jpy', 'mercari_price', 'hardoff_price', 'yahoofleamarket_price',
                'min_sourcing_price', 'profit_jpy', 'profit_rate', 'seller'
            ]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(results)
        
        print(f"\n{'='*60}")
        print(f"✅ {len(results)} 件を {filename} に保存しました")
        print(f"💡 利益ありの商品: {profitable_count}/{len(results)} 件")
        print(f"{'='*60}")

asyncio.run(analyze_ebay_products())
