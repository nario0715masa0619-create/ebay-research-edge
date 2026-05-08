with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# y_history の値をprintする
for i, line in enumerate(lines):
    if 'y_history = await fetch_yahoo_auction_history' in line:
        # その直後にprint文を追加
        indent = len(line) - len(line.lstrip())
        lines.insert(i+1, ' ' * indent + 'print(f"DEBUG: y_history result = {y_history}")\n')
        print(f'✓ y_history デバッグprint追加（Line {i+2}）')
        break

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('✓ y_history の値をデバッグ出力します')
