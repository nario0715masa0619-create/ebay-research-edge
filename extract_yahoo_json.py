import json
import re

html = open('yahoo_full.html', 'r', encoding='utf-8').read()

# __NEXT_DATA__ の JSON を抽出
match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html)
if match:
    try:
        data = json.loads(match.group(1))
        print("✅ __NEXT_DATA__ を抽出しました")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])  # 最初の2000文字を表示
        
        # 商品リストを探す
        def find_items(obj, depth=0):
            if depth > 10: return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'item' in k.lower() or 'product' in k.lower():
                        print(f"\n🔍 Found key: {k}")
                        print(json.dumps(v, indent=2, ensure_ascii=False)[:500])
                    find_items(v, depth+1)
            elif isinstance(obj, list):
                for item in obj[:5]:
                    find_items(item, depth+1)
        
        find_items(data)
    except Exception as e:
        print(f"❌ JSON パース失敗: {e}")
else:
    print("❌ __NEXT_DATA__ が見つかりません")
    
    # 代替案：<a> タグを数える
    links = re.findall(r'<a[^>]*href="[^"]*"[^>]*>', html)
    print(f"\n代替案: <a> タグ数 = {len(links)}")
    if links:
        print("最初の5個:")
        for link in links[:5]:
            print(link[:100])
