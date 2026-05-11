import asyncio
from playwright.async_api import async_playwright

async def test_closed_search():
    url = 'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89+%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&va=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89+%E3%83%9E%E3%83%8A%E3%83%95%E3%82%A3+004%2FPPP&b=1&n=50'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(5000)
        
        print(f'ページタイトル: {await page.title()}')
        
        # セレクタテスト
        selectors = [
            'li[class*="product"]',
            'div[class*="price"]',
            'span[class*="price"]',
            'div[data-auction-id]',
            'li'
        ]
        
        print('\nセレクタテスト:')
        for selector in selectors:
            count = len(await page.locator(selector).all())
            print(f'{selector}: {count}件')
        
        # HTML保存
        html = await page.content()
        with open('yahoo_closed_search.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'\n✓ HTML保存: {len(html)}文字')
        
        await browser.close()

asyncio.run(test_closed_search())
