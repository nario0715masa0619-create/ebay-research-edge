with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('=== 統合状況確認 ===\n')

# 1. fetch_yahoo_auction_history 関数の存在
if 'async def fetch_yahoo_auction_history' in content:
    print('✓ fetch_yahoo_auction_history 関数: 存在')
else:
    print('✗ fetch_yahoo_auction_history 関数: 不在')

# 2. y_history 呼び出しの存在
if 'y_history = await fetch_yahoo_auction_history' in content:
    print('✓ y_history 呼び出し: 存在')
else:
    print('✗ y_history 呼び出し: 不在')

# 3. items に y_history が含まれているか
target = \"'items': m_res + y_res + h_res\"
if target in content:
    print('✓ items定義: 見つかり')
    pos = content.find(target)
    snippet = content[pos:pos+300]
    if 'y_history' in snippet:
        print('  → y_history を含む')
    else:
        print('  → y_history を含まない')
        print(f'  内容: {snippet}')
