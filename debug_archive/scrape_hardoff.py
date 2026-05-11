import asyncio, re, csv, os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_hardoff(keyword='ポケモンカード'):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        # 最初のページでページ数を取得
        url = f"https://netmall.hardoff.co.jp/search/?q={keyword}&s=7&p=1&pl=30"
        await page.goto(url, wait_until='load')
        await page.wait_for_timeout(3000)
        
        # ページネーションの最後のページ番号を取得
        try:
            # ページネーション内のすべてのページ番号リンクを取得
            pagination_links = await page.locator('div.pagination a, div.pagenation a, nav a[href*="&p="]').all()
            
            page_numbers = []
            for link in pagination_links:
                href = await link.get_attribute('href')
                if href:
                    match = re.search(r'[&?]p=(\d+)', href)
                    if match:
                        page_numbers.append(int(match.group(1)))
            
            # テキストからもページ番号を抽出
            for link in pagination_links:
                text = await link.text_content()
                if text and text.strip().isdigit():
                    page_numbers.append(int(text.strip()))
            
            max_page = max(set(page_numbers)) if page_numbers else 1
            print(f"\n✓ 総ページ数: {max_page} ページ\n")
        except Exception as e:
            print(f"\n⚠️ ページ数取得失敗: {e}")
            print("ページ数を手動で入力してください（例: 38）: ", end='')
            try:
                max_page = int(input())
            except:
                max_page = 38
        
        # 各ページをスクレイピング
        for page_num in range(1, max_page + 1):
            url = f"https://netmall.hardoff.co.jp/search/?q={keyword}&s=7&p={page_num}&pl=30"
            print(f"ページ {page_num}/{max_page}: ", end='', flush=True)
            
            try:
                await page.goto(url, wait_until='load')
                await page.wait_for_timeout(3000)
                
                # スクロール
                for _ in range(10):
                    await page.evaluate('window.scrollBy(0, window.innerHeight)')
                    await page.wait_for_timeout(300)
                
                # 商品カードを取得
                items = await page.locator('div.itemcolmn_item').all()
                
                if len(items) == 0:
                    print("✓ 完了（商品なし）")
                    break
                
                page_count = 0
                for item in items:
                    try:
                        brand = await item.locator('div.item-brand-name').text_content()
                        brand = brand.strip() if brand else ""
                        
                        name = await item.locator('div.item-name').text_content()
                        name = name.strip() if name else ""
                        
                        code = await item.locator('div.item-code').text_content()
                        code = code.strip() if code else ""
                        
                        price_text = await item.locator('span.font-en.item-price-en').text_content()
                        if price_text:
                            price = re.sub(r'[^\d]', '', price_text)
                        else:
                            price = ""
                        
                        link = await item.locator('a').first.get_attribute('href')
                        if link and not link.startswith('http'):
                            link = 'https://netmall.hardoff.co.jp' + link
                        
                        title = f"{brand} {name} {code}".strip()
                        
                        if title and price:
                            results.append({
                                'title': title,
                                'brand': brand,
                                'price': price,
                                'url': link,
                                'scraped_at': datetime.now().isoformat()
                            })
                            page_count += 1
                    except:
                        continue
                
                print(f"✓ {page_count} 件取得（累計 {len(results)} 件）")
                
            except Exception as e:
                print(f"❌ エラー: {e}")
                break
        
        await browser.close()
    
    return results

def save_csv(items):
    os.makedirs('data/imports', exist_ok=True)
    filename = 'data/imports/hardoff_scrape.csv'
    if not items:
        print("\n❌ データなし")
        return
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['title','brand','price','url','scraped_at'])
        w.writeheader()
        w.writerows(items)
    print(f"\n✅ {len(items)} 件を {filename} に保存")

async def main():
    print("\n" + "="*60)
    print("ハードオフ スクレイピング開始（自動ページ判定）")
    print("="*60)
    
    items = await scrape_hardoff(keyword='ポケモンカード')
    
    print(f"\n{'='*60}")
    print(f"📊 完了")
    print(f"{'='*60}")
    print(f"合計: {len(items)} 件")
    
    if items:
        prices = [int(i['price']) for i in items if i['price'].isdigit()]
        if prices:
            print(f"平均: ¥{sum(prices)//len(prices):,}")
            print(f"最安: ¥{min(prices):,}")
            print(f"最高: ¥{max(prices):,}")
        save_csv(items)
        print("\n✨ 成功！")

asyncio.run(main())
