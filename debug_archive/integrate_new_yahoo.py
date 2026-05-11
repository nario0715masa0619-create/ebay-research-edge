with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# fetch_yahoo_auction_history 関数を完全に置き換え
old_func_start = content.find('async def fetch_yahoo_auction_history')
old_func_end = content.find('\nasync def', old_func_start + 1)

if old_func_start > 0 and old_func_end > 0:
    new_func = '''async def fetch_yahoo_auction_history(search_query, browser):
    try:
        if isinstance(search_query, list):
            search_query = ' '.join(search_query)
        
        new_page = await browser.new_page()
        new_page.set_default_timeout(10000)
        
        encoded_query = urllib.parse.quote(search_query, safe='')
        url = f'https://auctions.yahoo.co.jp/closedsearch/closedsearch?p={encoded_query}&va={encoded_query}&b=1&n=50'
        
        await new_page.goto(url, wait_until='domcontentloaded')
        await new_page.wait_for_timeout(2000)
        
        text = await new_page.evaluate('() => document.body.innerText')
        
        min_match = re.search(r'最安\s*(\d+,?\d*)\s*円', text)
        avg_match = re.search(r'平均\s*(\d+,?\d*)\s*円', text)
        max_match = re.search(r'最高\s*(\d+,?\d*)\s*円', text)
        
        await new_page.close()
        
        if min_match and avg_match and max_match:
            return {
                'min': int(min_match.group(1).replace(',', '')),
                'avg': int(avg_match.group(1).replace(',', '')),
                'max': int(max_match.group(1).replace(',', ''))
            }
    except Exception as e:
        print(f'Yahoo error: {e}')
    return None

'''
    
    content = content[:old_func_start] + new_func + content[old_func_end:]
    
    # 呼び出し側も修正
    content = content.replace(
        'y_history = await fetch_yahoo_auction_history(kw, page)',
        'y_history = await fetch_yahoo_auction_history(kw, browser)'
    )
    
    with open('generate_research_report.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('OK')
