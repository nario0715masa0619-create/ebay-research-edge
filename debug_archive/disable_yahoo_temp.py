with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# y_history 呼び出しをコメントアウト
content = content.replace(
    'y_history = await fetch_yahoo_auction_history(kw, browser)',
    '# y_history = await fetch_yahoo_auction_history(kw, browser)\n                y_history = None'
)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ ヤフオク機能を無効化しました')
