import asyncio, urllib.parse
from playwright.async_api import async_playwright

async def debug_auction_logic():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # ユーザー指定のワード「ゲンガー」でテスト
        keyword = "ゲンガー"
        url = f"https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote(keyword, safe='')}?open=1"
        
        print(f"Testing URL: {url}\n")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
        items = await page.locator('a[href^="/item/"], a[href^="/product/"]').all()
        
        auction_count = 0
        fixed_count = 0
        
        for i, it in enumerate(items[:20]):
            # innerText だけでなく、クラス名や特定のバッジ要素も調査
            data = await it.evaluate("""el => {
                const badges = Array.from(el.querySelectorAll('span, p, div')).map(e => e.innerText);
                return {
                    text: el.innerText,
                    html: el.outerHTML.substring(0, 500),
                    hasAuctionBadge: badges.some(b => b.includes('オークション') || b.includes('入札')),
                    href: el.getAttribute('href')
                }
            }""")
            
            is_auction = "入札" in data['text'] or "オークション" in data['text'] or data['hasAuctionBadge']
            
            if is_auction:
                auction_count += 1
                print(f"🚩 ITEM [{i}] (AUCTION DETECTED)")
                print(f"   Text: {data['text'].replace('\\n', ' | ')}")
                # 特定の属性やバッジがあるか調査
                print(f"   HREF: {data['href']}")
            else:
                fixed_count += 1
                print(f"✅ ITEM [{i}] (FIXED PRICE)")
        
        print(f"\nFinal Count - Fixed: {fixed_count}, Auction: {auction_count}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_auction_logic())
