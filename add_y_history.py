with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Line 198 の items に y_history を追加
old_line = "'items': m_res + y_res + h_res,"
new_line = "'items': m_res + y_res + h_res + ([{'price': y_history['avg'], 'source': 'yahoo_auction_history', 'history': y_history}] if y_history else []),"

content = content.replace(old_line, new_line)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ y_history added to items')
