import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def extract_auction_stats_fixed():
    search_query = 'ポケモンカード マナフィ 004/PPP'
    encoded_query = urllib.parse.quote(search_query, safe='')
    url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        
        text = await page.evaluate('() => document.body.innerText')
        
        print('統計情報抽出:')
        
        # パターンを調整
        min_match = re.search(r'最安\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最高\s*(\d+,?\d*)\s*円', text)
        count_match = re.search(r'(\d+)件', text)
        
        results = {}
        if min_match:
            results['min'] = int(min_match.group(1).replace(',', ''))
            print(f'✓ 最安: {results["min"]:,}円')
        if avg_match:
            results['avg'] = int(avg_match.group(1).replace(',', ''))
            print(f'✓ 平均: {results["avg"]:,}円')
        if max_match:
            results['max'] = int(max_match.group(1).replace(',', ''))
            print(f'✓ 最高: {results["max"]:,}円')
        if count_match:
            results['count'] = int(count_match.group(1))
            print(f'✓ 件数: {results["count"]}件')
        
        print(f'\n結果: {results}')
        
        await browser.close()

asyncio.run(extract_auction_stats_fixed())
