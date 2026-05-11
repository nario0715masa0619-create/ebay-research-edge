import asyncio
from playwright.async_api import async_playwright
import re
import csv
import os
from datetime import datetime

async def scrape_mercari(keyword="ポケモンカード", pages=5):
    """Playwright でメルカリをスクレイピング"""
    results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        for page_num in range(1, pages + 1):
            url = f"https://jp.mercari.com/search?keyword={keyword}&page={page_num}"
            print(f"\nページ {page_num}...")
            
            try:
                await page.goto(url, wait_until="load", timeout=60000)
                await page.wait_for_timeout(5000)
                
                print("  スクロール中...", end="", flush=True)
                for _ in range(15):
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                    await page.wait_for_timeout(300)
                print(" 完了")
                
                await page.wait_for_timeout(3000)
                
                items = await page.locator("[role='img'][aria-label]").all()
                print(f"  {len(items)} 個の要素を検出")
                
                page_count = 0
                page_seen_urls = set()  # ページごとに重複排除
                
                for item in items:
                    try:
                        aria_label = await item.get_attribute('aria-label')
                        
                        if not aria_label or 'サムネイル' in aria_label:
                            continue
                        
                        match = re.search(r'(.+?)の画像\s+(\d+(?:,\d+)?)円', aria_label)
                        if not match:
                            continue
                        
                        title = match.group(1).strip()
                        price = match.group(2)
                        
                        parent = item.locator("xpath=ancestor::a[@href]")
                        item_url = await parent.get_attribute('href')
                        
                        if not item_url:
                            continue
                        if not item_url.startswith('http'):
                            item_url = "https://jp.mercari.com" + item_url
                        
                        # ページ内重複のみ除外（全体重複は除外しない）
                        if item_url in page_seen_urls:
                            continue
                        page_seen_urls.add(item_url)
                        
                        results.append({
                            'title': title,
                            'price': price,
                            'url': item_url,
                            'scraped_at': datetime.now().isoformat()
                        })
                        page_count += 1
                        
                    except:
                        continue
                
                print(f"  {page_count} 件取得（合計 {len(results)} 件）")
                
            except Exception as e:
                print(f"  エラー: {e}")
                continue
        
        await browser.close()
    
    return results

async def main():
    results = await scrape_mercari(pages=5)
    
    os.makedirs('data/imports', exist_ok=True)
    with open('data/imports/mercari_scrape.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'price', 'url', 'scraped_at'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✅ {len(results)} 件を保存しました")
    if results:
        prices = [int(p['price'].replace(',', '')) for p in results]
        print(f"平均: ¥{sum(prices) // len(prices):,}")
        print(f"最安: ¥{min(prices):,}")
        print(f"最高: ¥{max(prices):,}")

asyncio.run(main())
