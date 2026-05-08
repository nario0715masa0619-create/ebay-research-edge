with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 'items' を含む行を探す
for i, line in enumerate(lines):
    if 'items' in line.lower():
        print(f'Line {i+1}: {line.rstrip()}')
