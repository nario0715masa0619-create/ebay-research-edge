# test_yahoo_history.py を再度実行して、単体で動作することを確認
import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def test_yahoo_auction_history():
    search_query = 'ポケモンカード マナフィ 004/PPP'
    encoded_query = urllib.parse.quote(search_query, safe='')
    url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        
        text = await page.evaluate('() => document.body.innerText')
        
        min_match = re.search(r'最安\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最高\s*(\d+,?\d*)\s*円', text)
        
        result = None
        if min_match and avg_match and max_match:
            result = {
                'min': int(min_match.group(1).replace(',', '')),
                'avg': int(avg_match.group(1).replace(',', '')),
                'max': int(max_match.group(1).replace(',', ''))
            }
        
        print(f'✓ Yahoo auction history result: {result}')
        
        await browser.close()

asyncio.run(test_yahoo_auction_history())
