with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# fetch_yahoo_auction_history 関数が存在するか
if 'async def fetch_yahoo_auction_history' in content:
    print('✓ 関数定義: 存在')
    # 関数の開始位置
    pos = content.find('async def fetch_yahoo_auction_history')
    print(f'  位置: {pos}')
else:
    print('✗ 関数定義: 不在')

# y_history 呼び出しが存在するか
if 'y_history = await fetch_yahoo_auction_history' in content:
    print('✓ 呼び出し: 存在')
    pos = content.find('y_history = await fetch_yahoo_auction_history')
    print(f'  位置: {pos}')
else:
    print('✗ 呼び出し: 不在')

# get_exchange_rate 関数が存在するか（必要な関数）
if 'def get_exchange_rate' in content:
    print('✓ get_exchange_rate: 存在')
else:
    print('✗ get_exchange_rate: 不在')
