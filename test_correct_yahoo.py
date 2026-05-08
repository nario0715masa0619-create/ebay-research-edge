import asyncio
from playwright.async_api import async_playwright
import json

async def test_correct_url():
    # あなたのURL
    url = 'https://auctions.yahoo.co.jp/search/search?p=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89+%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&va=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89+%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&fixed=1&is_postage_mode=1&dest_pref_code=13&b=1&n=50'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        
        title = await page.title()
        print(f'ページタイトル: {title}\n')
        
        # JSONデータを抽出
        script = await page.query_selector('script[type="application/json"]')
        if script:
            json_text = await script.evaluate('el => el.textContent')
            json_data = json.loads(json_text)
            
            items = json_data.get('items', [])
            print(f'定額出品数: {len(items)}件\n')
            
            for idx, item in enumerate(items[:5], 1):
                print(f'=== 商品 {idx} ===')
                print(f'名前: {item.get("productName")}')
                print(f'価格: {item.get("price")}円')
                print(f'入札数: {item.get("bids")}')
                print()
        
        await browser.close()

asyncio.run(test_correct_url())
