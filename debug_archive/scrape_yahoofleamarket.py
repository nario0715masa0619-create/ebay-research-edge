import asyncio, re, csv, os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_yahoofleamarket(keyword='ポケモンカード'):
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        # 最初のページでページ数を取得
        url = f"https://paypayfleamarket.yahoo.co.jp/search/{keyword}?page=1"
        print(f"\nURL: {url}")
        print("ページ読み込み中...")
        
        try:
            await page.goto(url, wait_until='load')
            await page.wait_for_timeout(5000)
            
            # ページネーション検出
            try:
                pagination_links = await page.locator('a[href*="page="]').all()
                page_numbers = []
                for link in pagination_links:
                    href = await link.get_attribute('href')
                    if href:
                        match = re.search(r'page=(\d+)', href)
                        if match:
                            page_numbers.append(int(match.group(1)))
                
                max_page = max(set(page_numbers)) if page_numbers else 1
                print(f"✓ 総ページ数: {max_page} ページ\n")
            except:
                print("⚠️ ページ数判定失敗。1ページのみ処理します")
                max_page = 1
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            await browser.close()
            return results
        
        # 各ページをスクレイピング
        for page_num in range(1, max_page + 1):
            url = f"https://paypayfleamarket.yahoo.co.jp/search/{keyword}?page={page_num}"
            print(f"ページ {page_num}/{max_page}: ", end='', flush=True)
            
            try:
                await page.goto(url, wait_until='load')
                await page.wait_for_timeout(3000)
                
                # スクロール
                for _ in range(10):
                    await page.evaluate('window.scrollBy(0, window.innerHeight)')
                    await page.wait_for_timeout(300)
                
                # 商品カードを取得
                items = await page.locator('div[class*="item"], li[class*="item"]').all()
                
                if len(items) == 0:
                    print("✓ 完了（商品なし）")
                    break
                
                page_count = 0
                for item in items:
                    try:
                        # 商品名
                        title = await item.locator('a, h2, h3').first.text_content()
                        title = title.strip() if title else ""
                        
                        # 価格
                        price_text = await item.locator('text=/¥\\d+/').first.text_content()
                        if price_text:
                            price = re.sub(r'[^\d]', '', price_text)
                        else:
                            price = ""
                        
                        # URL
                        link = await item.locator('a').first.get_attribute('href')
                        if link and not link.startswith('http'):
                            link = 'https://paypayfleamarket.yahoo.co.jp' + link
                        
                        if title and price:
                            results.append({
                                'title': title,
                                'price': price,
                                'url': link,
                                'scraped_at': datetime.now().isoformat()
                            })
                            page_count += 1
                    except:
                        continue
                
                print(f"✓ {page_count} 件取得（累計 {len(results)} 件）")
                
            except asyncio.TimeoutError:
                print(f"❌ タイムアウト")
                break
            except Exception as e:
                print(f"❌ エラー: {str(e)[:30]}")
                continue
        
        await browser.close()
    
    return results

def save_csv(items):
    os.makedirs('data/imports', exist_ok=True)
    filename = 'data/imports/yahoofleamarket_scrape.csv'
    if not items:
        print("\n❌ データなし")
        return
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['title','price','url','scraped_at'])
        w.writeheader()
        w.writerows(items)
    print(f"✅ {len(items)} 件を {filename} に保存")

async def main():
    print("\n" + "="*60)
    print("ヤフーフリマ スクレイピング開始")
    print("="*60)
    
    items = await scrape_yahoofleamarket(keyword='ポケモンカード')
    
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
