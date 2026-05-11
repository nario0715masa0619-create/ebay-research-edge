import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def debug_yahoo():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        encoded_query = urllib.parse.quote("マナフィ 004/PPP", safe='')
        url = f'https://paypayfleamarket.yahoo.co.jp/search/{encoded_query}?open=1'
        print(f"URL: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(5000)
        
        # ページソースを保存
        html = await page.content()
        with open('yahoo_structure.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ HTML保存: yahoo_structure.html")
        
        # 実際に表示されている商品数をカウント
        items = await page.locator('li[data-testid]').all()
        print(f"li[data-testid] の数: {len(items)}")
        
        # 他のセレクタも試す
        items2 = await page.locator('div[data-testid]').all()
        print(f"div[data-testid] の数: {len(items2)}")
        
        items3 = await page.locator('[data-testid*="item"]').all()
        print(f"[data-testid*='item'] の数: {len(items3)}")
        
        await browser.close()

asyncio.run(debug_yahoo())
