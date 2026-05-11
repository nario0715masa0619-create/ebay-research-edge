with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

# get_exchange_rate 関数が存在するか確認
if 'def get_exchange_rate' not in content:
    # import セクションの直後に追加
    import_end = content.rfind('import')
    line_end = content.find('\n', import_end)
    
    exchange_func = '''

def get_exchange_rate():
    try:
        import requests
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            return response.json()['rates']['JPY']
    except:
        pass
    return 150  # デフォルト値

'''
    
    content = content[:line_end] + exchange_func + content[line_end:]
    
    with open('generate_research_report.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✓ get_exchange_rate 関数を追加しました')
else:
    print('✓ 関数は既に存在します')
