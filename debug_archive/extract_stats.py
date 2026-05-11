import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import re

async def extract_auction_stats():
    search_query = 'ポケモンカード マナフィ 004/PPP'
    encoded_query = urllib.parse.quote(search_query, safe='')
    url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        
        # ページ全体のテキストを取得
        text = await page.evaluate('() => document.body.innerText')
        
        print('ページテキスト（先頭1000文字）:')
        print(text[:1000])
        print('\n\n統計情報を探索中...')
        
        # 「最小」「平均」「最大」パターンを探す
        min_match = re.search(r'最小\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最大\s*(\d+,?\d*)\s*円', text)
        count_match = re.search(r'(\d+)件', text)
        
        if min_match:
            print(f'✓ 最小: {min_match.group(1)}円')
        if avg_match:
            print(f'✓ 平均: {avg_match.group(1)}円')
        if max_match:
            print(f'✓ 最大: {max_match.group(1)}円')
        if count_match:
            print(f'✓ 件数: {count_match.group(1)}件')
        
        await browser.close()

asyncio.run(extract_auction_stats())
