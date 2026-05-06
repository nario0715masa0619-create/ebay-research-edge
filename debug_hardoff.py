import asyncio
from playwright.async_api import async_playwright

async def debug_hardoff():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        url = "https://netmall.hardoff.co.jp/search/?q=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89&s=7&p=1"
        await page.goto(url, wait_until='load', timeout=60000)
        await page.wait_for_timeout(3000)
        
        # ページ上のすべてのタグを確認
        html = await page.content()
        
        # 商品を含みそうな div/section をリスト
        elements = await page.locator('div, section, article').all()
        print(f"✓ 合計 {len(elements)} 個の div/section/article を検出\n")
        
        # 最初の 10 個の外側タグと class を表示
        for i, elem in enumerate(elements[:20]):
            tag = await elem.evaluate('e => e.tagName')
            cls = await elem.get_attribute('class')
            text = await elem.text_content()
            text = text[:50] if text else ""
            print(f"[{i}] <{tag} class='{cls}'> {text}...")
        
        # HTML の一部を保存
        with open('hardoff_page_source.html', 'w', encoding='utf-8') as f:
            f.write(html[:5000])
        print("\n✅ hardoff_page_source.html に保存しました")
        
        await browser.close()

asyncio.run(debug_hardoff())
