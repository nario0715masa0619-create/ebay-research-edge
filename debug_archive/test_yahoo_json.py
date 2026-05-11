import asyncio
from playwright.async_api import async_playwright
import json

async def test_yahoo_auction_json():
    url = 'https://auctions.yahoo.co.jp/search/search?auccat=&tab_ex=commerce&ei=utf-8&aq=-1&oq=&sc_i=&fr=auc_top&p=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89%E3%80%80%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&x=0&y=0'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='networkidle', timeout=20000)
        await page.wait_for_timeout(3000)
        
        # JSONデータを抽出
        script = await page.query_selector('script[type="application/json"]')
        if script:
            json_text = await script.evaluate('el => el.textContent')
            json_data = json.loads(json_text)
            
            print(f'商品数: {len(json_data.get("items", []))}件\n')
            
            for idx, item in enumerate(json_data.get('items', [])[:3], 1):
                print(f'=== 商品 {idx} ===')
                print(f'ID: {item.get("productID")}')
                print(f'名前: {item.get("productName")}')
                print(f'価格: {item.get("price")}円')
                print(f'即決価格: {item.get("winPrice")}')
                print(f'入札数: {item.get("bids")}')
                print()
        
        await browser.close()

asyncio.run(test_yahoo_auction_json())
