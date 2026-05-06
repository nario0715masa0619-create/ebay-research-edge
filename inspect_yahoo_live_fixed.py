import asyncio
import re
from playwright.async_api import async_playwright

async def inspect_live():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = 'https://paypayfleamarket.yahoo.co.jp/search/%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3%20004%2FPPP'
        print(f"📖 Navigating to: {url}")
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # ページタイトル確認
        title = await page.title()
        print(f"✅ Page title: {title}")
        
        # 複数のセレクタで検索
        selectors = [
            'a[href*="/item/"]',
            'a[data-cl-params*="exhibit"]',
            'div[data-testid]',
            'li[data-testid]',
            'article',
            '[role="listitem"]',
            '.product',
            '.item',
            'a.sc-'
        ]
        
        for sel in selectors:
            try:
                count = await page.locator(sel).count()
                print(f"  {sel}: {count}件")
                if count > 0:
                    elem = await page.locator(sel).first.inner_html()
                    print(f"    → 最初の要素: {elem[:200]}")
            except:
                pass
        
        # 「円」記号を含む要素を探す
        print("\n💰 「円」を含む要素:")
        try:
            price_elems = await page.locator('text=/円/').count()
            print(f"  「円」を含む要素: {price_elems}件")
            if price_elems > 0:
                first_price = await page.locator('text=/円/').first.text_content()
                print(f"    → 最初の価格表示: {first_price}")
        except Exception as e:
            print(f"  エラー: {e}")
        
        # 最終的なページソースを保存
        html = await page.content()
        open('yahoo_live.html', 'w', encoding='utf-8').write(html)
        print("\n✅ yahoo_live.html を保存しました")
        
        await browser.close()

asyncio.run(inspect_live())
