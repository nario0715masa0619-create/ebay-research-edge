with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# メイン処理ループ内で search_yahoo の呼び出しを探す
for i, line in enumerate(lines):
    if 'y_res = await search_yahoo(page, kw)' in line:
        print(f'Found search_yahoo at line {i+1}')
        # その直後に y_history の呼び出しを挿入
        indent = len(line) - len(line.lstrip())
        yahoo_history_call = ' ' * indent + 'y_history = await fetch_yahoo_auction_history(kw, page)\n'
        lines.insert(i + 1, yahoo_history_call)
        print(f'✓ ヤフオク呼び出しを追加（line {i+2}）')
        break

# さらに items の定義を探して y_history を追加
for i, line in enumerate(lines):
    if \"'items': m_res + y_res + h_res\" in line:
        print(f'Found items definition at line {i+1}')
        old_line = line
        new_line = line.replace(
            \"'items': m_res + y_res + h_res\",
            \"'items': m_res + y_res + h_res + ([{'price': y_history['avg'], 'source': 'yahoo_auction_history'}] if y_history else [])\"
        )
        lines[i] = new_line
        print(f'✓ items定義を更新（line {i+1}）')
        break

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('\n✓ ヤフオク呼び出しコードを統合しました')
