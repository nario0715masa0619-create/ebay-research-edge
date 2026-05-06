"""
Inspect actual HTML structure from Scrape.do responses
"""

import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

scrapedo_key = os.getenv('SCRAPEDO_API_KEY')

# Mercari HTML 検査
print("="*60)
print("Inspecting Mercari HTML Structure")
print("="*60)

mercari_url = "https://jp.mercari.com/search?keyword=ポケモンカード"
params = {'token': scrapedo_key, 'url': mercari_url, 'render': 'true'}
resp = requests.get('https://api.scrape.do', params=params, timeout=30)

if resp.status_code == 200:
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # すべての a タグを検査
    print("\n[Looking for product links...]")
    all_links = soup.find_all('a', limit=20)
    for i, link in enumerate(all_links):
        href = link.get('href', '')
        text = link.get_text(strip=True)[:50]
        classes = link.get('class', [])
        if 'mercari' in href or 'item' in href.lower():
            print(f"{i}: href={href[:60]}... | text={text} | class={classes}")
    
    # すべての div を class で検査
    print("\n[Looking for product containers...]")
    divs = soup.find_all('div', limit=30)
    for i, div in enumerate(divs):
        classes = div.get('class', [])
        if any(x in str(classes).lower() for x in ['product', 'item', 'card', 'merch']):
            print(f"{i}: class={classes}")
    
    # 価格要素を検査
    print("\n[Looking for price elements...]")
    price_spans = soup.find_all('span', limit=20)
    for i, span in enumerate(price_spans):
        text = span.get_text(strip=True)
        if '¥' in text or any(c.isdigit() for c in text):
            print(f"{i}: text={text} | class={span.get('class', [])}")

print("\n" + "="*60)
print("Inspecting Rakuma HTML Structure")
print("="*60)

rakuma_url = "https://fril.jp/search?query=ポケモンカード"
params = {'token': scrapedo_key, 'url': rakuma_url, 'render': 'true'}
resp = requests.get('https://api.scrape.do', params=params, timeout=30)

if resp.status_code == 200:
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    print("\n[Looking for product links...]")
    all_links = soup.find_all('a', limit=20)
    for i, link in enumerate(all_links):
        href = link.get('href', '')
        text = link.get_text(strip=True)[:50]
        classes = link.get('class', [])
        if 'fril' in href or 'item' in href.lower():
            print(f"{i}: href={href[:60]}... | text={text} | class={classes}")
    
    print("\n[Looking for product containers...]")
    divs = soup.find_all('div', limit=30)
    for i, div in enumerate(divs):
        classes = div.get('class', [])
        if any(x in str(classes).lower() for x in ['product', 'item', 'card']):
            print(f"{i}: class={classes}")
