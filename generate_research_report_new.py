import asyncio
import json
import re
import urllib.parse
from datetime import datetime
from playwright.async_api import async_playwright

async def fetch_yahoo_auction_history(search_query, page):
    """ヤフオク落札履歴から統計データを取得"""
    try:
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        
        items = await page.locator('li').all()
        prices = []
        
        for li in items:
            try:
                text = await li.evaluate('el => el.innerText')
                matches = re.findall(r'(\d+,?\d*)\s*円', text)
                if matches:
                    price = int(matches[0].replace(',', ''))
                    prices.append(price)
            except:
                pass
        
        if prices:
            return {
                'min': min(prices),
                'max': max(prices),
                'avg': int(sum(prices) / len(prices)),
                'median': sorted(prices)[len(prices)//2],
                'count': len(prices)
            }
    except Exception as e:
        print(f'ヤフオク落札履歴取得エラー: {e}')
    
    return None

async def main():
    search_query = 'ポケモンカード マナフィ 004/PPP'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        result = await fetch_yahoo_auction_history(search_query, page)
        
        if result:
            print('ヤフオク落札履歴統計:')
            print(f'  最小: {result["min"]:,}円')
            print(f'  最大: {result["max"]:,}円')
            print(f'  平均: {result["avg"]:,}円')
            print(f'  中央値: {result["median"]:,}円')
            print(f'  件数: {result["count"]}件')
        
        await context.close()
        await browser.close()

asyncio.run(main())
