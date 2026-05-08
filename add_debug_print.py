with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# fetch_yahoo_auction_history 関数の最初に print を追加
for i, line in enumerate(lines):
    if 'async def fetch_yahoo_auction_history' in line:
        # その次の行にprint文を挿入
        indent = '    '
        lines.insert(i+1, indent + 'print(f\"🔍 Yahoo auction history started for: {search_query}\")\n')
        print(f'✓ デバッグprint を追加（Line {i+2}）')
        break

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✓ デバッグ出力を追加しました')
