import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def check_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        encoded_query = urllib.parse.quote("マナフィ 004/PPP", safe='')
        url = f'https://paypayfleamarket.yahoo.co.jp/search/{encoded_query}?open=1'
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(5000)
        
        # ページソース全体を取得
        html = await page.content()
        
        # 「¥」が含まれる部分だけ抽出（商品情報が含まれる）
        lines = html.split('\n')
        for i, line in enumerate(lines):
            if '¥' in line and 'class' in line:
                print(f"行{i}: {line[:200]}")
        
        await browser.close()

asyncio.run(check_html())
