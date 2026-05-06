import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # メルカリ検索
        url = f'https://jp.mercari.com/search?keyword={urllib.parse.quote("ゲンガー メガ EX SAR")}'
        await page.goto(url, wait_until='load', timeout=15000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open('mercari_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ メルカリHTML保存: mercari_debug.html")
        
        # ハードオフ検索
        url = f'https://netmall.hardoff.co.jp/search/?q={urllib.parse.quote("ゲンガー メガ EX SAR")}&s=7&p=1'
        await page.goto(url, wait_until='load', timeout=15000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open('hardoff_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ ハードオフHTML保存: hardoff_debug.html")
        
        # ヤフーフリマ検索
        url = f'https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote("マナフィ 004/PPP")}?open=1'
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(5000)
        html = await page.content()
        with open('yahoo_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ ヤフーフリマHTML保存: yahoo_debug.html")
        
        await browser.close()

asyncio.run(inspect())
