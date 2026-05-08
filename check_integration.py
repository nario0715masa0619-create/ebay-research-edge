with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('=== ヤフオク関連コード確認 ===\n')

# 1. fetch_yahoo_auction_history 関数の存在確認
if 'async def fetch_yahoo_auction_history' in content:
    print('✓ fetch_yahoo_auction_history 関数: 存在')
else:
    print('✗ fetch_yahoo_auction_history 関数: 不在')

# 2. y_history 呼び出しの確認
if 'y_history = await fetch_yahoo_auction_history' in content:
    print('✓ ヤフオク呼び出し: 存在')
else:
    print('✗ ヤフオク呼び出し: 不在')

# 3. items に y_history が含まれているか
if 'y_history' in content:
    # y_history が使用されている箇所を探す
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'y_history' in line and 'items' in lines[max(0, i-5):i+5]:
            print('✓ items定義にy_history含まれる可能性あり')
            break
    else:
        print('✗ items定義にy_history統合されていない')
else:
    print('✗ y_history変数そのものが不在')
