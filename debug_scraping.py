"""
Debug script to verify Scrape.do and Diffbot responses
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Scrape.do テスト
print("="*60)
print("Testing Scrape.do")
print("="*60)

scrapedo_key = os.getenv('SCRAPEDO_API_KEY')
if not scrapedo_key:
    print("ERROR: SCRAPEDO_API_KEY not set in .env")
else:
    test_url = "https://jp.mercari.com/search?keyword=ポケモンカード"
    params = {
        'apikey': scrapedo_key,
        'url': test_url,
        'render': 'true'
    }
    
    print(f"Request URL: {test_url}")
    print(f"Scrape.do Params: {params}")
    
    try:
        resp = requests.get('https://api.scrape.do', params=params, timeout=30)
        print(f"Status Code: {resp.status_code}")
        print(f"Response Length: {len(resp.text)} bytes")
        print(f"First 500 chars:\n{resp.text[:500]}")
        
        if resp.status_code != 200:
            print(f"ERROR Response: {resp.text}")
    except Exception as e:
        print(f"Request Failed: {e}")

print("\n" + "="*60)
print("Testing Diffbot")
print("="*60)

diffbot_token = os.getenv('DIFFBOT_API_TOKEN')
if not diffbot_token:
    print("ERROR: DIFFBOT_API_TOKEN not set in .env")
else:
    test_url = "https://fril.jp/search?query=ポケモンカード"
    params = {'token': diffbot_token, 'url': test_url}
    
    print(f"Request URL: {test_url}")
    
    try:
        resp = requests.get('https://api.diffbot.com/v3/extract', params=params, timeout=30)
        print(f"Status Code: {resp.status_code}")
        print(f"Response:\n{resp.json()}")
    except Exception as e:
        print(f"Request Failed: {e}")
