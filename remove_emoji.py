with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 絵文字をテキストに置き換え
replacements = {
    '🔍': '[SEARCH]',
    '❌': '[ERROR]',
    '✓': '[OK]',
    '🌌': '[GALAXY]',
    '⏳': '[WAIT]',
    '✅': '[DONE]'
}

for emoji, text in replacements.items():
    content = content.replace(emoji, text)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ 絵文字をテキストに置き換えました')
