with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Yahoo!フリマセクションの直後にヤフオク落札履歴セクションを追加
marker = "elif site == 'yahoofleamarket':"
if marker in content:
    # マーカーの位置を探す
    pos = content.find(marker)
    # そのセクションの終わり（次のelifまで）を探す
    next_elif = content.find('\n        elif', pos + 1)
    
    if next_elif > 0:
        # ヤフオク落札履歴セクションを挿入
        yahoo_history_code = '''
        elif site == 'yahoo_auction_history':
            results = []
            history = await fetch_yahoo_auction_history(search_query, page)
            if history:
                results.append({'price': history['avg'], 'source': 'yahoo_auction_history', 'history': history})
            return results if results else None
'''
        content = content[:next_elif] + yahoo_history_code + content[next_elif:]
        
        with open('generate_research_report.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print('✓ Yahoo auction history section added')
    else:
        print('✗ Could not find insertion point')
else:
    print('✗ Marker not found')
