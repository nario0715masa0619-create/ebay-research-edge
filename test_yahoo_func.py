import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def fetch_yahoo_auction_history(search_query, browser):
    try:
        if isinstance(search_query, list):
            search_query = ' '.join(search_query)
        
        new_page = await browser.new_page()
        new_page.set_default_timeout(10000)
        
        print(f'Opening page for: {search_query}')
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        
        print(f'URL: {url}')
        await new_page.goto(url, wait_until='domcontentloaded')
        print('Page loaded')
        
        await new_page.wait_for_timeout(2000)
        
        text = await new_page.evaluate('() => document.body.innerText')
        print(f'Text length: {len(text)}')
        
        min_match = re.search(r'最安\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最高\s*(\d+,?\d*)\s*円', text)
        
        print(f'min_match: {min_match.group(1) if min_match else None}')
        print(f'avg_match: {avg_match.group(1) if avg_match else None}')
        print(f'max_match: {max_match.group(1) if max_match else None}')
        
        await new_page.close()
        
        if min_match and avg_match and max_match:
            result = {
                'min': int(min_match.group(1).replace(',', '')),
                'avg': int(avg_match.group(1).replace(',', '')),
                'max': int(max_match.group(1).replace(',', ''))
            }
            print(f'Result: {result}')
            return result
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    return None

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        result = await fetch_yahoo_auction_history('マナフィ 004/PPP', browser)
        print(f'\nFinal result: {result}')
        
        await browser.close()

asyncio.run(test())
