# 新しい完全版 generate_research_report.py を作成
import asyncio
import json
import re
import urllib.parse
import requests
from playwright.async_api import async_playwright
from datetime import datetime

def get_exchange_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            return response.json()['rates']['JPY']
    except:
        pass
    return 150

async def fetch_yahoo_auction_history(search_query, page):
    try:
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        await page.goto(url, wait_until='load', timeout=30000)
        await page.wait_for_timeout(3000)
        text = await page.evaluate('() => document.body.innerText')
        
        min_match = re.search(r'最安\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最高\s*(\d+,?\d*)\s*円', text)
        count_match = re.search(r'(\d+)件', text)
        
        if min_match and avg_match and max_match:
            return {
                'min': int(min_match.group(1).replace(',', '')),
                'avg': int(avg_match.group(1).replace(',', '')),
                'max': int(max_match.group(1).replace(',', '')),
                'count': int(count_match.group(1)) if count_match else 0
            }
    except Exception as e:
        print(f'Yahoo auction error: {e}')
    return None

async def main():
    search_query = 'ポケモンカード マナフィ 004/PPP'
    rate = get_exchange_rate()
    print(f'為替レート: 1 USD = {rate}円')
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        result = await fetch_yahoo_auction_history(search_query, page)
        
        if result:
            print(f'\nヤフオク落札履歴:')
            print(f'  最小: {result["min"]:,}円')
            print(f'  平均: {result["avg"]:,}円')
            print(f'  最大: {result["max"]:,}円')
            print(f'  件数: {result["count"]}件')
        else:
            print('データ取得失敗')
        
        await context.close()
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
