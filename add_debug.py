with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# fetch_yahoo_auction_history 関数内の先頭にprint文を追加
for i, line in enumerate(lines):
    if 'async def fetch_yahoo_auction_history(search_query, page):' in line:
        # 次の行にprint文を挿入
        lines.insert(i+1, '    print(f"DEBUG: fetch_yahoo_auction_history called for {search_query}")\n')
        print(f'✓ デバッグprint追加（Line {i+2}）')
        break

# y_history = await の行にもprint文を追加
for i, line in enumerate(lines):
    if 'y_history = await fetch_yahoo_auction_history' in line:
        indent = len(line) - len(line.lstrip())
        lines.insert(i, ' ' * indent + 'print("DEBUG: About to call fetch_yahoo_auction_history")\n')
        print(f'✓ 呼び出し前のprint追加（Line {i+1}）')
        break

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✓ デバッグ出力を追加しました')
