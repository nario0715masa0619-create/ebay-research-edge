with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    original = f.read()

# get_exchange_rate 関数が存在するか確認
if 'def get_exchange_rate' not in original:
    # インポートセクション直後に関数を追加
    import_section_end = original.find('\n\n')
    
    exchange_func = '''
def get_exchange_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            return response.json()['rates']['JPY']
    except:
        pass
    return 150

'''
    
    original = original[:import_section_end] + exchange_func + original[import_section_end:]

# fetch_yahoo_auction_history 関数を追加（まだない場合）
if 'async def fetch_yahoo_auction_history' not in original:
    # 最初のasync def の直前に挿入
    first_async = original.find('async def')
    
    yahoo_func = '''async def fetch_yahoo_auction_history(search_query, page):
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

'''
    
    original = original[:first_async] + yahoo_func + original[first_async:]

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(original)

print('✓ 関数を統合しました')
