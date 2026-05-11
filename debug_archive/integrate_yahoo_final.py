with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. y_res = await search_yahoo(page, kw) の直後に y_history を追加
inserted = False
for i, line in enumerate(lines):
    if 'y_res = await search_yahoo(page, kw)' in line and not inserted:
        indent = len(line) - len(line.lstrip())
        lines.insert(i + 1, ' ' * indent + 'y_history = await fetch_yahoo_auction_history(kw, page)\n')
        print(f'✓ y_history 呼び出しを追加（Line {i+2}）')
        inserted = True
        break

# 2. RESEARCH_RESULTS.append の items を修正
for i, line in enumerate(lines):
    if \"'items': m_res + y_res + h_res,\" in line:
        old = \"'items': m_res + y_res + h_res,\"
        new = \"'items': m_res + y_res + h_res + ([{'price': y_history['avg'], 'source': 'yahoo_auction_history'}] if y_history else []),\"
        lines[i] = line.replace(old, new)
        print(f'✓ items定義を修正（Line {i+1}）')
        break

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('\n✓ ヤフオク統合完了')
