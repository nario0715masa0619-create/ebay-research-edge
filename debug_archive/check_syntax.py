with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 29 周辺を確認
print('問題箇所（Line 25-35）:')
for i in range(24, min(35, len(lines))):
    print(f'{i+1}: {repr(lines[i])}')
