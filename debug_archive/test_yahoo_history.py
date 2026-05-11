import asyncio
from playwright.async_api import async_playwright
import urllib.parse

async def test_yahoo_auction_history():
    search_query = 'ポケモンカード マナフィ 004/PPP'
    encoded_query = urllib.parse.quote(search_query, safe='')
    url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
    
    print(f'テストURL: {url}')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print('ページ遷移中...')
            await page.goto(url, wait_until='load', timeout=30000)
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f'✓ ページロード成功')
            print(f'タイトル: {title}')
            
            # li要素をカウント
            items = await page.locator('li').all()
            print(f'li要素: {len(items)}件')
            
            # 最初の3件を確認
            print('\n最初の3件:')
            for idx, li in enumerate(items[:3], 1):
                text = await li.evaluate('el => el.innerText')
                print(f'{idx}. {text[:100]}...')
            
        except Exception as e:
            print(f'✗ エラー: {e}')
        
        await browser.close()

asyncio.run(test_yahoo_auction_history())
