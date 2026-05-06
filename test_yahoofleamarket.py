import asyncio, re, csv, os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_yahoofleamarket_test():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        
        # ページ1のみ
        url = f"https://paypayfleamarket.yahoo.co.jp/search/ポケモンカード?page=1"
        print(f"URL: {url}\n")
        
        await page.goto(url, wait_until='load')
        await page.wait_for_timeout(3000)
        
        # スクロール
        for _ in range(5):
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await page.wait_for_timeout(200)
        
        # 商品リンクを取得
        links = await page.locator('a[href*="/item/z"]').all()
        print(f"✓ {len(links)} 件の商品リンクを検出\n")
        
        for idx, link in enumerate(links[:5], 1):  # 最初の5件だけテスト
            try:
                href = await link.get_attribute('href')
                if not href:
                    continue
                
                if href.startswith('/'):
                    item_url = 'https://paypayfleamarket.yahoo.co.jp' + href
                else:
                    item_url = href
                
                print(f"[{idx}] アクセス中: {item_url}")
                
                # 商品ページにアクセス
                item_page = await browser.new_page()
                try:
                    await asyncio.wait_for(
                        item_page.goto(item_url, wait_until='load'),
                        timeout=10
                    )
                    await item_page.wait_for_timeout(2000)
                    
                    # HTMLを保存（デバッグ用）
                    if idx == 1:
                        html = await item_page.content()
                        with open('yahoofleamarket_item_debug.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                        print("    → HTMLを yahoofleamarket_item_debug.html に保存")
                    
                    # 商品名
                    title = await item_page.locator('h1').first.text_content()
                    title = title.strip() if title else "???"
                    
                    # 価格（複数パターン）
                    price = "???"
                    try:
                        price_text = await asyncio.wait_for(
                            item_page.locator('text=/¥[\\d,]+/').first.text_content(),
                            timeout=2
                        )
                        if price_text:
                            price = price_text.strip()
                    except:
                        pass
                    
                    print(f"    Title: {title[:50]}")
                    print(f"    Price: {price}\n")
                    
                finally:
                    await item_page.close()
                    
            except Exception as e:
                print(f"    ❌ エラー: {str(e)[:50]}\n")
                continue
        
        await browser.close()

asyncio.run(scrape_yahoofleamarket_test())
