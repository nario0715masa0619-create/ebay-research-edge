with open('generate_research_report.py', 'r', encoding='utf-8') as f:
    content = f.read()

checks = {
    'FEE_RATES DB': 'FEE_RATES' in content,
    'Yahoo!フリマ <a> タグ対応': 'a[href' in content and 'paypay' in content.lower(),
    '価格正規表現': r'\n' in content or 'strip()' in content,
    'AI 漢字優先化': '漢字' in content,
    'ユニークキーワード': 'set(' in content,
    'フォーカス保護': 'focus' in content or 'activeElement' in content,
}

print('=== V16.0 実装状況検証 ===\n')
for check, result in checks.items():
    status = '✅' if result else '❌'
    print(f'{status} {check}')
