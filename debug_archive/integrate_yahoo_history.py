with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# メイン処理内で y_res = await search_yahoo の直後に落札履歴を追加
if 'y_res = await search_yahoo(page, kw)' in content:
    # その直後に落札履歴取得を追加
    old_line = '                y_res = await search_yahoo(page, kw)'
    new_lines = '''                y_res = await search_yahoo(page, kw)
                y_history = await fetch_yahoo_auction_history(kw, page)'''
    
    content = content.replace(old_line, new_lines)
    
    # さらに結果を結合するコードを追加
    # y_res の後に y_history をマージ
    if 'results[kw] = {' in content:
        old_result = "results[kw] = {"
        new_result = '''if y_history:
                    results[kw]['yahoo_auction_history'] = y_history
                results[kw] = {'''
        content = content.replace(old_result, new_result)

with open('generate_research_report.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Yahoo auction history integrated')
