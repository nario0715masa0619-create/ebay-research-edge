"""
Fixed Scrape.do and Diffbot API calls
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("Testing Scrape.do (FIXED)")
print("="*60)

scrapedo_key = os.getenv('SCRAPEDO_API_KEY')
print(f"API Key (first 10 chars): {scrapedo_key[:10] if scrapedo_key else 'NOT SET'}...")

if scrapedo_key:
    test_url = "https://jp.mercari.com/search?keyword=ポケモンカード"
    
    # 正しいパラメータ: token (apikey ではなく)
    params = {
        'token': scrapedo_key,  # ← 修正：apikey → token
        'url': test_url,
        'render': 'true'
    }
    
    try:
        resp = requests.get('https://api.scrape.do', params=params, timeout=30)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✓ SUCCESS! Response length: {len(resp.text)} bytes")
            print(f"First 300 chars:\n{resp.text[:300]}")
        else:
            print(f"ERROR: {resp.text[:300]}")
    except Exception as e:
        print(f"Request Failed: {e}")

print("\n" + "="*60)
print("Testing Diffbot (Checking Token)")
print("="*60)

diffbot_token = os.getenv('DIFFBOT_API_TOKEN')
print(f"Token (first 10 chars): {diffbot_token[:10] if diffbot_token else 'NOT SET'}...")

if diffbot_token:
    # Diffbot の簡単なテスト
    test_url = "https://example.com"
    params = {'token': diffbot_token, 'url': test_url}
    
    try:
        resp = requests.get('https://api.diffbot.com/v3/extract', params=params, timeout=30)
        print(f"Status Code: {resp.status_code}")
        data = resp.json()
        if 'error' in data:
            print(f"Diffbot Error: {data['error']}")
            print(f"→ Token may be invalid or expired")
        else:
            print(f"✓ Diffbot response OK")
    except Exception as e:
        print(f"Request Failed: {e}")
