import asyncio, urllib.parse
from playwright.async_api import async_playwright

async def debug_yahoo():
    async with async_playwright() as p:
        # 目視できるように headless=False
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # テスト対象の検索ワード
        keyword = "リザードン 110/080"
        # スラッシュも強制的にエンコードして、パスとして誤認されるのを防ぐ
        url = f"https://paypayfleamarket.yahoo.co.jp/search/{urllib.parse.quote(keyword, safe='')}?open=1"
        
        print(f"\n[1] 接続テスト: {url}")
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"[2] ページタイトル: {title}")
            
            if "ロボット" in title or "Robot" in title:
                print("❌ 警告: Bot判定（CAPTCHA）が表示されています！")
                return

            # リンクの抽出テスト
            links = await page.locator('a[href^="/item/"], a[href^="/product/"]').all()
            print(f"[3] 検出された商品リンク数: {len(links)}")
            
            if len(links) == 0:
                print("❌ 警告: 商品が1件も見つかりません。セレクタが間違っている可能性があります。")
                # ページ全体のHTMLを一部出力して構造を調査
                content = await page.content()
                print(f"ページHTML断片: {content[:500]}")
            else:
                print("[4] 最初の商品の構造解析:")
                first_item = links[0]
                details = await first_item.evaluate("""el => {
                    const img = el.querySelector('img');
                    return {
                        html: el.outerHTML.substring(0, 300),
                        innerText: el.innerText,
                        imgAlt: img ? img.alt : "NO_ALT",
                        href: el.getAttribute('href')
                    }
                }""")
                print(f"  - href: {details['href']}")
                print(f"  - innerText: {details['innerText'].replace('\\n', ' ')}")
                print(f"  - imgAlt (タイトル候補): {details['imgAlt']}")
                
        except Exception as e:
            print(f"❌ エラー発生: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_yahoo())
