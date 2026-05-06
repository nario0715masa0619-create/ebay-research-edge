import asyncio
from playwright.async_api import async_playwright
import json

async def debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        url = 'https://paypayfleamarket.yahoo.co.jp/search/%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3%20004%2FPPP'
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(5000)
        
        # a[data-cl-params*="exhibit"] の詳細を確認
        items = await page.locator('a[data-cl-params*="exhibit"]').all()
        print(f"✅ a[data-cl-params*='exhibit']: {len(items)}件\n")
        
        for i, item in enumerate(items[:3]):
            print(f"--- 商品 {i+1} ---")
            
            # HTML 全体
            html = await item.inner_html()
            print(f"HTML: {html[:500]}\n")
            
            # href 確認
            href = await item.get_attribute('href')
            print(f"href: {href}\n")
            
            # 価格要素を探す
            try:
                price_text = await item.locator('text=/円/').first.text_content()
                print(f"価格テキスト: {price_text}\n")
            except:
                print("❌ 価格が見つかりません\n")
            
            # 画像要素を探す
            try:
                img_src = await item.locator('img').first.get_attribute('src')
                print(f"画像: {img_src}\n")
            except:
                print("❌ 画像が見つかりません\n")
        
        await browser.close()

asyncio.run(debug())
