with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'y_res = await search_yahoo(page, kw)' in line:
        indent = len(line) - len(line.lstrip())
        lines.insert(i + 1, ' ' * indent + 'y_history = await fetch_yahoo_auction_history(kw, page)\n')
        print('y_history added at line', i+2)
        break

for i, line in enumerate(lines):
    target = "'items': m_res + y_res + h_res,"
    if target in line:
        new_line = line.replace(target, "'items': m_res + y_res + h_res + ([{'price': y_history['avg'], 'source': 'yahoo_auction_history'}] if y_history else []),")
        lines[i] = new_line
        print('items modified at line', i+1)
        break

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Done')
