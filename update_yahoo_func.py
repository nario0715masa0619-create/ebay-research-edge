with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# fetch_yahoo_auction_history 関数を新しい実装で置き換え
old_func_start = content.find('async def fetch_yahoo_auction_history')
old_func_end = content.find('\nasync def', old_func_start + 1)

if old_func_start > 0 and old_func_end > 0:
    new_func = '''async def fetch_yahoo_auction_history(search_query, page):
    try:
        import re
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
    
    content = content[:old_func_start] + new_func + content[old_func_end:]
    
    with open('generate_research_report.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✓ fetch_yahoo_auction_history 関数を更新しました')
else:
    print('✗ 関数が見つかりません')
