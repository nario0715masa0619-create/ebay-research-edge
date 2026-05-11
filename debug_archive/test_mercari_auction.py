import asyncio, urllib.parse
from playwright.async_api import async_playwright

async def debug_mercari_auction():
    async with async_playwright() as p:
        # 目視確認
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 実戦と同じ「型番付き」キーワードでテスト
        keyword = "ゲンガー 240/193"
        url = f"https://jp.mercari.com/search?keyword={urllib.parse.quote(keyword)}&status=on_sale"
        
        print(f"Testing Mercari: {url}\n")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
        # 商品カードを抽出
        items = await page.locator('a[href^="/item/m"]').all()
        
        print(f"Found {len(items)} items. Checking for auction markers...\n")
        
        for i, it in enumerate(items[:20]):
            data = await it.evaluate("""el => {
                return {
                    text: el.innerText,
                    html: el.outerHTML.substring(0, 500),
                    ariaLabel: el.ariaLabel || ""
                }
            }""")
            
            # メルカリのオークションは innerText や ariaLabel に「入札」や「オークション」が含まれるはず
            is_auction = any(x in data['text'] or x in data['ariaLabel'] for x in ["入札", "オークション", "現在の価格"])
            
            if is_auction:
                print(f"🚩 ITEM [{i}] (MERCARI AUCTION)")
                print(f"   Text: {data['text'].replace('\\n', ' | ')}")
                print(f"   AriaLabel: {data['ariaLabel']}")
            else:
                print(f"✅ ITEM [{i}] (MERCARI FIXED PRICE)")
                # print(f"   Text: {data['text'].replace('\\n', ' | ')}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_mercari_auction())
