with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# y_history 呼び出しの周辺を確認
if 'y_history = await fetch_yahoo_auction_history' in content:
    pos = content.find('y_history = await fetch_yahoo_auction_history')
    print('y_history 呼び出し箇所:')
    print(content[pos-200:pos+300])
else:
    print('y_history 呼び出しなし')
