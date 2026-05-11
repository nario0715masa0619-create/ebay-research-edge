import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def check_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        encoded_query = urllib.parse.quote("マナフィ 004/PPP", safe='')
        url = f'https://paypayfleamarket.yahoo.co.jp/search/{encoded_query}?open=1'
        print(f"アクセス中: {url}")
        await page.goto(url, wait_until='domcontentloaded', timeout=20000)
        await page.wait_for_timeout(5000)
        
        # ページタイトルを確認
        title = await page.title()
        print(f"ページタイトル: {title}")
        
        # ページの総文字数
        html = await page.content()
        print(f"HTML長: {len(html)}")
        
        # 「マナフィ」が含まれているか
        if 'マナフィ' in html:
            print("✅ ページに『マナフィ』が含まれています")
        else:
            print("❌ ページに『マナフィ』が見つかりません")
        
        # 「¥」が含まれているか
        if '¥' in html:
            print("✅ ページに『¥』が含まれています")
        else:
            print("❌ ページに『¥』が見つかりません")
        
        # HTML全体をファイル保存
        with open('yahoo_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ yahoo_full.html に保存しました")
        
        await browser.close()

asyncio.run(check_page())
