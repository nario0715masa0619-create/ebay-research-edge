import asyncio
from playwright.async_api import async_playwright

async def debug_yahoofleamarket():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = "https://paypayfleamarket.yahoo.co.jp/search/ポケモンカード?page=1"
        await page.goto(url, wait_until='load')
        await page.wait_for_timeout(5000)
        
        # スクロール
        for _ in range(10):
            await page.evaluate('window.scrollBy(0, window.innerHeight)')
            await page.wait_for_timeout(300)
        
        # HTML全体を保存
        html = await page.content()
        with open('yahoofleamarket_debug.html', 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("✅ yahoofleamarket_debug.html に保存しました")
        print(f"HTMLサイズ: {len(html)} 文字")
        
        # 商品リンクを探す
        import re
        links = re.findall(r'href="([^"]*item[^"]*)"', html)
        print(f"\n🔍 item を含むリンク: {len(links)} 件")
        if links:
            for link in links[:5]:
                print(f"  {link[:80]}")
        
        # 価格を探す
        prices = re.findall(r'¥[\d,]+', html)
        print(f"\n💰 価格: {len(prices)} 件")
        if prices:
            for price in prices[:5]:
                print(f"  {price}")
        
        await browser.close()

asyncio.run(debug_yahoofleamarket())
