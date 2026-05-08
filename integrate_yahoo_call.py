import re

with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# search_yahoo の後に y_history 呼び出しを追加
content = content.replace(
    'y_res = await search_yahoo(page, kw)',
    'y_res = await search_yahoo(page, kw)' + '\n                y_history = await fetch_yahoo_auction_history(kw, page)'
)

# items 定義に y_history を追加
old_items = "'items': m_res + y_res + h_res,"
new_items = "'items': m_res + y_res + h_res + ([{'price': y_history['avg'], 'source': 'yahoo_auction_history'}] if y_history else []),"

content = content.replace(old_items, new_items)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ ヤフオク呼び出しコードを統合しました')
