with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# fetch_yahoo_auction_history 関数を修正
old_func = '''async def fetch_yahoo_auction_history(search_query, page):
    print(f"DEBUG: fetch_yahoo_auction_history called for {search_query}")
    try:
        encoded_query = urllib.parse.quote(search_query, safe='')'''

new_func = '''async def fetch_yahoo_auction_history(search_query, page):
    print(f"DEBUG: fetch_yahoo_auction_history called for {search_query}")
    try:
        if isinstance(search_query, list):
            search_query = ' '.join(search_query)
        encoded_query = urllib.parse.quote(search_query, safe='')'''

content = content.replace(old_func, new_func)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ search_query を文字列に変換する処理を追加しました')
