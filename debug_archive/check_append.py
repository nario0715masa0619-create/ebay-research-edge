with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# RESEARCH_RESULTS.append のセクションを確認
for i, line in enumerate(lines):
    if 'RESEARCH_RESULTS.append' in line:
        print(f'Found at line {i+1}')
        # その後の20行を表示
        for j in range(i, min(i+20, len(lines))):
            print(f'{j+1}: {lines[j].rstrip()}')
        break
