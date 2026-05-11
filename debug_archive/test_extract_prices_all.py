import asyncio
from playwright.async_api import async_playwright
import re
from datetime import datetime, timedelta

async def extract_prices_90days():
    # 直近90日間のパラメータを含めたURL
    url = 'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89+%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&va=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89+%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&b=1&n=50'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(5000)
        
        items = await page.locator('li').all()
        print(f'合計li要素: {len(items)}件\n')
        
        prices = []
        
        # 全li要素から価格を抽出
        for idx, li in enumerate(items):
            try:
                text = await li.evaluate('el => el.innerText')
                
                # 金額パターンマッチング（複数のマッチから最初のものを取得）
                matches = re.findall(r'(\d+,?\d*)\s*円', text)
                if matches:
                    # 最初にマッチした金額を価格として使用
                    price = int(matches[0].replace(',', ''))
                    prices.append(price)
                    
                    if idx < 3:  # 最初の3件を詳細表示
                        print(f'=== li #{idx+1} ===')
                        print(f'Text: {text[:150]}...')
                        print(f'✓ 抽出価格: {price}円\n')
            except:
                pass
        
        print(f'\n抽出成功: {len(prices)}件')
        if prices:
            print(f'最小: {min(prices):,}円')
            print(f'最大: {max(prices):,}円')
            print(f'平均: {int(sum(prices) / len(prices)):,}円')
            print(f'中央値: {sorted(prices)[len(prices)//2]:,}円')
        
        await browser.close()

asyncio.run(extract_prices_90days())
