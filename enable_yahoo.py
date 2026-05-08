with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# コメントアウトを解除
content = content.replace(
    '# y_history = await fetch_yahoo_auction_history(kw, browser)\n                y_history = None',
    'y_history = await fetch_yahoo_auction_history(kw, browser)'
)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('OK')
