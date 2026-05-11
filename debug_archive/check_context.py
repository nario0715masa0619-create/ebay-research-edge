with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 188 周辺を確認して、結果の処理を追加
for i in range(185, min(205, len(lines))):
    print(f'Line {i+1}: {lines[i].rstrip()}')
