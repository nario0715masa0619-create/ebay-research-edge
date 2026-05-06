import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # ヤフーフリマ検索 - マナフィで試す
        keywords = "マナフィ"
        url = f'https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote(keywords)}?open=1'
        print(f"URL: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(5000)
        html = await page.content()
        with open('yahoo_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ ヤフーフリマHTML保存: yahoo_debug.html")
        
        await browser.close()

asyncio.run(inspect())
